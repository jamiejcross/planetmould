"""
Content Enhancement System for Mouldwire News Aggregator
========================================================

This system provides three main features:
1. Automated article summaries
2. Smart categorization
3. Keyword extraction

Free AI options included:
- Hugging Face (free tier)
- Ollama (completely free, local)
- OpenAI (limited free credits)
"""

import requests
import json
from typing import List, Dict, Optional
import feedparser
from dataclasses import dataclass
import re


@dataclass
class Article:
    """Represents a news article"""
    title: str
    content: str
    url: str
    source: str
    published_date: Optional[str] = None
    

class ContentEnhancer:
    """Main class for enhancing article content with AI"""
    
    def __init__(self, ai_provider: str = "huggingface"):
        """
        Initialize the content enhancer
        
        Args:
            ai_provider: 'huggingface', 'ollama', or 'openai'
        """
        self.ai_provider = ai_provider
        self.hf_api_url = "https://router.huggingface.co/models/"
        self.hf_token = None  # Set via set_api_key()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.openai_key = None
        
    def set_api_key(self, key: str, provider: str = None):
        """Set API key for the chosen provider"""
        provider = provider or self.ai_provider
        if provider == "huggingface":
            self.hf_token = key
        elif provider == "openai":
            self.openai_key = key
    
    # ============= SUMMARIZATION =============
    
    def summarize_article_hf(self, text: str, max_length: int = 150) -> str:
        """
        Generate summary using Hugging Face (FREE)
        
        Model: facebook/bart-large-cnn (excellent for news summarization)
        """
        model = "facebook/bart-large-cnn"
        headers = {"Authorization": f"Bearer {self.hf_token}"} if self.hf_token else {}
        
        # Truncate input to avoid API limits (1024 tokens max for BART)
        words = text.split()
        if len(words) > 400:
            text = " ".join(words[:400])
        
        payload = {
            "inputs": text,
            "parameters": {
                "max_length": max_length,
                "min_length": 30,
                "do_sample": False
            }
        }
        
        response = requests.post(
            self.hf_api_url + model,
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return result[0]["summary_text"]
        else:
            raise Exception(f"HF API Error: {response.text}")
    
    def summarize_article_ollama(self, text: str, max_length: int = 150) -> str:
        """
        Generate summary using Ollama (COMPLETELY FREE, runs locally)
        
        Recommended models:
        - llama3.2 (fast, efficient)
        - mistral (good balance)
        - llama3.1:8b (higher quality)
        
        Install: curl -fsSL https://ollama.com/install.sh | sh
        Then: ollama pull llama3.2
        """
        prompt = f"""Summarize this scientific article about mould/fungi in 2-3 sentences. 
Focus on the key findings, methodology, or health implications.

Article: {text[:1500]}

Summary:"""
        
        payload = {
            "model": "llama3.2",  # Change to your installed model
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 100
            }
        }
        
        response = requests.post(self.ollama_url, json=payload)
        
        if response.status_code == 200:
            return response.json()["response"].strip()
        else:
            raise Exception(f"Ollama Error: {response.text}")
    
    def summarize_article_openai(self, text: str, max_length: int = 150) -> str:
        """
        Generate summary using OpenAI API (limited free credits)
        
        Note: New accounts get $5 free credit
        """
        import openai
        
        openai.api_key = self.openai_key
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Cheapest option
            messages=[
                {"role": "system", "content": "You are a scientific summarizer specializing in mycology and mould research."},
                {"role": "user", "content": f"Summarize this article in 2-3 sentences:\n\n{text[:2000]}"}
            ],
            max_tokens=max_length,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    
    def summarize(self, article: Article) -> str:
        """Main summarization method - routes to chosen provider"""
        text = f"{article.title}. {article.content}"
        
        if self.ai_provider == "huggingface":
            return self.summarize_article_hf(text)
        elif self.ai_provider == "ollama":
            return self.summarize_article_ollama(text)
        elif self.ai_provider == "openai":
            return self.summarize_article_openai(text)
        else:
            raise ValueError(f"Unknown provider: {self.ai_provider}")
    
    # ============= CATEGORIZATION =============
    
    def categorize_article_hf(self, text: str, categories: List[str]) -> Dict[str, float]:
        """
        Categorize using Hugging Face zero-shot classification (FREE)
        
        Model: facebook/bart-large-mnli
        """
        model = "facebook/bart-large-mnli"
        headers = {"Authorization": f"Bearer {self.hf_token}"} if self.hf_token else {}
        
        payload = {
            "inputs": text[:500],  # Limit for faster processing
            "parameters": {
                "candidate_labels": categories
            }
        }
        
        response = requests.post(
            self.hf_api_url + model,
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return dict(zip(result["labels"], result["scores"]))
        else:
            raise Exception(f"HF API Error: {response.text}")
    
    def categorize_article_ollama(self, text: str, categories: List[str]) -> Dict[str, float]:
        """Categorize using Ollama (FREE, local)"""
        
        categories_str = ", ".join(categories)
        prompt = f"""Classify this article into one or more of these categories: {categories_str}

Article: {text[:800]}

Return ONLY a JSON object with category names as keys and confidence scores (0-1) as values.
Example: {{"Clinical": 0.8, "Health & Environment": 0.6}}

JSON:"""
        
        payload = {
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1}
        }
        
        response = requests.post(self.ollama_url, json=payload)
        
        if response.status_code == 200:
            result = response.json()["response"]
            return json.loads(result)
        else:
            raise Exception(f"Ollama Error: {response.text}")
    
    def categorize(self, article: Article, categories: List[str] = None) -> Dict[str, float]:
        """Main categorization method"""
        
        if categories is None:
            # Default categories from your site
            categories = [
                "Scientific Research",
                "Popular Media",
                "Health & Environment",
                "Housing & Indoor Air",
                "Clinical"
            ]
        
        text = f"{article.title}. {article.content}"
        
        if self.ai_provider == "huggingface":
            return self.categorize_article_hf(text, categories)
        elif self.ai_provider == "ollama":
            return self.categorize_article_ollama(text, categories)
        else:
            # For OpenAI, similar to Ollama approach
            return self.categorize_article_ollama(text, categories)
    
    # ============= KEYWORD EXTRACTION =============
    
    def extract_keywords_hf(self, text: str, top_k: int = 10) -> List[str]:
        """
        Extract keywords using KeyBERT-style approach with sentence transformers
        
        This uses a simple TF-IDF + filtering approach for the free tier
        """
        from collections import Counter
        import string
        
        # Simple keyword extraction (can be enhanced with transformers library)
        # Remove punctuation and convert to lowercase
        text_clean = text.lower()
        for char in string.punctuation:
            text_clean = text_clean.replace(char, ' ')
        
        words = text_clean.split()
        
        # Filter stopwords and short words
        stopwords = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                        'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
                        'those', 'it', 'its', 'their', 'our', 'your'])
        
        filtered_words = [w for w in words if len(w) > 3 and w not in stopwords]
        
        # Count frequencies
        word_freq = Counter(filtered_words)
        
        # Focus on mould-related scientific terms
        mould_terms = ['mould', 'mold', 'fungi', 'fungal', 'aspergillus', 'penicillium',
                       'mycotoxin', 'spore', 'indoor', 'moisture', 'ventilation', 
                       'respiratory', 'asthma', 'allergen', 'species', 'exposure']
        
        keywords = []
        for term in mould_terms:
            if term in word_freq:
                keywords.append(term)
        
        # Add other high-frequency terms
        for word, count in word_freq.most_common(top_k * 2):
            if word not in keywords and len(keywords) < top_k:
                keywords.append(word)
        
        return keywords[:top_k]
    
    def extract_keywords_ollama(self, text: str, top_k: int = 10) -> List[str]:
        """Extract keywords using Ollama"""
        
        prompt = f"""Extract the {top_k} most important keywords or key phrases from this article about mould/fungi.
Focus on scientific terms, species names, methodologies, and health-related concepts.

Article: {text[:1000]}

Return ONLY a JSON array of keywords/phrases.
Example: ["Aspergillus fumigatus", "indoor air quality", "respiratory health", "mycotoxins"]

JSON:"""
        
        payload = {
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1}
        }
        
        response = requests.post(self.ollama_url, json=payload)
        
        if response.status_code == 200:
            result = response.json()["response"]
            return json.loads(result)
        else:
            raise Exception(f"Ollama Error: {response.text}")
    
    def extract_keywords(self, article: Article, top_k: int = 10) -> List[str]:
        """Main keyword extraction method"""
        text = f"{article.title}. {article.content}"
        
        if self.ai_provider == "ollama":
            return self.extract_keywords_ollama(text, top_k)
        else:
            return self.extract_keywords_hf(text, top_k)
    
    # ============= ENHANCED PROCESSING =============
    
    def process_article(self, article: Article) -> Dict:
        """Process article with all enhancements"""
        
        print(f"Processing: {article.title}")
        
        try:
            summary = self.summarize(article)
            categories = self.categorize(article)
            keywords = self.extract_keywords(article)
            
            # Get primary category (highest score)
            primary_category = max(categories.items(), key=lambda x: x[1])
            
            return {
                "original": article,
                "summary": summary,
                "categories": categories,
                "primary_category": primary_category[0],
                "keywords": keywords,
                "enhanced": True
            }
        except Exception as e:
            print(f"Error processing article: {e}")
            return {
                "original": article,
                "enhanced": False,
                "error": str(e)
            }


