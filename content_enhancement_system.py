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
        sanitized_text = self._sanitize_for_ai(article)
        
        if len(sanitized_text) < 50:
            return sanitized_text if len(sanitized_text) > 0 else article.title

        # REFINED PROMPT: More aggressive instructions to skip citations
        prompt = f"<s>[INST] You are an expert anthropologist. Summarize the following news in 5 to 7 detailed sentences. 
        Focus on infrastructure, fungal sociality, and the built environment. 
        IGNORE all journal volume numbers, dates, and citations. 
        Start your summary immediately.
        
        Article Content: {article.title}. {sanitized_text[:1200]} [/INST]</s>"

        if self.ai_provider == "huggingface":
            api_url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 400, # Increased for longer summaries
                    "temperature": 0.7,
                    "repetition_penalty": 1.2, # Prevents the AI from repeating the input
                    "return_full_text": False
                },
                "options": {
                    "wait_for_model": True, # CRITICAL: Prevents "cold start" failures
                    "use_cache": False
                }
            }
            
            try:
                response = requests.post(api_url, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    summary = result[0].get("generated_text", "")
                    if len(summary.strip()) > 100: # Ensure we got a real summary
                        return summary.strip()
            except Exception as e:
                print(f"Connection error: {e}")

            # Fallback if AI fails: show first 300 chars of the actual content
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
