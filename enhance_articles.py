#!/usr/bin/env python3
import sys
import json
import re
import os
from datetime import datetime
from collections import Counter
import anthropic

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
    r'\bSDH\b': 'succinate dehydrogenase',
    r'\bDHODH\b': 'dihydroorotate dehydrogenase',
    r'\bBGCs?\b': 'biosynthetic gene clusters',
    r'\bLPs?\b(?=\s)': 'lipopeptides',
    r'\bGSNOR\b': 'S-nitrosoglutathione reductase',
    r'\bNrf2\b': 'nuclear factor erythroid 2-related factor 2',
    r'\bNLRP3\b': 'NOD-like receptor protein 3',
}

def strip_parenthetical_acronyms(text):
    """Remove parenthetical acronyms like 'scanning electron microscopy (SEM)' → keep the full term.
    Also handles reverse: 'SEM (scanning electron microscopy)' → keep the full term.
    Also handles identical: 'SEM (SEM)' → keep one copy.
    Prevents stutter after expand_acronyms() runs."""
    # Pattern 0: "ACRONYM (ACRONYM)" — identical duplication, keep one
    text = re.sub(r'\b([A-Z][A-Z0-9/-]{1,12})\s*\(\1\)', r'\1', text)
    # Pattern 1: "full term (ACRONYM)" — strip the parenthetical
    text = re.sub(r'(\b[A-Za-z][\w\s/-]{4,}?)\s*\(([A-Z][A-Z0-9/-]{1,12})\)', r'\1', text)
    # Pattern 2: "ACRONYM (full term)" — keep the full term in parens, drop the acronym
    text = re.sub(r'\b([A-Z][A-Z0-9/-]{1,12})\s*\(([A-Za-z][\w\s/-]{4,}?)\)', r'\2', text)
    return text

JARGON_MAP = {
    # Cell biology
    r'\bapoptosis\b': 'programmed cell death',
    r'\bapoptotic\b': 'cell-death',
    r'\bnecros(?:is|ed)\b': 'tissue death',
    r'\bnecrotic\b': 'dead-tissue',
    r'\blipid peroxidation\b': 'cell membrane damage caused by oxidation',
    r'\bcytotoxicity\b': 'toxicity to cells',
    r'\bcytotoxic\b': 'cell-damaging',
    r'\bgenotoxic(?:ity)?\b': 'DNA-damaging',
    r'\bhepatotoxic(?:ity)?\b': 'liver-damaging',
    r'\bnephrotoxic(?:ity)?\b': 'kidney-damaging',
    r'\bpathogenesis\b': 'disease development',
    r'\bvirulence factors?\b': 'infection-enabling traits',
    r'\bvirulence\b': 'disease-causing ability',
    r'\bbiofilm formation\b': 'surface-colonising microbial communities',
    r'\bbiofilms?\b': 'surface-bound microbial communities',
    # Genetics / molecular
    r'\bphylogenetic(?:ally)?\b': 'evolutionary-relationship',
    r'\bgenotyping\b': 'genetic profiling',
    r'\bgenotype\b': 'genetic profile',
    r'\bgenotypes\b': 'genetic profiles',
    r'\bphenotypic(?:ally)?\b': 'observable-trait',
    r'\bphenotypes\b': 'observable traits',
    r'\bphenotype\b': 'observable trait profile',
    r'\btranscriptomic(?:s)?\b': 'gene-expression analysis',
    r'\bproteomic(?:s)?\b': 'protein-level analysis',
    r'\bmetabolomic(?:s)?\b': 'metabolite-level analysis',
    r'\bupregulation of\b': 'increased activity of',
    r'\bwere upregulated\b': 'showed increased activity',
    r'\bupregulated\b': 'elevated',
    r'\bupregulating\b': 'increasing the activity of',
    r'\bdownregulation of\b': 'decreased activity of',
    r'\bwere downregulated\b': 'showed decreased activity',
    r'\bdownregulated\b': 'reduced',
    r'\bdownregulating\b': 'decreasing the activity of',
    # Clinical / pharmacological
    r'\b[Ii]n vitro experiments?\b': 'laboratory experiments',
    r'\b[Ii]n vitro\b': 'laboratory-based',
    r'\b[Ii]n vivo experiments?\b': 'live-organism experiments',
    r'\b[Ii]n vivo\b': 'in living organisms',
    r'\bprophylaxis\b': 'preventive treatment',
    r'\bprophylactic\b': 'preventive',
    r'\betiolog(?:y|ical)\b': 'cause',
    r'\bcomorbid(?:ity|ities)\b': 'co-occurring conditions',
    r'\bimmunocompromised\b': 'immune-weakened',
    r'\bimmunosuppressed\b': 'immune-suppressed',
    # Chemistry / methods
    r'\bsynergistic(?:ally)?\b': 'combined-effect',
    r'\bantagonistic(?:ally)?\b': 'counteracting',
    r'\blyophili[sz](?:ed|ation)\b': 'freeze-dried',
    r'\bsubstrate\b': 'growth medium',
    r'\bsubstrates\b': 'growth media',
    # Ecology
    r'\bbioremediation\b': 'biological cleanup',
    r'\brhizosphere\b': 'root zone',
    r'\bendophyt(?:e|ic|es)\b': 'plant-internal microbe',
    r'\bmycorrhiza[el]?\b': 'root-associated fungal',
    # Phrasing
    r'\bsignificantly inhibited\b': 'substantially reduced',
    r'\bsignificantly enhanced\b': 'substantially increased',
    r'\bsignificantly reduced\b': 'substantially reduced',
    r'\blesion expansion\b': 'the spread of damage',
    r'\bhost-pathogen interactions?\b': 'infection dynamics',
    r'\bdose-dependent\b': 'dose-related',
}

