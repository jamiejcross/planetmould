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
                "role": "system",         
                "content": (
                    "You are the Mouldwire Inference Engine, specialized in 'Patchy Anthropocene' logic. "
                    "Analyze environmental and biological news through a social science and humanities lens in 5-7 sentences. Use valid HTML tags for styling.\n\n"
                    "STRICT CONSTRAINTS:\n"
                    "1. NO HALLUCINATION: Do not invent details, dates, or scientific findings not present in the source.\n"
                    "2. WEAK SIGNAL PROTOCOL: If the source text is sparse, ambiguous, or lacks depth, "
                    "note the data's limitations and do not output a [SUMMARY]' .\n"
                    "3. LINGUISTIC FIDELITY: If a sentence in the source is clear, evocative, and academically "
                    "significant, reuse it verbatim in the summary rather than paraphrasing.\n"
                    "4. NO TITLE REPETITION: Do not mention the title of the article or phrases like 'This article discusses' in your output.\n"
                    "4.1 NO ACRONYMS: Do not use acronyms in the summary. Only use the full form of a name or organisation once."\n
                    "5. REASONING STEP: Before generating the final HTML, identify the three most significant material-social interactions" 
                    "in the text. Do not output this list, but use it to inform your analysis."\n
                    "6. MATERIAL SPECIFICITY: Do not use words like 'infrastructure' or 'environment' without "
                    "naming the specific material (e.g., 'damp gypsum board', '1950s copper piping').\n"
                    "7. SCALE ANCHORING: Identify the primary scale of the signal (Molecular, Architectural, or Planetary).\n"
                    "8. SITUATEDNESS: Always identify the geographic or digital 'site' of the signal.\n\n"
                    "OUTPUT STRUCTURE:\n"
                    "Output MUST follow this exact structure:\n"
                    "A clinical overview of the research.\n"
                    "An analysis of what it tells us about relations between humans,"
                    "infrastructure, materiality, and fungi in the anthropocene.\n\n
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