# ============= RSS FEED PROCESSOR =============

class RSSProcessor:
    """Process RSS feeds and enhance articles"""
    
    def __init__(self, enhancer: ContentEnhancer):
        self.enhancer = enhancer
    
    def fetch_rss_feed(self, feed_url: str) -> List[Article]:
        """Fetch and parse RSS feed"""
        feed = feedparser.parse(feed_url)
        articles = []
        
        for entry in feed.entries:
            # Extract content (different RSS feeds use different fields)
            content = ""
            if hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description
            elif hasattr(entry, 'content'):
                content = entry.content[0].value
            
            # Clean HTML tags
            content = re.sub('<[^<]+?>', '', content)
            
            article = Article(
                title=entry.title,
                content=content,
                url=entry.link,
                source=feed.feed.title if hasattr(feed.feed, 'title') else feed_url,
                published_date=entry.published if hasattr(entry, 'published') else None
            )
            articles.append(article)
        
        return articles
    
    def process_feed(self, feed_url: str) -> List[Dict]:
        """Fetch and enhance all articles from a feed"""
        articles = self.fetch_rss_feed(feed_url)
        enhanced_articles = []
        
        for article in articles:
            enhanced = self.enhancer.process_article(article)
            enhanced_articles.append(enhanced)
        
        return enhanced_articles