def simplify_jargon(text):
    """Post-processing: replace specialist jargon with plain language equivalents."""
    for pattern, replacement in JARGON_MAP.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

def expand_acronyms(text):
    """Post-processing: expand any acronyms the model failed to write in full."""
    # First strip parenthetical acronym patterns to prevent stutter
    text = strip_parenthetical_acronyms(text)
    # Then expand any remaining bare acronyms
    for pattern, expansion in ACRONYM_MAP.items():
        text = re.sub(pattern, expansion, text)
    # Final safety: catch any "full term (full term)" stutter that slipped through
    text = re.sub(r'(\b[\w\s/-]{5,}?)\s*\(\1\)', r'\1', text)
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

    # Simplify specialist jargon for general readability
    text = simplify_jargon(text)

    return to_sentence_case(text.strip())

# --- RAG Integration (optional) ---
def get_rag_context(article):
    """Retrieve related articles from ChromaDB for cross-referencing.
    Returns formatted context string, or empty string if RAG unavailable."""
    try:
        from rag_retrieve import find_related, format_context_for_prompt
        results = find_related(article, n_results=3)
        if results:
            context = format_context_for_prompt(results, max_chars=800)
            return context
    except ImportError:
        pass  # RAG modules not installed
    except Exception as e:
        print(f"  RAG context unavailable: {e}")
    return ""


