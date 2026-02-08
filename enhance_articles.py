#!/usr/bin/env python3
import sys
import traceback

def main():
    try:
        from content_enhancement_system import ContentEnhancer, Article
        import json
        import os
        from datetime import datetime
        
        print("✓ All imports successful")
        print(f"✓ Python version: {sys.version}")
        
        print("=" * 60)
        print("Mouldwire AI Enhancement System")
        print("=" * 60)
        print()
        
        # Initialize AI enhancer
        print("🤖 Initializing AI enhancer...")
        enhancer = ContentEnhancer(ai_provider="huggingface")
        
        # Define categories
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
            print("   ⚠ No HF_TOKEN found - using free tier")
        print()
        
        # Load articles from mould_news.json (YOUR FILE!)
        print("📥 Loading articles from mould_news.json...")
        try:
            with open('mould_news.json', 'r', encoding='utf-8') as f:
                articles_data = json.load(f)
        except FileNotFoundError:
            print("❌ Error: mould_news.json not found.")
            sys.exit(1)
        
        if not articles_data:
            print("❌ No articles to process. Exiting.")
            sys.exit(1)
        
        print(f"   ✓ Loaded {len(articles_data)} articles")
        print()
        
        # Process articles
        enhanced_articles = []
        errors = []
        
        print("🔮 Enhancing articles...")
        print("-" * 60)
        
        for i, article_data in enumerate(articles_data, 1):
            try:
                # Create Article object
                article = Article(
                    title=article_data.get('title', 'Untitled'),
                    content=article_data.get('excerpt', ''),
                    url=article_data.get('url', ''),
                    source=article_data.get('source', 'Unknown'),
                    published_date=article_data.get('pubDate', None)
                )
                
                print(f"[{i}/{len(articles_data)}] Enhancing: {article.title[:50]}...")
                
                summary = enhancer.summarize(article)
                category_scores = enhancer.categorize(article, categories)
                keywords = enhancer.extract_keywords(article)
                
                primary_category = max(category_scores.items(), key=lambda x: x[1])[0] if category_scores else "Scientific Research"
                
                enhanced = {
                    **article_data,
                    'summary': summary,
                    'ai_summary': summary,
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
                errors.append({'title': article_data.get('title', 'Unknown'), 'error': str(e)})
                enhanced_articles.append({**article_data, 'enhanced': False, 'error': str(e)})
                print()
        
        # Save results
        print("💾 Saving enhanced articles...")
        with open('articles_enhanced.json', 'w', encoding='utf-8') as f:
            json.dump(enhanced_articles, f, indent=2, ensure_ascii=False)
        print(f"   ✓ Saved to articles_enhanced.json")
        print()
        
        # Summary
        print("=" * 60)
        print("✅ Enhancement Complete")
        print("=" * 60)
        print(f"Total articles: {len(enhanced_articles)}")
        print(f"Successfully enhanced: {sum(1 for a in enhanced_articles if a.get('enhanced', False))}")
        print(f"Failed: {len(errors)}")
        print()
        
        if errors:
            print("⚠ Errors:")
            for error in errors[:5]:
                print(f"   • {error['title'][:50]}: {error['error']}")
        
        # Category breakdown
        print("📊 Categories:")
        category_counts = {}
        for article in enhanced_articles:
            if article.get('enhanced'):
                cat = article.get('primary_category', 'Uncategorized')
                category_counts[cat] = category_counts.get(cat, 0) + 1
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {category}: {count}")
        
        print()
        print("🎉 Done!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
