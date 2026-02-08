#!/usr/bin/env python3
"""
Mouldwire AI Enhancement - Anthropological Research Edition
Reengineered for deep infrastructural summaries and fungal sociality.
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
    # Capitalize first letter and fix sentences after punctuation
    text = text.strip().capitalize()
    return re.sub(r'(?<=[.!?]\s)([a-z])', lambda x: x.group(1).upper(), text)

def clean_text(text, title=""):
    """Strips metadata and prepends title for context."""
    if not text: return ""
    if title and text.lower().startswith(title.lower()):
        text = text[len(title):].strip()

    patterns_to_remove = [
        r'Publication date:.*?(?:\\.|$)',
        r'Published:.*?(?:\\.|$)',
        r'Source:.*?(?:\\.|$)',
        r'Author\(s\):.*?(?:\\.|$)',
        r'https?://\S+', 
        r'Click here.*?(?:\\.|$)',
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
    stopwords = {'the', 'and', 'this', 'that', 'with', 'from', 'using', 'study'}
    filtered = [w for w in words if len(w) > 4 and w not in stopwords]
    
    # Priority terms for your research
    research_terms = ['infrastructure', 'material', 'anthropocene', 'biopolitics', 'assemblage', 'toxicity', 'decay']
    word_freq = Counter(filtered)
    
    keywords = [t for t in research_terms if t in word_freq]
    for word, count in word_freq.most_common(20):
        if word not in keywords and len(keywords) < top_k:
            keywords.append(word)
    return keywords[:top_k]

def main():
    print("=" * 60)
    print("Mouldwire Research Enhancement System")
    print("=" * 60)

    hf_token = os.getenv('HF_TOKEN')
    # Using Mistral-7B for better reasoning/anthropological context
    client = InferenceClient(model="mistralai/Mistral-7B-Instruct-v0.2", token=hf_token)

    try:
        with open('mould_news.json', 'r', encoding='utf-8') as f:
            articles_data = json.load(f)
    except FileNotFoundError:
        print("❌ Error: mould_news.json not found.")
        sys.exit(1)

    enhanced_articles = []

    for i, article in enumerate(articles_data, 1):
        title = article.get('title', '')
        excerpt = clean_text(article.get('excerpt', ''))
        
        print(f"[{i}/{len(articles_data)}] Researching: {title[:50]}...")

        # THE NEW RESEARCH PROMPT
        prompt = f"""<s>[INST] Task: Summarize this article for a Social Anthropologist tracking infrastructural conditions and Filamentous fungi.
        
        Length: Exactly 5 to 7 sentences.
        
        Requirements:
        1. Summary: Explain the core event or discovery.
        2. Infrastructure: How does this intersect with the built environment, housing, or material networks?
        3. Fungal Sociality: How does it depict the life or resistance of fungi in relation to human life?
        4. Anthropological Hook: Mention implications for material conditions, labor, or toxicity.
        
        Format: Sentence Case. No bullet points.
        
        Article: {title}. {excerpt} [/INST]</s>"""

        try:
            # Generate longer response
            response = client.text_generation(
                prompt,
                max_new_tokens=500,
                temperature=0.7,
                repetition_penalty=1.2
            )
            
            ai_summary = to_sentence_case(response.strip())
            
        except Exception as e:
            print(f"  ⚠ AI error: {e}. Using fallback.")
            ai_summary = to_sentence_case(excerpt[:300] + "...")

        enhanced = {
            **article,
            'summary': ai_summary,
            'keywords': extract_keywords(title + " " + excerpt + " " + ai_summary),
            'enhanced': True,
            'enhanced_at': datetime.utcnow().isoformat()
        }
        enhanced_articles.append(enhanced)
        print(f"   ✓ Summary length: {len(ai_summary.split('.'))} sentences.")

    with open('articles_enhanced.json', 'w', encoding='utf-8') as f:
        json.dump(enhanced_articles, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Research Enhancement Complete. Saved to articles_enhanced.json")

if __name__ == '__main__':
    main()
