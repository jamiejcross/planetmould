#!/usr/bin/env python3
"""
Mouldwire PDF Enrichment — Google Drive → Full Paper → Claude → Enhanced Article

Reads PDFs from a Google Drive folder, sends full paper text to Claude,
and produces both an excerpt and Patchy Anthropocene summary in one pass.
Patches mould_news.json and articles_enhanced.json directly.

Requires:
  - ANTHROPIC_API_KEY env var
  - GDRIVE_CREDENTIALS env var (service account JSON key, base64-encoded)
  - GDRIVE_PDF_FOLDER_ID env var (Google Drive folder ID)
"""

import json
import os
import re
import io
import sys
import base64
import tempfile
from datetime import datetime

import anthropic
import PyPDF2

# Google Drive imports
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Reuse post-processing from enhance_articles
from enhance_articles import formalize_voice

from rag_config import (
    NEWS_FILE, ENHANCED_FILE,
    GDRIVE_PDF_FOLDER_ID, MISSING_ABSTRACTS_JSON,
)
from fetch_news import _titles_match


# ---------------------------------------------------------------------------
# Google Drive helpers
# ---------------------------------------------------------------------------

def get_drive_service():
    """Authenticate with Google Drive using service account credentials."""
    creds_b64 = os.getenv('GDRIVE_CREDENTIALS', '')
    if not creds_b64:
        print("❌ GDRIVE_CREDENTIALS not set. Skipping PDF enrichment.")
        return None
    try:
        creds_json = base64.b64decode(creds_b64)
        creds_info = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        print(f"❌ Google Drive auth failed: {e}")
        return None


def list_pdfs(service, folder_id):
    """List all PDF files in a Google Drive folder."""
    try:
        query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(
            q=query,
            fields="files(id, name, createdTime)",
            orderBy="createdTime desc"
        ).execute()
        return results.get('files', [])
    except Exception as e:
        print(f"  ❌ Error listing Drive folder: {e}")
        return []


def download_pdf(service, file_id):
    """Download a PDF from Google Drive, return bytes."""
    try:
        request = service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"  ❌ Error downloading file {file_id}: {e}")
        return None


def move_to_processed(service, file_id, folder_id):
    """Move a processed PDF into a 'processed' subfolder in Google Drive."""
    try:
        # Find or create 'processed' subfolder
        query = (f"'{folder_id}' in parents and name='processed' "
                 f"and mimeType='application/vnd.google-apps.folder' and trashed=false")
        results = service.files().list(q=query, fields="files(id)").execute()
        subfolders = results.get('files', [])

        if subfolders:
            processed_id = subfolders[0]['id']
        else:
            metadata = {
                'name': 'processed',
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [folder_id]
            }
            folder = service.files().create(body=metadata, fields='id').execute()
            processed_id = folder['id']

        # Move file: remove from current parent, add to processed
        service.files().update(
            fileId=file_id,
            addParents=processed_id,
            removeParents=folder_id,
            fields='id, parents'
        ).execute()
    except Exception as e:
        print(f"  ⚠ Could not move file to processed/: {e}")


# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_buffer):
    """Extract full text from a PDF file buffer."""
    try:
        reader = PyPDF2.PdfReader(pdf_buffer)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return '\n\n'.join(pages)
    except Exception as e:
        print(f"  ❌ PDF extraction error: {e}")
        return None


# ---------------------------------------------------------------------------
# Matching PDFs to articles
# ---------------------------------------------------------------------------

def extract_doi_from_filename(filename):
    """Try to extract a DOI from a PDF filename.
    Expected format: 10.1016_j.jhazmat.2026.141323.pdf (slashes → underscores)"""
    name = os.path.splitext(filename)[0]
    # Replace underscores back to slashes for DOI matching
    candidate = name.replace('_', '/')
    if re.match(r'^10\.\d{4,9}/', candidate):
        return candidate
    return None


def match_pdf_to_article(filename, pdf_text, missing_articles):
    """Match a PDF to an article from the missing abstracts manifest.
    Returns the matched article dict, or None."""
    # Strategy 1: DOI from filename
    doi = extract_doi_from_filename(filename)
    if doi:
        for article in missing_articles:
            if article.get('doi', '').lower() == doi.lower():
                return article

    # Strategy 2: Fuzzy title match using first 500 chars of PDF text
    # (the title is usually in the first page)
    pdf_header = pdf_text[:2000].lower() if pdf_text else ''
    for article in missing_articles:
        title = article.get('title', '')
        if title and _titles_match(title.lower(), pdf_header):
            return article

    # Strategy 3: Match by title words in filename
    name_clean = re.sub(r'[_\-.]', ' ', os.path.splitext(filename)[0]).lower()
    for article in missing_articles:
        title = article.get('title', '')
        if title and _titles_match(title.lower(), name_clean):
            return article

    return None


