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
    text = re.sub(r'\[/?INST\]|<s>|</s>', '', text).strip()
    text = text.replace('\n', ' ').strip()
    if not text: return ""
    text = text[0].upper() + text[1:]
    return text

def clean_text(text, title=""):
    """Aggressively removes author lists and journal metadata."""
    if not text: return ""
    
    # Remove title if repeated
    if title and text.lower().startswith(title.lower()[:30]):
        text = text[len(title):].strip()

    # Cleaning patterns
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

ACRONYM_MAP = {
    r'\bPCR\b': 'polymerase chain reaction',
    r'\bqPCR\b': 'quantitative polymerase chain reaction',
    r'\bRT-qPCR\b': 'reverse transcription quantitative polymerase chain reaction',
    r'\bMIC\b': 'minimum inhibitory concentration',
    r'\bMICs\b': 'minimum inhibitory concentrations',
    r'\bSNP\b': 'single nucleotide polymorphism',
    r'\bSNPs\b': 'single nucleotide polymorphisms',
    r'\bROS\b': 'reactive oxygen species',
    r'\bNO\b(?=\s(?:homeostasis|signaling|levels|stress|production|pathway))': 'nitric oxide',
    r'\bHPLC\b': 'high-performance liquid chromatography',
    r'\bLC-MS/MS\b': 'liquid chromatography-tandem mass spectrometry',
    r'\bLC-MS\b': 'liquid chromatography-mass spectrometry',
    r'\bUPLC-MS/MS\b': 'ultra-performance liquid chromatography-tandem mass spectrometry',
    r'\bFT-NIR\b': 'Fourier transform near-infrared spectroscopy',
    r'\bGC-MS\b': 'gas chromatography-mass spectrometry',
    r'\bCNN\b': 'convolutional neural network',
    r'\bCNNs\b': 'convolutional neural networks',
    r'\bAUROC\b': 'area under the receiver operating characteristic curve',
    r'\bMoA\b': 'mode of action',
    r'\bMoAs\b': 'modes of action',
    r'\bTAG\b': 'triacylglycerol',
    r'\bSSF\b': 'solid-state fermentation',
    r'\bSmF\b': 'submerged fermentation',
    r'\bTFA\b': 'total fatty acid',
    r'\bSEM\b': 'scanning electron microscopy',
    r'\bTEM\b': 'transmission electron microscopy',
    r'\bECD\b': 'electronic circular dichroism',
    r'\bVOCs?\b': 'volatile organic compounds',
    r'\bIFDs?\b': 'invasive fungal diseases',
    r'\bMALDI-TOF MS\b': 'matrix-assisted laser desorption/ionization time-of-flight mass spectrometry',
    r'\bITS\b': 'internal transcribed spacer',
    r'\bCGD\b': 'chronic granulomatous disease',
    r'\bETP\b': 'epipolythiodioxopiperazine',
}

def expand_acronyms(text):
    """Post-processing: expand any acronyms the model failed to write in full."""
    for pattern, expansion in ACRONYM_MAP.items():
        text = re.sub(pattern, expansion, text)
    return text

def formalize_voice(text):
    """Ensures a clinical, observational 'Patchy Anthropocene' tone."""
    disallowed = [
        "In this study,", "The researchers found that", "I find it",
        "It is interesting to note", "As an anthropologist,", "This research suggests",
        "The authors observe", "I observe", "In my view,",
        "This study highlights", "Notably,", "Interestingly,",
        "It is worth noting", "It should be noted", "Importantly,",
    ]

    # Initial cleanup
    text = re.sub(r'\[/?INST\]|<s>|</s>', '', text).strip()

    # Strip subjective framing
    for phrase in disallowed:
        reg = re.compile(re.escape(phrase), re.IGNORECASE)
        text = reg.sub('', text)

    # Expand any remaining acronyms
    text = expand_acronyms(text)

    return to_sentence_case(text.strip())

