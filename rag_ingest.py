#!/usr/bin/env python3
"""
Mouldwire RAG Ingestion Module

Reads articles from mould_news.json and articles_enhanced.json,
creates embeddings using sentence-transformers, and stores them
in a ChromaDB collection.

Designed to run:
- Locally for development
- In GitHub Actions as part of the 6-hour pipeline

Usage:
    python rag_ingest.py                    # Full ingest
    python rag_ingest.py --incremental      # Only new articles
    python rag_ingest.py --rebuild          # Drop and rebuild collection
"""

import json
import os
import sys
import hashlib
import argparse
from datetime import datetime, timezone

import chromadb
from chromadb.config import Settings

from rag_config import (
    CHROMA_DIR, NEWS_FILE, ENHANCED_FILE,
    COLLECTION_ARTICLES, COLLECTION_ABSTRACTS,
    EMBEDDING_MODEL, MAX_CHUNK_LENGTH, CHUNK_OVERLAP
)


def get_client():
    """Create a persistent ChromaDB client."""
    os.makedirs(CHROMA_DIR, exist_ok=True)
    return chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False)
    )


def get_or_create_collection(client, name):
    """Get or create a ChromaDB collection with sentence-transformer embeddings."""
    from chromadb.utils import embedding_functions
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    return client.get_or_create_collection(
        name=name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )


def article_id(article):
    """Generate a stable ID for an article from its URL."""
    url = article.get('url', '')
    return hashlib.md5(url.encode()).hexdigest()


def chunk_text(text, max_words=MAX_CHUNK_LENGTH, overlap=CHUNK_OVERLAP):
    """Split long text into overlapping chunks.
    Returns a list of text chunks."""
    words = text.split()
    if len(words) <= max_words:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = start + max_words
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        start = end - overlap
    return chunks


def prepare_article_document(article):
    """Prepare a single article for ChromaDB ingestion.

    Returns (doc_id, document_text, metadata) or None if article is unusable.
    """
    url = article.get('url', '')
    title = article.get('title', '')
    if not url or not title:
        return None

    # Build the richest available text representation
    parts = [f"Title: {title}"]

    # Prefer enhanced summary, fall back to excerpt
    summary = article.get('summary', '')
    excerpt = article.get('excerpt', '')
    abstract_text = summary if summary else excerpt

    if abstract_text:
        parts.append(abstract_text)

    # Add source and category for context
    source = article.get('source', '')
    if source:
        parts.append(f"Source: {source}")

    # Add keywords if available
    keywords = article.get('keywords', [])
    if keywords:
        parts.append(f"Keywords: {', '.join(keywords[:5])}")

    document = '\n'.join(parts)

    # Metadata for filtering
    metadata = {
        'url': url,
        'title': title,
        'source': source or 'unknown',
        'category': article.get('category', 'unknown'),
        'pub_date': article.get('pubDate', ''),
        'enhanced': str(article.get('enhanced', False)),
        'abstract_source': article.get('abstract_source', 'none'),
    }

    return article_id(article), document, metadata