# ---------------------------------------------------------------------------
# Claude: full paper → excerpt + summary
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a detached field researcher documenting human-nonhuman interactions in the Anthropocene.\n\n"
    "You have been given the FULL TEXT of an academic paper. Your task is to produce TWO outputs, "
    "clearly separated by the marker ---SUMMARY---\n\n"
    "OUTPUT 1 — ABSTRACT EXCERPT (before the marker):\n"
    "Write a concise, factual abstract of the paper in 3-5 sentences (max 300 words). "
    "Report the key findings, methods, organisms, and materials. "
    "This will serve as the article's excerpt for a news aggregator.\n\n"
    "---SUMMARY---\n\n"
    "OUTPUT 2 — PATCHY ANTHROPOCENE ANALYSIS (after the marker):\n"
    "Write 5 to 7 sentences.\n"
    "- The first sentences accurately summarise the source findings. Report only what the source text contains. "
    "Use specific data, methods, organisms, and materials named in the source.\n"
    "- The final 1-2 sentences frame the findings through the Patchy Anthropocene lens: "
    "The Patchy Anthropocene lens brings 'located relations between humans and nonhumans into focus within "
    "the broader ongoing material transformations and ruptures brought on by colonialism, imperialism, and capitalism' "
    "(Deger, Zhou, Tsing & Keleman Saxena). The same species of mould flagged as planetary pathogens can also be "
    "vehicles for accumulation; the same species that operate as signs of austerity or racialized exclusion can also "
    "be potential industrial saviours. The capacity of moulds to metabolize diverse materials — from food, walls and "
    "minerals to livers and lungs — and to rapidly adapt to external stresses makes them both a threat and a resource. "
    "Draw out the tension, duality, or material entanglement implied by the research. "
    "Do NOT reproduce the Patchy Anthropocene description verbatim. "
    "Apply the lens in your own words, specific to the findings of this paper.\n\n"
    "TONE: Clinical, detached, observational. No enthusiasm, no hedging. "
    "Write as if documenting a field site, not reviewing a paper.\n\n"
    "READABILITY: Write for an educated general audience, not specialists. "
    "Replace specialist jargon with plain language equivalents.\n\n"
    "STRICT CONSTRAINTS:\n"
    "1. NO HALLUCINATION: Do not invent findings not present in the paper.\n"
    "2. NO ACRONYMS OR ABBREVIATIONS: Write every term in full.\n"
    "3. DIRECT REFERENCE: Refer to the source as 'this paper' or 'this study'.\n"
    "4. NO first person. NO title repetition. NO 'Abstract' or 'Summary' headings.\n"
    "5. MATERIAL SPECIFICITY: Name the specific material, organism, or site."
)


