#!/usr/bin/env python3
"""
Enhance Mouldwire articles with AI-generated summaries, categories, and keywords.
This script reads articles from fetch_news.py output and enhances them.
"""

from content_enhancement_system import ContentEnhancer, Article
import json
import os
from datetime import datetime
from pathlib import Path

def load_articles(filepath='articles.json'):
    """Load articles from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {filepath} not found. Run fetch_news.py first.")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing {filepath}: {e}")
        return []

def load_existing_enhanced(filepath='articles_enhanced.json'):
    """Load previously enhanced articles to avoid reprocessing"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            existing = json.load(f)
            # Return as dict for faster lookup
            return {article['url']: article for article in existing}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_enhanced_articles(articles, filepath='articles_enhanced.json'):
    """Save enhanced articles to JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(articles)} articles to {filepath}")

def enhance_articles():
    """Main function to enhance articles"""
    
    print("=" * 60)
    print("Mouldwire AI Enhancement System")
    print("=" * 60)
    print()
    
    # Initialize AI enhancer
    print("🤖 Initializing AI enhancer...")
    enhancer = ContentEnhancer(ai_provider="huggingface")
    
    # Define categories to match Mouldwire's existing filter system
    categories = [
        "Scientific Research",
        "Popular Media", 
        "Health & Environment",
        "Housing & Indoor Air",
        "Clinical"
    ]
    
    # Check for Hugging Face token
    hf_token = os.getenv('HF_TOKEN')
    if hf_token:
        enhancer.set_api_key(hf_token)
        print("   ✓ Using Hugging Face token for higher rate limits")
    else:
        print("   ⚠ No HF_TOKEN found - using free tier (limited requests)")
        print("   💡 Add HF_TOKEN secret for better performance")
    print()
    
    # Load articles from fetch_news.py output
    print("📥 Loading articles...")
    new_articles = load_articles('articles.json')
    
    if not new_articles:
        print("❌ No articles to process. Exiting.")
        return
    
    print(f"   ✓ Loaded {len(new_articles)} articles from RSS feeds")
    print()
    
    # Load existing enhanced articles
    print("🔍 Checking for previously enhanced articles...")
    existing_enhanced = load_existing_enhanced('articles_enhanced.json')
    print(f"   ✓ Found {len(existing_enhanced)} previously enhanced articles")
    print()
    
    # Identify new articles that need enhancement
    new_urls = {article.get('url', '') for article in new_articles}
    existing_urls = set(existing_enhanced.keys())
    urls_to_enhance = new_urls - existing_urls
    
    print(f"📊 Article Status:")
    print(f"   • Total articles: {len(new_articles)}")
    print(f"   • Already enhanced: {len(existing_urls & new_urls)}")
    print(f"   • New to enhance: {len(urls_to_enhance)}")
    print()
    
    # Process articles
    enhanced_articles = []
    errors = []
    
    if urls_to_enhance:
        print("🔮 Enhancing new articles...")
        print("-" * 60)
        
        for i, article_data in enumerate(new_articles, 1):
            url = article_data.get('url', '')
            
            # Skip if already enhanced
            if url in existing_enhanced:
                enhanced_articles.append(existing_enhanced[url])
                continue
            
            # Skip if no URL
            if not url:
                print(f"⚠ Skipping article {i}: No URL found")
                continue
            
            try:
                # Create Article object
                article = Article(
                    title=article_data.get('title', 'Untitled'),
                    content=article_data.get('description', '') or article_data.get('summary', ''),
                    url=url,
                    source=article_data.get('source', {}).get('title', 'Unknown') if isinstance(article_data.get('source'), dict) else article_data.get('source', 'Unknown'),
                    published_date=article_data.get('published', None)
                )
                
                # Generate enhancements
                print(f"[{i}/{len(new_articles)}] Enhancing: {article.title[:50]}...")
                
                summary = enhancer.summarize(article)
                category_scores = enhancer.categorize(article, categories)
                keywords = enhancer.extract_keywords(article)
                
                # Get primary category
                primary_category = max(category_scores.items(), key=lambda x: x[1])[0] if category_scores else "Uncategorized"
                
                # Create enhanced article
                enhanced = {
                    **article_data,  # Keep all original fields
                    'summary': summary,
                    'ai_summary': summary,  # Alias for clarity
                    'primary_category': primary_category,
                    'categories': category_scores,
                    'keywords': keywords,
                    'enhanced': True,
                    'enhanced_at': datetime.utcnow().isoformat()
                }
                
                enhanced_articles.append(enhanced)
                print(f"   ✓ Category: {primary_category}")
                print(f"   ✓ Keywords: {', '.join(keywords[:3])}...")
                print()
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                errors.append({
                    'url': url,
                    'title': article_data.get('title', 'Unknown'),
                    'error': str(e)
                })
                # Keep original article without enhancement
                enhanced_articles.append({
                    **article_data,
                    'enhanced': False,
                    'error': str(e)
                })
                print()
    else:
        print("✨ All articles already enhanced - using cached versions")
        print()
        # Use all existing enhanced articles
        enhanced_articles = list(existing_enhanced.values())
    
    # Sort by date (newest first)
    enhanced_articles.sort(
        key=lambda x: x.get('published', '') or x.get('published_date', ''),
        reverse=True
    )
    
    # Save results
    print("💾 Saving enhanced articles...")
    save_enhanced_articles(enhanced_articles, 'articles_enhanced.json')
    print()
    
    # Summary
    print("=" * 60)
    print("✅ Enhancement Complete")
    print("=" * 60)
    print(f"Total articles: {len(enhanced_articles)}")
    print(f"Successfully enhanced: {sum(1 for a in enhanced_articles if a.get('enhanced', False))}")
    print(f"Failed to enhance: {len(errors)}")
    print()
    
    if errors:
        print("⚠ Errors encountered:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"   • {error['title'][:50]}: {error['error']}")
        if len(errors) > 5:
            print(f"   ... and {len(errors) - 5} more")
        print()
    
    # Category breakdown
    print("📊 Category Breakdown:")
    category_counts = {}
    for article in enhanced_articles:
        if article.get('enhanced'):
            cat = article.get('primary_category', 'Uncategorized')
            category_counts[cat] = category_counts.get(cat, 0) + 1
    
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {category}: {count}")
    print()
    
    print("🎉 Done! Articles ready for display on your website.")
    print("=" * 60)

if __name__ == '__main__':
    try:
        enhance_articles()
    except KeyboardInterrupt:
        print("\n\n⚠ Enhancement cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        raise