def main():
    print("=" * 60)
    print("Mouldwire Research Enhancement System (Claude Haiku 4.5)")
    print("=" * 60)

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set. Exiting.")
        return
    model_id = "claude-haiku-4-5-20251001"
    client = anthropic.Anthropic(api_key=api_key)

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

    # Identify articles needing enhancement:
    # 1. New articles not yet in the archive
    # 2. Previously enhanced articles whose summary was a WEAK SIGNAL
    #    AND whose excerpt has since been enriched with a real abstract
    def needs_enhancement(article):
        url = article.get('url', '')
        if url not in existing_enhanced:
            return True  # New article
        prev = existing_enhanced[url]
        prev_summary = prev.get('summary', '')
        was_weak = ('WEAK SIGNAL' in prev_summary
                    or 'hot off the press' in prev_summary)
        now_has_abstract = not _is_thin(article.get('excerpt', ''))
        if was_weak and now_has_abstract:
            return True  # Was weak, now has real abstract — re-enhance
        return False

    def _is_thin(excerpt):
        """Quick check if excerpt is metadata-only."""
        if not excerpt or len(excerpt) < 100:
            return True
        if re.match(r'^Publication date:', excerpt, re.IGNORECASE):
            return True
        if excerpt.strip().endswith('...') and len(excerpt) < 150:
            return True
        return False

    new_articles = [a for a in articles_data if needs_enhancement(a)]
    retry_count = sum(1 for a in new_articles if a.get('url', '') in existing_enhanced)
    print(f"Found {len(new_articles)} articles to enhance ({len(new_articles) - retry_count} new, {retry_count} retrying after abstract enrichment).")

    enhanced_articles = []

    for i, article in enumerate(new_articles, 1):
        title = article.get('title', 'Untitled Research')
        raw_excerpt = article.get('excerpt', '')
        
        # 1. Clean the raw ScienceDirect text
        excerpt = clean_text(raw_excerpt, title)
        
        print(f"[{i}/{len(new_articles)}] Researching: {title[:50]}...")

        # Retrieve related articles from RAG for cross-referencing context
        rag_context = get_rag_context(article)
        if rag_context:
            print(f"  RAG: retrieved related context ({len(rag_context)} chars)")

        system_prompt = (
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
            "STRUCTURE: Write 5 to 7 sentences.\n"
            "- The first sentences accurately summarise the source findings. Report only what the source text contains. "
            "Use specific data, methods, organisms, and materials named in the source.\n"
            "- The final 1-2 sentences frame the findings through the Patchy Anthropocene lens described above. "
            "Draw out the tension, duality, or material entanglement implied by the research — "
            "for example, how a pathogen is also a resource, how a remediation technology reveals deeper dependencies, "
            "or how a clinical finding reflects broader patterns of exposure shaped by housing, labour, or capital. "
            "These sentences should be observational and grounded — do not invent details not implied by the source. "
            "Do NOT reproduce the Patchy Anthropocene description verbatim. "
            "Apply the lens in your own words, specific to the findings of this paper.\n\n"
            "TONE: Clinical, detached, observational. No enthusiasm, no hedging. "
            "Write as if documenting a field site, not reviewing a paper.\n\n"
            "READABILITY: Write for an educated general audience, not specialists. "
            "Replace specialist jargon with plain language equivalents — for example, write 'programmed cell death' "
            "not 'apoptosis', 'reduced the spread of damage' not 'significantly inhibited lesion expansion', "
            "'genetic variation' not 'single nucleotide polymorphism', 'cell membrane damage' not 'lipid peroxidation'. "
            "Keep the scientific detail but express it in words a non-scientist can follow.\n\n"
            "STRICT CONSTRAINTS:\n"
            "1. NO HALLUCINATION: Do not invent findings, organisms, locations, or materials not present in the source text. "
            "If the source lacks detail, acknowledge the limitation rather than fabricating an analysis. "
            "If RELATED RESEARCH CONTEXT is provided, it is for your background awareness ONLY. "
            "Do NOT report findings from related articles as if they belong to the source paper. "
            "Do NOT merge, blend, or attribute related findings to the source. "
            "Your factual summary sentences must describe ONLY the source abstract.\n"
            "2. WEAK SIGNAL PROTOCOL: If the source text contains only metadata (author names, journal info, publication date) "
            "with no substantive abstract or findings, output ONLY the following message and nothing else:\n"
            "\"This paper is still hot off the press. That means the abstract is not yet indexed by scholarly databases "
            "like CrossRef, Semantic Scholar or OpenAlex. If you want to learn what the research tells us about life on Planet Mould "
            "you'll just have to read it yourself!\"\n"
            "Do not attempt a full summary from a title alone. "
            "Related research context does NOT substitute for missing source data.\n"
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

        user_message = (
            f"Analyze this research signal.\n\nTitle: {title}\nSource abstract: {excerpt}"
            + (f"\n\n{rag_context}" if rag_context else "")
        )

        # Safety fallback
        excerpt_text = str(excerpt) if excerpt else "No abstract provided."

        try:
            response = client.messages.create(
                model=model_id,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                max_tokens=550,
                temperature=0.5
            )
            raw_ai_summary = response.content[0].text.strip()
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