# ============= USAGE EXAMPLES =============

def example_huggingface():
    """Example using Hugging Face (FREE but may have rate limits)"""
    
    print("\n=== Using Hugging Face ===\n")
    
    enhancer = ContentEnhancer(ai_provider="huggingface")
    # Optional: set API key for faster processing
    # enhancer.set_api_key("your_hf_token_here")
    
    # Test article
    test_article = Article(
        title="Aspergillus fumigatus in Indoor Environments",
        content="A recent study found that Aspergillus fumigatus spores were present in 78% of water-damaged buildings tested. The research team from the University of Helsinki analyzed air samples from 150 homes and found correlations between moisture levels and fungal concentrations. Residents of affected homes showed higher rates of respiratory symptoms.",
        url="https://example.com/article1",
        source="Journal of Mycology"
    )
    
    result = enhancer.process_article(test_article)
    
    print(f"Title: {result['original'].title}")
    print(f"\nSummary: {result['summary']}")
    print(f"\nPrimary Category: {result['primary_category']}")
    print(f"\nAll Categories: {result['categories']}")
    print(f"\nKeywords: {', '.join(result['keywords'])}")


def example_ollama():
    """Example using Ollama (COMPLETELY FREE, requires local installation)"""
    
    print("\n=== Using Ollama (Local) ===\n")
    print("Make sure Ollama is installed and running:")
    print("  curl -fsSL https://ollama.com/install.sh | sh")
    print("  ollama pull llama3.2")
    print()
    
    enhancer = ContentEnhancer(ai_provider="ollama")
    
    test_article = Article(
        title="Mycotoxin Detection in Agricultural Settings",
        content="This study presents a novel biosensor for detecting aflatoxins in grain storage facilities. The device uses immunoassay technology and can detect contamination levels as low as 2 ppb. Field tests in corn silos showed 95% accuracy compared to laboratory methods.",
        url="https://example.com/article2",
        source="Agricultural Research"
    )
    
    result = enhancer.process_article(test_article)
    
    print(f"Title: {result['original'].title}")
    print(f"\nSummary: {result['summary']}")
    print(f"\nPrimary Category: {result['primary_category']}")
    print(f"\nAll Categories: {result['categories']}")
    print(f"\nKeywords: {', '.join(result['keywords'])}")


def example_batch_processing():
    """Example processing multiple RSS feeds"""
    
    print("\n=== Batch Processing RSS Feeds ===\n")
    
    enhancer = ContentEnhancer(ai_provider="ollama")  # Change as needed
    processor = RSSProcessor(enhancer)
    
    # Example feeds (replace with your actual feeds)
    feeds = [
        "https://www.sciencedaily.com/rss/plants_animals/fungi.xml",
        # Add your ~50 feeds here
    ]
    
    all_enhanced = []
    for feed_url in feeds:
        print(f"\nProcessing feed: {feed_url}")
        try:
            enhanced_articles = processor.process_feed(feed_url)
            all_enhanced.extend(enhanced_articles)
            print(f"  ✓ Processed {len(enhanced_articles)} articles")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Save to JSON for your website
    with open("enhanced_articles.json", "w") as f:
        json.dump([{
            "title": a["original"].title,
            "url": a["original"].url,
            "source": a["original"].source,
            "summary": a.get("summary", ""),
            "category": a.get("primary_category", ""),
            "keywords": a.get("keywords", [])
        } for a in all_enhanced if a["enhanced"]], f, indent=2)
    
    print(f"\n✓ Saved {len(all_enhanced)} enhanced articles to enhanced_articles.json")


if __name__ == "__main__":
    print("Content Enhancement System for Mouldwire")
    print("=" * 50)
    print("\nChoose an example to run:")
    print("1. Hugging Face (free, cloud)")
    print("2. Ollama (free, local)")
    print("3. Batch process RSS feeds")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == "1":
        example_huggingface()
    elif choice == "2":
        example_ollama()
    elif choice == "3":
        example_batch_processing()
    else:
        print("Invalid choice")

