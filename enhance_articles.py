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
    # Basic cleanup
    text = text.replace('\n', ' ').strip()
    if not text: return ""
    text = text[0].upper() + text[1:]
    return text

def clean_text(text, title=""):
    """Aggressively removes author lists and journal metadata."""
    if not text: return ""
    
    # Remove the title if it's repeated in the excerpt
    if title and text.lower().startswith(title.lower()[:30]):
        text = text[len(title):].strip()

    # List of patterns to wipe out (Authors, Dates, Volumes)
    patterns = [
        r'Publication date:.*?(?:\.|$)',
        r'Source:.*?(?:\.|$)',
        r'Author\(s\):.*', # Usually authors are the end of the metadata block
        r'Volume \d+.*?(?:\.|$)',
        r'https?://\S+',
        r'Journal of .*',
        r'Edited by .*'
    ]
    for p in patterns:
        text = re.sub(p, '', text, flags=re.IGNORECASE)
    
    # If we stripped everything, return a placeholder so the AI has context
    return text.strip() if len(text.strip()) > 20 else "Research focused on the themes of the title."

def main():
    print("=" * 60)
    print("Mouldwire Research Enhancement System (v0.3 Chat)")
    print("=" * 60)

    hf_token = os.getenv('HF_TOKEN')
    # Stable model for Chat API
    model_id = "meta-llama/Meta-Llama-3-8B-Instruct" 
    client = InferenceClient(model=model_id, token=hf_token)

    # 1. Initialize the variable FIRST to avoid NameError
    articles_data = [] 

    try:
        with open('mould_news.json', 'r', encoding='utf-8') as f:
            articles_data = json.load(f)
        print(f"✅ Loaded {len(articles_data)} articles.")
    except Exception as e:
        print(f"❌ Error loading mould_news.json: {e}")
        # Exit gracefully if there is no data to process
        return 

    enhanced_articles = []

    # 2. Now the loop will safely find 'articles_data'
    for i, article in enumerate(articles_data, 1):
        title = article.get('title', '')
        # ... rest of your loop logic

        messages = [
            {"role": "system", "content": "You are a social anthropologist. Summarize in 5 sentences focusing on infrastructure and toxicity."},
            {"role": "user", "content": f"Title: {title}\nSnippet: {excerpt}"}
        ]

        try:
            response = client.chat_completion(
                messages=messages,
                max_tokens=400,
                temperature=0.7
            )
            ai_summary = response.choices[0].message.content.strip()
        except Exception as e:
            # Check if it's a model error and suggest a fix in logs
            print(f"  ⚠ AI error: {e}")
            ai_summary = f"Summary currently unavailable for: {title}. Focus on fungal degradation and material safety."

        # ... (save code)
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