def main():
    print("=" * 60)
    print("Mouldwire Research Enhancement System (Llama-3 Chat)")
    print("=" * 60)

    hf_token = os.getenv('HF_TOKEN')
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

    # Load existing enhanced articles for rolling archive
    existing_enhanced = {}
    if os.path.exists('articles_enhanced.json'):
        try:
            with open('articles_enhanced.json', 'r', encoding='utf-8') as f:
                existing_enhanced_list = json.load(f)
                existing_enhanced = {a['url']: a for a in existing_enhanced_list}
            print(f"Loaded {len(existing_enhanced)} previously enhanced articles.")
        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: Could not load existing enhanced articles: {e}")
            existing_enhanced = {}

    # Only enhance articles not already in the archive
    new_articles = [a for a in articles_data if a['url'] not in existing_enhanced]
    print(f"Found {len(new_articles)} new articles to enhance ({len(articles_data) - len(new_articles)} already in archive).")

    enhanced_articles = []

    for i, article in enumerate(new_articles, 1):
        title = article.get('title', 'Untitled Research')
        raw_excerpt = article.get('excerpt', '')
        
        # 1. Clean the raw ScienceDirect text
        excerpt = clean_text(raw_excerpt, title)
        
        print(f"[{i}/{len(new_articles)}] Researching: {title[:50]}...")

        messages = [
            {
                "role": "system", 
                "content": (
                    "You are a detached field researcher documenting human-nonhuman interactions in the Anthropocene.\n\n"
                    "ANALYTICAL LENS (Patchy Anthropocene):\n"
                    "The Patchy Anthropocene lens brings 'located relations between humans and nonhumans into focus within "
                    "the broader ongoing material transformations and ruptures brought on by colonialism, imperialism, and capitalism' "
                    "(Deger, Zhou, Tsing & Keleman Saxena). The same species of mould flagged as planetary pathogens can also be "
                    "vehicles for accumulation; the same species that operate as signs of austerity or racialized exclusion can also "
                    "be potential industrial saviours. The capacity of moulds to metabolize diverse materials — from food, walls and "
                    "minerals to livers and lungs — and to rapidly adapt to external stresses makes them both a threat and a resource. "
                    "What emerges from such ecological assemblages in turbulent times are not just novel strains of mould but also "
                    "novel forms of social and economic power.\n\n"
                    "STRUCTURE: Write exactly 5 sentences.\n"
                    "- Sentences 1-4: Accurately summarise the source findings. Report only what the source text contains. "
                    "Use specific data, methods, organisms, and materials named in the source.\n"
                    "- Sentence 5: Frame the findings through the Patchy Anthropocene lens described above. "
                    "Draw out the tension, duality, or material entanglement implied by the research — "
                    "for example, how a pathogen is also a resource, how a remediation technology reveals deeper dependencies, "
                    "or how a clinical finding reflects broader patterns of exposure shaped by housing, labour, or capital. "
                    "This sentence should be observational and grounded — do not invent details not implied by the source.\n\n"
                    "TONE: Clinical, detached, observational. No enthusiasm, no hedging. "
                    "Write as if documenting a field site, not reviewing a paper.\n\n"
                    "STRICT CONSTRAINTS:\n"
                    "1. NO HALLUCINATION: Do not invent findings, organisms, locations, or materials not present in the source text. "
                    "If the source lacks detail, acknowledge the limitation rather than fabricating an analysis.\n"
                    "2. WEAK SIGNAL PROTOCOL: If the source text contains only metadata (author names, journal info, publication date) "
                    "with no substantive abstract or findings, write 2-3 sentences only. State clearly that source data is limited. "
                    "Do not attempt a full 5-sentence summary from a title alone.\n"
                    "3. NO ACRONYMS OR ABBREVIATIONS: Write every term in full, every time. "
                    "Do not introduce an acronym even once. For example: write 'polymerase chain reaction' not 'PCR', "
                    "'minimum inhibitory concentration' not 'MIC', 'reactive oxygen species' not 'ROS', "
                    "'single nucleotide polymorphism' not 'SNP'. This applies to ALL technical terms throughout the entire summary.\n"
                    "4. DIRECT REFERENCE: Always refer to the source directly as 'this paper', 'this study', or 'this report'. "
                    "Never use indefinite references like 'a paper', 'a study', or 'research has shown'.\n"
                    "5. MATERIAL SPECIFICITY: Do not use vague terms like 'infrastructure' or 'environment' in isolation. "
                    "Name the specific material, organism, or site described in the source (e.g. 'polypropylene mask fabric', 'postharvest tomato storage').\n"
                    "6. DO NOT use the first person ('I', 'me', 'my'). DO NOT describe your role. "
                    "DO NOT give a Title or Abstract heading for your summary.\n"
                    "7. DO NOT repeat the title of the article in your summary."
                )
            },
            {
                "role": "user", 
                "content": f"Analyze this research signal.\n\nTitle: {title}\nSource abstract: {excerpt}"
            }
        ]

        # Safety fallback
        excerpt_text = str(excerpt) if excerpt else "No abstract provided."

        try:
            response = client.chat_completion(
                messages=messages,
                max_tokens=400,
                temperature=0.5
            )
            raw_ai_summary = response.choices[0].message.content.strip()
            ai_summary = formalize_voice(raw_ai_summary)
            
        except Exception as e:
            print(f"  ⚠ AI error: {e}. Using fallback.")
            ai_summary = f"Observation of {title}. {excerpt_text[:200]}..."

        enhanced = {
            **article,
            'summary': ai_summary,
            'enhanced': True,
            'enhanced_at': datetime.utcnow().isoformat()
        }
        enhanced_articles.append(enhanced)

    # Merge newly enhanced articles into existing archive
    for article in enhanced_articles:
        existing_enhanced[article['url']] = article

    # Sort all enhanced articles by pubDate descending
    all_enhanced = sorted(existing_enhanced.values(), key=lambda x: x.get('pubDate', ''), reverse=True)

    with open('articles_enhanced.json', 'w', encoding='utf-8') as f:
        json.dump(all_enhanced, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Archive now contains {len(all_enhanced)} enhanced articles ({len(enhanced_articles)} newly enhanced).")

if __name__ == '__main__':
    main()