def ingest_articles(rebuild=False, incremental=True):
    """Main ingestion routine.

    Args:
        rebuild: If True, drop and recreate the collection.
        incremental: If True, skip articles already in the collection.
    """
    print("=" * 60)
    print("Mouldwire RAG Ingestion")
    print("=" * 60)

    client = get_client()

    # Handle rebuild
    if rebuild:
        try:
            client.delete_collection(COLLECTION_ARTICLES)
            print("  Dropped existing collection for rebuild.")
        except Exception:
            pass

    collection = get_or_create_collection(client, COLLECTION_ARTICLES)
    existing_count = collection.count()
    print(f"  Collection '{COLLECTION_ARTICLES}': {existing_count} existing documents")

    # Load articles — prefer enhanced, merge with raw for coverage
    articles = {}

    if os.path.exists(NEWS_FILE):
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        for a in raw:
            articles[a.get('url', '')] = a
        print(f"  Loaded {len(raw)} articles from {NEWS_FILE}")

    if os.path.exists(ENHANCED_FILE):
        with open(ENHANCED_FILE, 'r', encoding='utf-8') as f:
            enhanced = json.load(f)
        for a in enhanced:
            # Enhanced articles overwrite raw (richer content)
            articles[a.get('url', '')] = a
        print(f"  Loaded {len(enhanced)} articles from {ENHANCED_FILE}")

    if not articles:
        print("  No articles found. Nothing to ingest.")
        return

    all_articles = list(articles.values())
    print(f"  Total unique articles: {len(all_articles)}")

    # Get existing IDs for incremental mode
    existing_ids = set()
    if incremental and existing_count > 0:
        # ChromaDB get() returns all IDs
        try:
            result = collection.get(include=[])
            existing_ids = set(result['ids'])
        except Exception:
            pass

    # Prepare documents
    docs_to_add = []
    skipped = 0

    for article in all_articles:
        prepared = prepare_article_document(article)
        if not prepared:
            continue

        doc_id, document, metadata = prepared

        # Skip if already ingested (incremental mode)
        if incremental and doc_id in existing_ids:
            skipped += 1
            continue

        # Chunk long documents
        chunks = chunk_text(document)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_{i}" if len(chunks) > 1 else doc_id
            chunk_meta = {**metadata, 'chunk_index': i, 'total_chunks': len(chunks)}
            docs_to_add.append((chunk_id, chunk, chunk_meta))

    if skipped:
        print(f"  Skipped {skipped} already-ingested articles.")

    if not docs_to_add:
        print("  No new documents to ingest.")
        return

    # Batch ingest (ChromaDB recommends batches of ~5000)
    batch_size = 100
    total_added = 0

    for i in range(0, len(docs_to_add), batch_size):
        batch = docs_to_add[i:i + batch_size]
        ids = [d[0] for d in batch]
        documents = [d[1] for d in batch]
        metadatas = [d[2] for d in batch]

        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        total_added += len(batch)
        print(f"  Ingested batch {i // batch_size + 1}: {len(batch)} documents")

    final_count = collection.count()
    print(f"\n✅ Ingestion complete: {total_added} documents added. Collection now has {final_count} documents.")

    # Also ingest into abstracts-only collection for focused retrieval
    ingest_abstracts(client, all_articles, rebuild, existing_ids)


def ingest_abstracts(client, articles, rebuild, skip_ids):
    """Ingest a separate collection of just abstracts/summaries for focused retrieval."""
    if rebuild:
        try:
            client.delete_collection(COLLECTION_ABSTRACTS)
        except Exception:
            pass

    collection = get_or_create_collection(client, COLLECTION_ABSTRACTS)

    docs_to_add = []
    for article in articles:
        doc_id = article_id(article)
        if doc_id in skip_ids:
            continue

        # Only ingest if we have substantial text
        summary = article.get('summary', '')
        excerpt = article.get('excerpt', '')
        text = summary if summary else excerpt

        if not text or len(text) < 30:
            continue

        metadata = {
            'url': article.get('url', ''),
            'title': article.get('title', ''),
            'category': article.get('category', 'unknown'),
            'pub_date': article.get('pubDate', ''),
            'abstract_source': article.get('abstract_source', 'none'),
        }

        docs_to_add.append((doc_id, text, metadata))

    if docs_to_add:
        ids = [d[0] for d in docs_to_add]
        documents = [d[1] for d in docs_to_add]
        metadatas = [d[2] for d in docs_to_add]

        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        print(f"  Abstracts collection: {len(docs_to_add)} documents ingested. Total: {collection.count()}")


def main():
    parser = argparse.ArgumentParser(description='Mouldwire RAG Ingestion')
    parser.add_argument('--rebuild', action='store_true', help='Drop and rebuild collections')
    parser.add_argument('--incremental', action='store_true', default=True, help='Only add new articles (default)')
    parser.add_argument('--full', action='store_true', help='Re-ingest all articles')
    args = parser.parse_args()

    rebuild = args.rebuild
    incremental = not args.full and not rebuild

    ingest_articles(rebuild=rebuild, incremental=incremental)


if __name__ == '__main__':
    main()
