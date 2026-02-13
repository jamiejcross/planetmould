#!/usr/bin/env python3
"""
Mouldwire RAG Configuration

Central configuration for the Retrieval-Augmented Generation system.
Shared across ingestion, retrieval, and query modules.
"""

import os

# --- Paths ---
CHROMA_DIR = os.path.join(os.path.dirname(__file__), 'chroma_db')
NEWS_FILE = 'mould_news.json'
ENHANCED_FILE = 'articles_enhanced.json'
CUSTOM_SOURCES_FILE = 'custom_sources.json'

# --- ChromaDB Collection Names ---
COLLECTION_ARTICLES = 'mouldwire_articles'
COLLECTION_ABSTRACTS = 'mouldwire_abstracts'

# --- Embedding Model ---
# sentence-transformers model for local embeddings (no API key needed)
# all-MiniLM-L6-v2: 384-dim, fast, good for semantic similarity
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

# --- Retrieval Settings ---
DEFAULT_N_RESULTS = 5          # Number of similar articles to retrieve
SIMILARITY_THRESHOLD = 0.35    # Minimum cosine similarity (lower = more permissive)

# --- Chunking ---
MAX_CHUNK_LENGTH = 500         # Max words per chunk (for long abstracts)
CHUNK_OVERLAP = 50             # Word overlap between chunks

# --- HuggingFace (for query interface) ---
HF_MODEL = os.getenv('HF_MODEL', 'meta-llama/Meta-Llama-3-8B-Instruct')
HF_TOKEN = os.getenv('HF_TOKEN', '')

# --- Categories for metadata filtering ---
VALID_CATEGORIES = ['science', 'health', 'indoor', 'media', 'clinical', 'custom']

# --- Google Drive PDF Enrichment ---
GDRIVE_PDF_FOLDER_ID = os.getenv('GDRIVE_PDF_FOLDER_ID', '')
MISSING_ABSTRACTS_JSON = 'missing_abstracts.json'
MISSING_ABSTRACTS_CSV = 'missing_abstracts.csv'
