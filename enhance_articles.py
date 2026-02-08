#!/usr/bin/env python3
import sys
import json
import re
import os
from datetime import datetime
from collections import Counter
from huggingface_hub import InferenceClient

def to_sentence_case(text):
    if not text: return ""
    # Remove AI artifacts like [INST] or <s>
    text = re.sub(r'\[/?INST\]|<s>|</s>', '', text).strip()
    text = text.replace('\n', ' ').strip()
    if not text: return ""
    text = text[0].upper() + text[1:]
    return text

def clean_text(text, title=""):
    """Aggressively removes author lists and journal metadata."""
    if not text: return ""
    if title and text.lower().startswith(title.lower()[:30]):
        text = text[len(title):].strip()

    patterns = [
        r'Publication date:.*?(?:\.|$)',
        r'Source:.*?(?:\.|$)',
        r'Author\(s\):.*', 
        r'Volume \d+.*?(?:\.|$)',
        r'https?://\S+',
        r'Journal of .*',
        r'Edited by .*'
    ]
    for p in patterns:
        text = re.sub(p, '', text, flags=re.IGNORECASE)
    
    return text.strip() if len(text.strip()) > 20 else "Research focusing on the themes of the title."

def main():
    print("=" * 60)
    print("Mouldwire Research Enhancement System (Llama-3 Chat)")
    print("=" * 60)

    hf_token = os.getenv('HF_TOKEN')
    # meta-llama/Meta-Llama-3-8B-Instruct is highly stable for Chat API tasks
    model_id = "meta-llama/Meta-Llama-3-8B-Instruct" 
    client = InferenceClient(model=model_id, token=hf_token)

    articles_data = []
    try:
        with open('mould_news.json', 'r', encoding='utf-8') as f:
            articles_data = json.load(f)
        print(f"✅ Loaded {len(articles_data)} articles.")
    except Exception as e:
        print(f"❌ Error loading mould_news.json: {e}")
        return

    enhanced_articles = []

    for i, article in enumerate(articles_data, 1):
        title = article.get('title', 'Untitled Research')
        raw_excerpt = article.get('excerpt', '')
        
        # Ensure 'excerpt' is defined before the AI call
        excerpt = clean_text(raw_excerpt, title)
        
        print(f"[{i}/{len(articles_data)}] Researching: {title[:50]}...")

        messages = [
            {
                "role": "system", 
                "content": "You are a social anthropologist. Summarize the research in 5 sentences. Focus on infrastructure, fungal sociality, and material toxicity. Do not use bullet points or mention authors."
            },
            {
                "role": "user", 
                "content": f"Title: {title}\nAbstract Snippet: {excerpt}"
            }
        ]

        try:
            response = client.chat_completion(
                messages=messages,
                max_tokens=400,
                temperature=0.7
            )
            ai_summary = response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"  ⚠ AI error: {e}. Using fallback.")
            ai_summary = f"Analysis of {title}. {excerpt[:200]}..."

        enhanced = {
            **article,
            'summary': to_sentence_case(ai_summary),
            'enhanced': True,
            'enhanced_at': datetime.utcnow().isoformat()
        }
        enhanced_articles.append(enhanced)

    with open('articles_enhanced.json', 'w', encoding='utf-8') as f:
        json.dump(enhanced_articles, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Success! Saved to articles_enhanced.json")

if __name__ == '__main__':
    main()
