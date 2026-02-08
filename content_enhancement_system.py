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
        self.hf_model = "mistralai/Mistral-7B-Instruct-v0.2" # Upgraded for better reasoning
        
    def set_api_key(self, key: str):
        self.hf_token = key

    def _sanitize_for_ai(self, article: Article) -> str:
        text = article.content
        if text.lower().startswith(article.title.lower()):
            text = text[len(article.title):].strip()
        
        # Strip metadata noise
        patterns = [r'Publication date:.*?(?:\.|$)', r'Source:.*?(?:\.|$)', r'https?://\S+']
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text.strip()

    def generate_research_summary(self, article: Article) -> str:
def generate_research_summary(self, article: Article) -> str:
        """The core anthropological summary engine with safety fallbacks"""
        sanitized_text = self._sanitize_for_ai(article)
        
        # --- FALLBACK 1: If the article is too short to summarize, return the excerpt ---
        if len(sanitized_text) < 50:
            return sanitized_text if len(sanitized_text) > 0 else article.title

        # Construct the specialized research prompt
        prompt = f"<s>[INST] Task: Provide a 5-7 sentence summary for an anthropologist tracking infrastructure and fungal life.\n\n" \
                 f"Article: {article.title}. {sanitized_text[:1500]}\n\n" \
                 f"Focus on: 1. Core summary 2. Built environment/infrastructure 3. Fungal sociality 4. Anthropological hooks. [/INST]</s>"

        if self.ai_provider == "huggingface":
            api_url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            payload = {
                "inputs": prompt,
                "parameters": {"max_new_tokens": 500, "temperature": 0.7, "return_full_text": False}
            }
            
            try:
                response = requests.post(api_url, headers=headers, json=payload, timeout=45)
                if response.status_code == 200:
                    result = response.json()
                    summary = result[0].get("generated_text", "") if isinstance(result, list) else ""
                    if summary.strip():
                        return summary.strip().capitalize()
            except Exception as e:
                print(f"AI Error: {e}")

            # --- FALLBACK 2: If AI fails/timeouts, return the original sanitized text ---
            return sanitized_text[:500] + "..."
        
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
