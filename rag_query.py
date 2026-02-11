#!/usr/bin/env python3
"""
Mouldwire RAG Query Interface

Ask natural language questions across qthe Mouldwire archive.
Retrieves relevant articles from ChromaDB, then uses Llama-3
to generate grounded answers with citations.

Usage:
    python rag_query.py "What is known about azole resistance in Aspergillus?"
    python rag_query.py --category health "How does indoor mould affect respiratory health?"
    python rag_query.py --interactive  # Enter interactive mode
"""

import json
import os
import sys
import argparse

from rag_config import (
    HF_MODEL, HF_TOKEN, DEFAULT_N_RESULTS, VALID_CATEGORIES
)
from rag_retrieve import retrieve_context, format_context_for_prompt


def get_llm_client():
    """Create a HuggingFace Inference client."""
    token = HF_TOKEN or os.getenv('HF_TOKEN', '')
    if not token:
        print("Warning: No HF_TOKEN set. LLM queries will fail.")
        print("Set HF_TOKEN environment variable or pass via --token flag.")
        return None

    from huggingface_hub import InferenceClient
    return InferenceClient(model=HF_MODEL, token=token)


def build_query_prompt(question, context_text):
    """Build the system + user messages for the query."""
    system_prompt = (
        "You are a research assistant for the Mouldwire news service, "
        "an academic project documenting mould-related research in the Anthropocene.\n\n"
        "RULES:\n"
        "1. Answer ONLY using the provided research context. Do not invent findings.\n"
        "2. If the context does not contain enough information, say so clearly.\n"
        "3. Cite specific articles by title when referencing findings.\n"
        "4. Write in a clear, accessible style — avoid specialist jargon.\n"
        "5. Keep answers concise: 3-5 sentences for simple questions, up to a paragraph for complex ones.\n"
        "6. If multiple articles address the question, synthesise across them.\n"
        "7. Do not use the first person.\n"
    )

    user_message = f"{context_text}\n\nQUESTION: {question}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]


def ask(question, category=None, n_results=DEFAULT_N_RESULTS,
        client=None, verbose=True):
    """Ask a question across the Mouldwire archive.

    Args:
        question: Natural language question.
        category: Optional category filter.
        n_results: Number of articles to retrieve for context.
        client: HuggingFace InferenceClient (created if None).
        verbose: Print detailed output.

    Returns:
        Dict with 'answer', 'sources', and 'context_used'.
    """
    # Step 1: Retrieve relevant context
    if verbose:
        print(f"\nSearching archive for: \"{question}\"...")

    results = retrieve_context(
        query=question,
        n_results=n_results,
        category=category
    )

    if not results:
        msg = "No relevant articles found in the archive for this question."
        if verbose:
            print(f"\n{msg}")
        return {'answer': msg, 'sources': [], 'context_used': ''}

    # Step 2: Format context for the LLM
    context_text = format_context_for_prompt(results, max_chars=2000)

    if verbose:
        print(f"  Found {len(results)} relevant articles.")
        for r in results:
            sim = r.get('similarity', 0)
            title = r['metadata'].get('title', '?')
            print(f"    [{sim:.0%}] {title[:70]}")

    # Step 3: Generate answer with LLM
    if client is None:
        client = get_llm_client()

    if client is None:
        # No LLM available — return context only
        sources = [{'title': r['metadata'].get('title', ''),
                     'url': r['metadata'].get('url', ''),
                     'similarity': r.get('similarity', 0)}
                    for r in results]
        return {
            'answer': 'LLM not available. Relevant articles found (see sources).',
            'sources': sources,
            'context_used': context_text
        }

    messages = build_query_prompt(question, context_text)

    try:
        response = client.chat_completion(
            messages=messages,
            max_tokens=500,
            temperature=0.3  # Lower temperature for factual accuracy
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer: {e}"

    # Step 4: Compile sources
    sources = []
    for r in results:
        sources.append({
            'title': r['metadata'].get('title', ''),
            'url': r['metadata'].get('url', ''),
            'source': r['metadata'].get('source', ''),
            'category': r['metadata'].get('category', ''),
            'similarity': r.get('similarity', 0)
        })

    if verbose:
        print(f"\n{'=' * 60}")
        print("ANSWER:")
        print(f"{'=' * 60}")
        print(f"\n{answer}\n")
        print("SOURCES:")
        for i, s in enumerate(sources, 1):
            print(f"  [{i}] {s['title']}")
            print(f"      {s['url']}")
        print()

    return {
        'answer': answer,
        'sources': sources,
        'context_used': context_text
    }


def interactive_mode(category=None):
    """Run an interactive question-answer session."""
    print("=" * 60)
    print("Mouldwire RAG Query Interface")
    print("=" * 60)
    print("Ask questions about the mould research archive.")
    print("Type 'quit' or 'exit' to stop.\n")

    client = get_llm_client()

    while True:
        try:
            question = input("Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not question:
            continue
        if question.lower() in ('quit', 'exit', 'q'):
            print("Goodbye.")
            break

        ask(question, category=category, client=client)


def main():
    parser = argparse.ArgumentParser(description='Mouldwire RAG Query')
    parser.add_argument('question', nargs='?', help='Question to ask')
    parser.add_argument('--category', '-c', choices=VALID_CATEGORIES,
                        help='Filter by category')
    parser.add_argument('--n', type=int, default=DEFAULT_N_RESULTS,
                        help='Number of context articles')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Enter interactive Q&A mode')
    parser.add_argument('--json', action='store_true',
                        help='Output as JSON')
    args = parser.parse_args()

    if args.interactive:
        interactive_mode(category=args.category)
        return

    if not args.question:
        print("Usage: python rag_query.py \"your question here\"")
        print("       python rag_query.py --interactive")
        return

    result = ask(args.question, category=args.category, n_results=args.n,
                 verbose=not args.json)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
