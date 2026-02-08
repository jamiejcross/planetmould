#!/usr/bin/env python3
"""
Mouldwire AI Enhancement - Using NEW Hugging Face Inference Providers
"""

import sys
import json
from datetime import datetime
from collections import Counter

# Use the NEW Hugging Face client
from huggingface_hub import InferenceClient

def extract_keywords(text, top_k=10):
    """Extract keywords using frequency analysis"""
    import string
    
    text_clean = text.lower()
    for char in string.punctuation:
        text_clean = text_clean.replace(char, ' ')
    
    words = text_clean.split()
    
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
                 'those', 'it', 'its', 'their', 'our', 'your', 'using', 'used'}
    
    filtered = [w for w in words if len(w) > 3 and w not in stopwords]
    word_freq = Counter(filtered)
    
    mould_terms = ['mould', 'mold', 'fungi', 'fungal', 'aspergillus', 'penicillium',
                   'mycotoxin', 'spore', 'indoor', 'moisture', 'ventilation',
                   'respiratory', 'asthma', 'allergen', 'species', 'exposure', 'infection']
    
    keywords = [term for term in mould_terms if term in word_freq]
    
    for word, count in word_freq.most_common(30):
        if word not in keywords and len(keywords) < top_k:
            keywords.append(word)
    
    return keywords[:top_k]

def categorize_article(title, content):
    """Categorize based on keywords"""
    text = (title + " " + content).lower()
    
    category_keywords = {
        "Scientific Research": ["study", "research", "university", "published", "journal", "analysis", "data", "findings", "species", "mechanism"],
        "Clinical": ["patient", "clinical", "hospital", "treatment", "diagnosis", "medical", "disease", "infection", "therapy", "healthcare"],
        "Health & Environment": ["health", "environment", "exposure", "risk", "public", "safety", "contamination", "pollution", "air quality"],
        "Housing & Indoor Air": ["indoor", "building", "home", "ventilation", "moisture", "wall", "construction", "hvac", "residential"],
        "Popular Media": ["news", "report", "according", "said", "announced", "revealed", "media", "press"]
    }
    
    scores = {}
    for category, keywords in category_keywords.items():
        score = sum(1 for kw in keywords if kw in text)
        scores[category] = min(score / 8, 1.0)
    
    if max(scores.values()) < 0.3:
        scores["Scientific Research"] = 0.7
    
    primary = max(scores.items(), key=lambda x: x[1])[0]
    return primary, scores

def main():
    import os
    
    print("=" * 60)
    print("Mouldwire AI Enhancement System")
    print("Using NEW Hugging Face Inference Providers")
    print("=" * 60)
    print()
    
    # Initialize HF Inference Client
    hf_token = os.getenv('HF_TOKEN')
    if hf_token:
        client = InferenceClient(token=hf_token)
        print("✓ Using Hugging Face token")
    else:
        client = InferenceClient()
        print("⚠ No HF_TOKEN - using free tier (limited)")
    print()
    
    # Load articles
    print("📥 Loading articles from mould_news.json...")
    try:
        with open('mould_news.json', 'r', encoding='utf-8') as f:
            articles_data = json.load(f)
    except FileNotFoundError:
        print("❌ Error: mould_news.json not found.")
        sys.exit(1)
    
    if not articles_data:
        print("❌ No articles to process.")
        sys.exit(1)
    
    print(f"   ✓ Loaded {len(articles_data)} articles")
    print()
    
    # Process articles
    enhanced_articles = []
    
    print("🔮 Enhancing articles...")
    print("-" * 60)
    
    for i, article in enumerate(articles_data, 1):
        title = article.get('title', '')
        content = article.get('excerpt', '')
        text = f"{title}. {content}"
        
        print(f"[{i}/{len(articles_data)}] {title[:50]}...")
        
        # Extract keywords
        keywords = extract_keywords(text)
        
        # Categorize  
        primary_category, category_scores = categorize_article(title, content)
        
        # Try AI summarization (with fallback)
        try:
            # Truncate to avoid token limits
            words = text.split()
            if len(words) > 300:
                text = " ".join(words[:300])
            
            # Use the NEW summarization method
            summary = client.summarization(
                text,
                model="facebook/bart-large-cnn"
            )
            
            if isinstance(summary, dict) and 'summary_text' in summary:
                ai_summary = summary['summary_text']
            elif isinstance(summary, str):
                ai_summary = summary
            else:
                # Fallback
                ai_summary = ' '.join(content.split('.')[:2]) + '.'
            
            print(f"   ✓ AI summary generated")
            
        except Exception as e:
            # Fallback to simple summary
            ai_summary = ' '.join(content.split('.')[:2]) + '.'
            print(f"   ⚠ AI failed, using fallback summary: {str(e)[:50]}")
        
        # Create enhanced article
        enhanced = {
            **article,
            'summary': ai_summary,
            'ai_summary': ai_summary,
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
    
    # Save
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
    print(f"Successfully enhanced: {len(enhanced_articles)}")
    print()
    
    # Category breakdown
    print("📊 Categories:")
    category_counts = {}
    for article in enhanced_articles:
        cat = article.get('primary_category', 'Unknown')
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {category}: {count}")
    
    print()
    print("🎉 Done!")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