def enhance_from_full_paper(client, title, full_text, model_id="claude-haiku-4-5-20251001"):
    """Send full paper text to Claude, get back excerpt + summary."""
    # Truncate to ~80k chars to stay within context limits
    text = full_text[:80000]

    user_message = f"Analyze this full research paper.\n\nTitle: {title}\n\nFull text:\n{text}"

    try:
        response = client.messages.create(
            model=model_id,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=1200,
            temperature=0.5
        )
        raw_output = response.content[0].text.strip()

        # Split on the marker
        if '---SUMMARY---' in raw_output:
            parts = raw_output.split('---SUMMARY---', 1)
            excerpt = parts[0].strip()
            summary = parts[1].strip()
        else:
            # Fallback: use first paragraph as excerpt, rest as summary
            paragraphs = raw_output.split('\n\n')
            excerpt = paragraphs[0].strip() if paragraphs else raw_output[:500]
            summary = '\n\n'.join(paragraphs[1:]).strip() if len(paragraphs) > 1 else raw_output

        # Post-process the summary through the same voice pipeline
        summary = formalize_voice(summary)

        return excerpt, summary

    except Exception as e:
        print(f"  ❌ Claude API error: {e}")
        return None, None


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Mouldwire PDF Enrichment (Google Drive → Claude)")
    print("=" * 60)

    # Check prerequisites
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set. Exiting.")
        return

    folder_id = GDRIVE_PDF_FOLDER_ID or os.getenv('GDRIVE_PDF_FOLDER_ID', '')
    if not folder_id:
        print("⚠ GDRIVE_PDF_FOLDER_ID not set. Skipping PDF enrichment.")
        return

    # Connect to Google Drive
    service = get_drive_service()
    if not service:
        return

    # Load missing abstracts manifest
    if not os.path.exists(MISSING_ABSTRACTS_JSON):
        print("⚠ No missing_abstracts.json found. Run fetch_news.py first.")
        return

    with open(MISSING_ABSTRACTS_JSON, 'r', encoding='utf-8') as f:
        missing_articles = json.load(f)
    print(f"  Loaded {len(missing_articles)} articles missing abstracts.")

    # List PDFs in Drive folder
    pdfs = list_pdfs(service, folder_id)
    if not pdfs:
        print("  No PDFs found in Google Drive folder. Nothing to do.")
        return
    print(f"  Found {len(pdfs)} PDFs in Google Drive folder.")

    # Load existing data
    articles_data = []
    if os.path.exists(NEWS_FILE):
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            articles_data = json.load(f)
    articles_by_url = {a['url']: a for a in articles_data}

    enhanced_data = {}
    if os.path.exists(ENHANCED_FILE):
        try:
            with open(ENHANCED_FILE, 'r', encoding='utf-8') as f:
                enhanced_list = json.load(f)
                enhanced_data = {a['url']: a for a in enhanced_list}
        except (json.JSONDecodeError, Exception):
            enhanced_data = {}

    client = anthropic.Anthropic(api_key=api_key)
    enriched_count = 0

    for pdf_file in pdfs:
        filename = pdf_file['name']
        file_id = pdf_file['id']
        print(f"\n  Processing: {filename}")

        # Download PDF
        pdf_buffer = download_pdf(service, file_id)
        if not pdf_buffer:
            continue

        # Extract text
        full_text = extract_text_from_pdf(pdf_buffer)
        if not full_text or len(full_text) < 200:
            print(f"    ⚠ Could not extract meaningful text from {filename}")
            continue
        print(f"    Extracted {len(full_text)} chars from PDF")

        # Match to a missing article
        matched = match_pdf_to_article(filename, full_text, missing_articles)
        if not matched:
            print(f"    ⚠ Could not match to any article in missing_abstracts.json")
            continue
        print(f"    ✅ Matched: {matched['title'][:60]}...")

        # Send full paper to Claude
        title = matched['title']
        excerpt, summary = enhance_from_full_paper(client, title, full_text)
        if not excerpt or not summary:
            print(f"    ⚠ Claude enhancement failed for {filename}")
            continue

        print(f"    ✅ Enhanced: excerpt={len(excerpt)} chars, summary={len(summary)} chars")

        url = matched['url']

        # Patch mould_news.json
        if url in articles_by_url:
            articles_by_url[url]['excerpt'] = excerpt[:2000]
            articles_by_url[url]['abstract_source'] = 'manual_pdf'

        # Patch articles_enhanced.json
        enhanced_entry = articles_by_url.get(url, matched).copy()
        enhanced_entry.update({
            'excerpt': excerpt[:2000],
            'abstract_source': 'manual_pdf',
            'summary': summary,
            'enhanced': True,
            'enhanced_at': datetime.utcnow().isoformat(),
        })
        enhanced_data[url] = enhanced_entry

        enriched_count += 1

        # Move processed PDF to 'processed/' subfolder
        move_to_processed(service, file_id, folder_id)
        print(f"    📁 Moved to processed/")

    # Save updated data
    if enriched_count > 0:
        # Save mould_news.json
        updated_articles = sorted(articles_by_url.values(),
                                  key=lambda x: x.get('pubDate', ''), reverse=True)
        with open(NEWS_FILE, 'w', encoding='utf-8') as f:
            json.dump(updated_articles, f, indent=2, ensure_ascii=False)

        # Save articles_enhanced.json
        all_enhanced = sorted(enhanced_data.values(),
                              key=lambda x: x.get('pubDate', ''), reverse=True)
        with open(ENHANCED_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_enhanced, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"✅ PDF enrichment complete: {enriched_count}/{len(pdfs)} articles enriched from full papers.")


if __name__ == '__main__':
    main()
