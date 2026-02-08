#!/usr/bin/env python3
"""
Mouldwire AI Enhancement - Anthropological Research Edition
Updated for Hugging Face Chat Completion API (v0.3)
"""

import sys
import json
import re
import os
from datetime import datetime
from collections import Counter
from huggingface_hub import InferenceClient

def to_sentence_case(text):
    """Ensures the output is professional Sentence Case."""
    if not text: return ""
    text = text.strip()
    # Remove any leading [INST] or <s> tags if the AI accidentally includes them
    text = re.sub(r'\[/?INST\]|<s>|</s>', '', text).strip()
    text = text.capitalize()
    return re.sub(r'(?<=[.!?]\s)([a-z])', lambda x: x.group(1).upper(), text)

def clean_text(text, title=""):
    """Strips metadata and prepends title for context."""
    if not text: return ""
    if title and text.lower().startswith(title.lower()):
        text = text[len(title):].strip()

    patterns_to_remove = [
        r'Publication date:.*?(?:\.|$)',
        r'Published:.*?(?:\.|$)',
        r'Source:.*?(?:\.|$)',
        r'Author\(s\):.*?(?:\.|$)',
        r'https?://\S+', 
        r'Click here.*?(?:\.|$)',
        r'Journal of.*?,? vol\w*\.? \d+.*?(?:\.|$)',
    ]
    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    return text.strip()

def extract_keywords(text, top_k=10):
    """Frequency analysis for fungal and infrastructural terms."""
    import string
    text_clean = text.lower()
    for char in string.punctuation:
        text_clean = text_clean.replace(char, ' ')
    
    words = text_clean.split()
    stopwords = {'the', 'and', 'this', 'that', 'with', 'from', 'using', 'study', 'research'}
    filtered = [w for w in words if len(w) > 4 and w not in stopwords]
    
    research_terms = ['infrastructure', 'material', 'anthropocene', 'biopolitics', 'assemblage', 'toxicity', 'decay', 'fungal', 'mycelium']
    word_freq = Counter(filtered)
    
    keywords = [t for t in research_terms if t in word_freq]
    for word, count in word_freq.most_common(20):
        if word not in keywords and len(keywords) < top_k:
            keywords.append(word)
    return keywords[:top_k]

def main():
    print("=" * 60)
    print("Mouldwire Research Enhancement System (Chat Mode)")
    print("=" * 60)

    hf_token = os.getenv('HF_TOKEN')
    # CHANGED: Using v0.3 for better stability with Chat API
    model_id = "mistralai/Mistral-7B-Instruct-v0.3"
    client = InferenceClient(model=model_id, token=hf_token)

    try:
        with open('mould_news.json', 'r', encoding='utf-8') as f:
            articles_data = json.load(f)
    except FileNotFoundError:
        print("❌ Error: mould_news.json not found.")
        sys.exit(1)

    enhanced_articles = []

    for i, article in enumerate(articles_data, 1):
        title = article.get('title', '')
        excerpt = clean_text(article.get('excerpt', ''), title)
        
        print(f"[{i}/{len(articles_data)}] Researching: {title[:50]}...")

        # CHANGED: Format as Messages for the 'Conversational' task
        messages = [
            {
                "role": "system", 
                "content": "You are an expert anthropologist. Summarize research in 5-7 sentences. Focus on infrastructure, fungal sociality, and materiality. Never use bullet points. Ignore all journal citations or volume numbers."
            },
            {
                "role": "user", 
                "content": f"Article Title: {title}\nContent: {excerpt}"
            }
        ]

        try:
            # CHANGED: use client.chat_completion instead of text_generation
            response = client.chat_completion(
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            ai_summary = response.choices[0].message.content.strip()
            ai_summary = to_sentence_case(ai_summary)
            
        except Exception as e:
            print(f"  ⚠ AI error: {e}. Using fallback.")
            ai_summary = to_sentence_case(excerpt[:350] + "...")

        enhanced = {
            **article,
            'summary': ai_summary,
            'keywords': extract_keywords(title + " " + excerpt + " " + ai_summary),
            'enhanced': True,
            'enhanced_at': datetime.utcnow().isoformat()
        }
        enhanced_articles.append(enhanced)
        print(f"    ✓ Summary length: {len(ai_summary.split('.'))} sentences.")

    with open('articles_enhanced.json', 'w', encoding='utf-8') as f:
        json.dump(enhanced_articles, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Research Enhancement Complete. Saved to articles_enhanced.json")

if __name__ == '__main__':
    main()
