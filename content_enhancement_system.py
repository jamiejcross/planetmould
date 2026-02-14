#!/usr/bin/env python3
"""
Content Enhancement System - Research Edition
=============================================
Reengineered for: 
1. 5-7 sentence long-form research summaries.
2. Anthropological/Infrastructural focus.
3. Mistral-7B Instruct integration.
"""

import requests
import json
from typing import List, Dict, Optional
import feedparser
from dataclasses import dataclass
import re

@dataclass
class Article:
    title: str
    content: str
    url: str
    source: str
    published_date: Optional[str] = None

class ContentEnhancer:
    def __init__(self, ai_provider: str = "huggingface"):
        self.ai_provider = ai_provider
        self.hf_token = None  
      # Change v0.2 to v0.3 here:
        self.hf_model = "mistralai/Mistral-7B-Instruct-v0.3"
        
    def set_api_key(self, key: str):
        self.hf_token = key

def _sanitize_for_ai(self, article: Article) -> str:
        text = article.content
        
        # 1. Strip Title
        if text.lower().startswith(article.title.lower()):
            text = text[len(article.title):].strip()
        
        # 2. Aggressively strip Journal Metadata (Volume, Issue, Pages)
        metadata_patterns = [
            r'Journal of.*?,? vol\w*\.? \d+.*?(?:\.|$)',
            r'Volume \d+, Issue \d+.*?(?:\.|$)',
            r'https?://\S+',
            r'Page \d+-\d+',
            r'Published: \d{1,2} \w+ \d{4}'
        ]
        for pattern in metadata_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
        return text.strip()

   def generate_research_summary(self, article: Article) -> str:
        """Updated for v0.3 and the Chat Completions requirement"""
        sanitized_text = self._sanitize_for_ai(article)
        
        if len(sanitized_text) < 50:
            return sanitized_text if len(sanitized_text) > 0 else article.title

        # THIS SECTION IS THE PROMPT We must use the 'messages' format for conversational models
        messages = [
            {
                system_prompt = (
            "You are a detached field researcher documenting human-nonhuman interactions in the Anthropocene.\n\n"
          
            "ANALYTICAL LENS (Patchy Anthropocene):\n"
            "The Patchy Anthropocene lens brings 'located relations between humans and nonhumans into focus within "
            "the broader ongoing material transformations and ruptures brought on by colonialism, imperialism, and capitalism' "
            "(Tsing, Deger, Saxemna, and Zhou 2024, Field Guide to the Patchy Anthropocene). "
            "As Cross writes, (The moulds at the end of the corridor 2025), "
            "The same species of mould flagged as planetary pathogens can also be "
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
            "\"This publication is still hot off the press. That means the paper is not yet indexed by global "
            "databases like CrossRef, Semantic Scholar or OpenAlex. If you want to learn what the research might have to say about life on Planet Mould "
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
    },
    {
        "role": "user",
        "content": f"Analyze this biosphere signal: {article.title}. {sanitized_text[:2000]}"
    }
]
       

        if self.ai_provider == "huggingface":
            # NOTE: The URL changes to include '/v1/chat/completions'
            api_url = f"https://api-inference.huggingface.co/models/{self.hf_model}/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.hf_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.hf_model,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            try:
                # Increased timeout for the v0.3 model 'wake up' time
                response = requests.post(api_url, headers=headers, json=payload, timeout=90)
                
                if response.status_code == 200:
                    result = response.json()
                    # The response path is different for Chat!
                    summary = result['choices'][0]['message']['content']
                    if summary.strip():
                        return summary.strip()
                else:
                    print(f"API Error ({response.status_code}): {response.text}")

            except Exception as e:
                print(f"Connection error: {e}")

            # Fallback to snippet if AI is sleeping
            return sanitized_text[:400] + "..."
        
        return sanitized_text[:300] + "..."
            
            }
            
            response = requests.post(api_url, headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()
                summary = result[0].get("generated_text", "") if isinstance(result, list) else ""
                # Sentence Case cleanup
                return summary.strip().capitalize()
            return f"Summary generation failed (Error {response.status_code})"
        
        return sanitized_text[:300] + "..."

    def process_article(self, article: Article) -> Dict:
        """Main entry point for processing"""
        summary = self.generate_research_summary(article)
        
        return {
            "title": article.title,
            "url": article.url,
            "source": article.source,
            "pubDate": article.published_date,
            "summary": summary,
            "enhanced": True,
            "keywords": self.extract_keywords(article)
        }

    def extract_keywords(self, article: Article) -> List[str]:
        # Focus keywords on infrastructure and fungi
        mould_terms = ['infrastructure', 'materiality', 'toxicity', 'assemblage', 'biopolitics', 'decay']
        text = (article.title + " " + article.content).lower()
        return [term for term in mould_terms if term in text]
