#!/usr/bin/env python3
"""
Mouldwire RAG Retrieval Module

Provides semantic search over the article archive to:
1. Supply relevant context to the AI enhancement pipeline
2. Find related articles for cross-referencing
3. Power the standalone query interface

Usage as a library:
    from rag_retrieve import retrieve_context, find_related

Usage standalone:
    python rag_retrieve.py "aspergillus azole resistance"
    python rag_retrieve.py --category science "indoor air quality mould exposure"
"""

import json
import sys
import argparse

import chromadb
from chromadb.config import Settings

from rag_config import (
    CHROMA_DIR, COLLECTION_ARTICLES, COLLECTION_ABSTRACTS,
    EMBEDDING_MODEL, DEFAULT_N_RESULTS, SIMILARITY_THRESHOLD,
    VALID_CATEGORIES
)


def get_client():
    """Get persistent ChromaDB client."""
    return chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False)
    )


def get_collection(client, name):
    """Get a collection with the embedding function."""
    from chromadb.utils import embedding_functions
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    return client.get_collection(name=name, embedding_function=ef)


def retrieve_context(query, n_results=DEFAULT_N_RESULTS, category=None,
                     collection_name=COLLECTION_ARTICLES, exclude_urls=None):
    """Retrieve relevant article context for a query.

    Args:
        query: Natural language search query or article text.
        n_results: Max number of results to return.
        category: Optional category filter (science, health, indoor, media, clinical).
        collection_name: Which collection to search.
        exclude_urls: List of URLs to exclude (e.g., the article being enhanced).

    Returns:
        List of dicts with keys: document, metadata, distance
    """
    client = get_client()

    try:
        collection = get_collection(client, collection_name)
    except Exception as e:
        print(f"  RAG: Collection '{collection_name}' not found. Run rag_ingest.py first.")
        return []

    # Build where filter
    where_filter = None
    if category and category in VALID_CATEGORIES:
        where_filter = {"category": category}

    # Query
    try:
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results * 2, 20),  # Over-fetch for post-filtering
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
    except Exception as e:
        print(f"  RAG retrieval error: {e}")
        return []

    if not results or not results['documents'] or not results['documents'][0]:
        return []

    # Post-process results
    output = []
    for doc, meta, dist in zip(results['documents'][0],
                                results['metadatas'][0],
                                results['distances'][0]):
        # Skip excluded URLs
        if exclude_urls and meta.get('url') in exclude_urls:
            continue

        # Filter by similarity threshold (cosine distance: 0 = identical, 2 = opposite)
        if dist > (1 - SIMILARITY_THRESHOLD):
            continue

        output.append({
            'document': doc,
            'metadata': meta,
            'distance': dist,
            'similarity': 1 - dist  # Convert distance to similarity score
        })

        if len(output) >= n_results:
            break

    return output


def find_related(article, n_results=3):
    """Find articles related to a given article.

    Used for cross-referencing in the enhancement pipeline.

    Args:
        article: Article dict with title, excerpt/summary.
        n_results: Number of related articles to find.

    Returns:
        List of related article contexts.
    """
    # Build query from the article's content
    title = article.get('title', '')
    text = article.get('summary', '') or article.get('excerpt', '')
    query = f"{title}. {text}"[:500]  # Cap query length

    # Exclude the article itself
    exclude = [article.get('url', '')]

    return retrieve_context(
        query=query,
        n_results=n_results,
        collection_name=COLLECTION_ABSTRACTS,
        exclude_urls=exclude
    )


def format_context_for_prompt(results, max_chars=1500):
    """Format retrieved results into a text block suitable for an LLM prompt.

    Args:
        results: List from retrieve_context().
        max_chars: Maximum total characters for the context block.

    Returns:
        Formatted string of related research context.
    """
    if not results:
        return ""

    parts = []
    total_chars = 0

    for i, result in enumerate(results, 1):
        title = result['metadata'].get('title', 'Unknown')
        doc = result['document']
        sim = result.get('similarity', 0)

        entry = f"[Related finding {i} (similarity: {sim:.0%})]\n{title}\n{doc}\n"

        if total_chars + len(entry) > max_chars:
            # Truncate this entry to fit
            remaining = max_chars - total_chars - 50
            if remaining > 100:
                entry = f"[Related finding {i} (similarity: {sim:.0%})]\n{title}\n{doc[:remaining]}...\n"
            else:
                break

        parts.append(entry)
        total_chars += len(entry)

    if not parts:
        return ""

    header = "RELATED RESEARCH CONTEXT (from Mouldwire archive):\n"
    return header + '\n'.join(parts)


def search(query, n_results=5, category=None, verbose=True):
    """Standalone search interface.

    Args:
        query: Natural language search query.
        n_results: Max results.
        category: Optional category filter.
        verbose: Print detailed output.

    Returns:
        List of results.
    """
    results = retrieve_context(query, n_results=n_results, category=category)

    if verbose:
        if not results:
            print("No matching articles found.")
            return results

        print(f"\n{'=' * 60}")
        print(f"Search: \"{query}\"")
        print(f"{'=' * 60}\n")

        for i, r in enumerate(results, 1):
            meta = r['metadata']
            sim = r.get('similarity', 0)
            print(f"  [{i}] {meta.get('title', 'Unknown')}")
            print(f"      Source: {meta.get('source', '?')} | Category: {meta.get('category', '?')}")
            print(f"      Date: {meta.get('pub_date', '?')[:10]}")
            print(f"      Similarity: {sim:.1%}")
            print(f"      URL: {meta.get('url', '')}")

            # Show first 200 chars of document
            doc_preview = r['document'][:200].replace('\n', ' ')
            print(f"      Preview: {doc_preview}...")
            print()

    return results


def main():
    parser = argparse.ArgumentParser(description='Mouldwire RAG Search')
    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('--category', '-c', choices=VALID_CATEGORIES,
                        help='Filter by category')
    parser.add_argument('--n', type=int, default=5, help='Number of results')
    args = parser.parse_args()

    if not args.query:
        print("Usage: python rag_retrieve.py \"your search query\"")
        print("       python rag_retrieve.py --category science \"aspergillus resistance\"")
        return

    search(args.query, n_results=args.n, category=args.category)


if __name__ == '__main__':
    main()
