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

def formalize_voice(text):
    """Post-processes the AI response to ensure a clinical, observational tone."""
    # List of 'subjective' or 'introductory' phrases to strip
    disallowed = [
        "In this study,", "The researchers found that", "I find it", 
        "It is interesting to note", "As an anthropologist,", "This research suggests",
        "The authors observe", "I observe", "In my view,"
    ]

    # Remove AI artifacts
    text = re.sub(r'\[/?INST\]|<s>|</s>', '', text).strip()
    
    for phrase in disallowed:
        # Case-insensitive replacement
        reg = re.compile(re.escape(phrase), re.IGNORECASE)
        text = reg.sub('', text)
    
    return to_sentence_case(text.strip())
    
    
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

        #THIS IS A CRITICAL SECTION WHERE YOU DEFINE THE AI'S VOICE. It explicitly forbids first-person language and focuses on the "Patchy Anthropocene" vocabulary.  
        messages = [
            {
                "role": "system", 
                "content": (
                    "You are a detached field researcher documenting the 'Patchy Anthropocene.' "
                    "Summarize research in 5 concise sentences. Focus on 'feral effects'—nonhuman responses "
                    "to human infrastructure that exceed human design. Analyze how multispecies assemblages "
                    "(fungi, bacteria, toxins) interact with industrial materials or landscapes. "
                    "Maintain a clinical, observational tone. DO NOT use the first person ('I', 'me', 'my'). "
                    "DO NOT describe your role as an anthropologist or use phrases like 'it is intriguing to observe.' "
                    "Treat the research as a site of environmental rupture or unexpected coordination."
                )
            },
            {
                "role": "user", 
                "content": f"Title: {title}\nAbstract: {excerpt}"
            }
        ]

        try:
            response = client.chat_completion(
                messages=messages,
                max_tokens=400,
                temperature=0.7
            )
            ai_summary = response.choices[0].message.content.strip()

        # CALL THE NEW FORMALIZER HERE
            ai_summary = formalize_voice(raw_ai_summary)
            
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
