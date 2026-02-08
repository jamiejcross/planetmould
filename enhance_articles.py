#!/usr/bin/env python3
"""
Mouldwire AI Enhancement - FIXED VERSION
Addresses: short summaries, categorization, and metadata cleanup
"""

import sys
import json
import re
from datetime import datetime
from collections import Counter

from huggingface_hub import InferenceClient

def clean_text(text):
    """Remove metadata patterns from text"""
    if not text:
        return ""
    
    # Remove publication date patterns
    text = re.sub(r'Publication date:.*?\.', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Published:.*?\.', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}', '', text)
    
    # Remove journal names (common pattern: Journal of X, Volume Y)
    text = re.sub(r',\s*Volume\s+\d+.*?\.', '.', text)
    text = re.sub(r'Journal of [^,\.]+,', '', text)
    
    # Remove author lists (names with commas)
    # Pattern: ", Name Name, Name Name." at end
    text = re.sub(r',\s+[A-Z][a-z]+\s+[A-Z][a-z]+(?:,\s+[A-Z][a-z]+\s+[A-Z][a-z]+)*\.?\s*$', '.', text)
    
    # Clean up extra spaces and periods
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\.+', '.', text)
    text = text.strip()
    
    return text

def extract_keywords(text, top_k=10):
    """Extract keywords using frequency analysis"""
    import string
    
    text_clean = clean_text(text).lower()
    for char in string.punctuation:
        text_clean = text_clean.replace(char, ' ')
    
    words = text_clean.split()
    
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
                 'those', 'it', 'its', 'their', 'our', 'your', 'using', 'used', 'also'}
    
    filtered = [w for w in words if len(w) > 3 and w not in stopwords]
    word_freq = Counter(filtered)
    
    mould_terms = ['mould', 'mold', 'fungi', 'fungal', 'aspergillus', 'penicillium',
                   'mycotoxin', 'mycotoxins', 'spore', 'spores', 'indoor', 'moisture', 
                   'ventilation', 'respiratory', 'asthma', 'allergen', 'species', 
                   'exposure', 'infection', 'fusarium', 'alternaria', 'cladosporium']
    
    keywords = [term for term in mould_terms if term in word_freq]
    
    for word, count in word_freq.most_common(40):
        if word not in keywords and len(keywords) < top_k:
            keywords.append(word)
    
    return keywords[:top_k]

def categorize_article(title, content):
    """Categorize based on enhanced keyword matching"""
    text = (title + " " + clean_text(content)).lower()
    
    category_keywords = {
        "Clinical": {
            "strong": ["patient", "clinical", "hospital", "treatment", "diagnosis", "therapy", "medical", "healthcare", "disease", "infection", "antifungal", "mortality"],
            "weak": ["human", "case", "immune", "blood"]
        },
        "Housing & Indoor Air": {
            "strong": ["indoor", "building", "home", "ventilation", "moisture", "wall", "hvac", "residential", "dwelling", "apartment", "house"],
            "weak": ["air quality", "environment", "contamination"]
        },
        "Health & Environment": {
            "strong": ["health", "public health", "exposure", "risk", "safety", "pollution", "environmental", "hazard", "toxic"],
            "weak": ["contamination", "air", "water"]
        },
        "Popular Media": {
            "strong": ["news", "report", "announced", "revealed", "press release", "breaking", "discovered"],
            "weak": ["according", "said", "media"]
        },
        "Scientific Research": {
            "strong": ["study", "research", "analysis", "findings", "investigated", "observed", "mechanism", "pathway", "gene"],
            "weak": ["data", "results", "published", "university", "journal"]
        }
    }
    
    scores = {}
    for category, keyword_sets in category_keywords.items():
        strong_score = sum(3 for kw in keyword_sets["strong"] if kw in text)
        weak_score = sum(1 for kw in keyword_sets["weak"] if kw in text)
        total = strong_score + weak_score
        scores[category] = min(total / 15, 1.0)
    
    # If nothing scores well, default based on content patterns
    if max(scores.values()) < 0.2:
        if "patient" in text or "clinical" in text:
            scores["Clinical"] = 0.7
        elif "indoor" in text or "building" in text:
            scores["Housing & Indoor Air"] = 0.7
        else:
            scores["Scientific Research"] = 0.6
    
    primary = max(scores.items(), key=lambda x: x[1])[0]
    return primary, scores

def main():
    import os
    
    print("=" * 60)
    print("Mouldwire AI Enhancement System - FIXED")
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
        
        # CLEAN the content first
        cleaned_content = clean_text(content)
        
        print(f"[{i}/{len(articles_data)}] {title[:50]}...")
        
        # Extract keywords from cleaned text
        keywords = extract_keywords(title + " " + cleaned_content)
        
        # Categorize with cleaned text
        primary_category, category_scores = categorize_article(title, cleaned_content)
        
        # Generate AI summary
        try:
            # Prepare text for summarization (title + CLEANED content)
            text_for_summary = f"{title}. {cleaned_content}"
            
            # Truncate to avoid token limits
            words = text_for_summary.split()
            if len(words) > 400:
                text_for_summary = " ".join(words[:400])
            
            # Use HF summarization
            summary_result = client.summarization(
                text_for_summary,
                model="facebook/bart-large-cnn"
            )
            
            # Extract summary text
            if isinstance(summary_result, dict) and 'summary_text' in summary_result:
                ai_summary = summary_result['summary_text']
            elif isinstance(summary_result, str):
                ai_summary = summary_result
            else:
                ai_summary = None
            
            # Clean the AI summary too
            if ai_summary:
                ai_summary = clean_text(ai_summary)
                print(f"   ✓ AI summary: {ai_summary[:60]}...")
            else:
                # Fallback: first 2-3 sentences of cleaned content
                sentences = cleaned_content.split('.')[:3]
                ai_summary = '. '.join(s.strip() for s in sentences if s.strip()) + '.'
                print(f"   ⚠ Using fallback summary")
            
        except Exception as e:
            # Fallback summary
            sentences = cleaned_content.split('.')[:3]
            ai_summary = '. '.join(s.strip() for s in sentences if s.strip()) + '.'
            print(f"   ⚠ AI failed: {str(e)[:40]}, using fallback")
        
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
        print(f"   ✓ Category: {primary_category} (score: {category_scores[primary_category]:.2f})")
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
