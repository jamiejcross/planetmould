import feedparser
import json
import csv
import datetime
import re
import time
import os
import requests

# CATEGORIES AND FEEDS (Updated with Biotechnology, Food Science, and Vascular Review)
RSS_FEEDS = {
    "science": [
        "https://www.nature.com/srep.rss", 
        "https://www.nature.com/ncomms.rss",
        "https://journals.plos.org/plosone/feed/atom", 
        "https://www.mdpi.com/rss/journal/jof",
        "https://www.mdpi.com/rss/journal/microorganisms", 
        "https://www.mdpi.com/rss/journal/molecules",
        "https://onlinelibrary.wiley.com/action/showFeed?jc=10970010&type=etoc&feed=rss", # J. Sci Food Agric
        "https://www.mdpi.com/rss/journal/biomolecules", 
        "https://www.mdpi.com/rss/journal/ijms",
        "https://journals.asm.org/action/showFeed?feed=rss&jc=MBIO&type=etoc",
        "https://journals.asm.org/action/showFeed?feed=rss&jc=SPECTRUM&type=etoc", 
        "https://www.frontiersin.org/journals/microbiology/rss",
        "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=acsodf", 
        "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=jacsat",
        "https://rss.sciencedirect.com/publication/science/01418130"
    ],
    "media": [
        "https://www.sciencedaily.com/rss/plants_animals/fungi.xml",
        "https://phys.org/rss-feed/biology-news/microbiology/"
    ],
    "health": [
        "https://www.mdpi.com/rss/journal/toxins", 
        "https://www.cdc.gov/media/rss/topic/fungal.xml",
        "https://www.mdpi.com/rss/journal/animals", 
        "https://www.mdpi.com/rss/journal/plants",
        "https://www.mdpi.com/rss/journal/agronomy", 
        "https://www.frontiersin.org/journals/plant-science/rss",
        "https://www.frontiersin.org/journals/veterinary-science/rss", 
        "https://www.mdpi.com/rss/journal/foods",
        "https://rss.sciencedirect.com/publication/science/03088146", 
        "https://rss.sciencedirect.com/publication/science/09639969",
        "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=jafcau", 
        "https://www.mdpi.com/rss/journal/marinedrugs"
    ],
    "indoor": [
        "https://journals.asm.org/action/showFeed?feed=rss&jc=AEM&type=etoc", 
        "https://www.ashrae.org/RssFeeds/news-feed.xml",
        "https://www.gov.uk/search/news-and-communications.atom?content_store_document_type=news_story&organisations[]=department-for-levelling-up-housing-and-communities",
        "https://www.mdpi.com/rss/journal/fermentation", 
        "https://www.mdpi.com/rss/journal/catalysts",
        "https://www.mdpi.com/rss/journal/applsci", 
        "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=jnprdf",
        "https://rss.sciencedirect.com/publication/science/09608524", 
        "https://rss.sciencedirect.com/publication/science/00489697",
        "https://rss.sciencedirect.com/publication/science/02697491", 
        "https://rss.sciencedirect.com/publication/science/03043894", 
        "https://rss.sciencedirect.com/publication/science/13858947",
        "https://rss.sciencedirect.com/publication/science/09619534"
    ],
    "clinical": [
        "https://journals.plos.org/plospathogens/feed/atom", 
        "https://www.benthamdirect.com/content/journals/cpb/fasttrack?feed=rss", # Current Pharm. Biotech
        "https://verjournal.com/index.php/ver/gateway/plugin/WebFeedGatewayPlugin/rss2", # Vascular & Endo Review
        "https://www.mdpi.com/rss/journal/antibiotics",
        "https://www.mdpi.com/rss/journal/pathogens", 
        "https://www.mdpi.com/rss/journal/pharmaceuticals",
        "https://www.mdpi.com/rss/journal/diagnostics", 
        "https://journals.asm.org/action/showFeed?feed=rss&jc=AAC&type=etoc",
        "https://journals.asm.org/action/showFeed?feed=rss&jc=JCM&type=etoc", 
        "https://www.frontiersin.org/journals/cellular-and-infection-microbiology/rss",
        "https://www.frontiersin.org/journals/medicine/rss", 
        "https://www.frontiersin.org/journals/immunology/rss",
        "https://www.frontiersin.org/journals/pharmacology/rss"
    ]
}

SUBJECTS = ['mould', 'mold', 'mycotoxin', 'aflatoxin', 'aspergillus', 'penicillium', 'stachybotrys', 'cladosporium', 'alternaria', 'fusarium', 'mucor', 'filamentous']
CONTEXTS = ['resistance', 'amr', 'famr', 'infection', 'clinical', 'indoor air', 'housing', 'home', 'building', 'hvac', 'ventilation', 'azole', 'pathogen', 'humidity', 'condensation', 'iaq', 'antifungal', 'mask', 'surgical', 'degradation', 'environmental', 'fabric', 'damp', 'bioaerosol', 'environment', 'bioremediation', 'exposure', 'public health', 'study', 'analysis', 'climate', 'heat', 'metabolic', 'metabolise', 'metabolize', 'infrastructure', 'materiality', 'biopolitics', 'labor', 'urban', 'decay', 'toxicity', 'assemblage', 'sociality', 'precarity', 'policy', 'regulation', 'governance', 'justice', 'inequality', 'tenure']
BROAD_JOURNALS = ['Scientific Reports', 'Nature Communications', 'PLOS ONE', 'ACS Omega', 'JACS', 'Chemical Engineering Journal', 'Science of the Total Environment']

def clean_text(text):
    return re.sub('<[^<]+?>', '', text).strip()

THEORY_KEYWORDS = ['anthropology', 'sociology', 'ethnography', 'material culture', 'political economy']

def is_relevant(title, excerpt, source):
    text = (title + " " + excerpt).lower()
    
    # Priority 1: If it's a theory-heavy article, keep it regardless of source
    if any(t in text for t in THEORY_KEYWORDS): return True
    
    # Priority 2: Standard Mould/Subject check
    if not any(s in text for s in SUBJECTS): return False
    
    # Priority 3: Context check for broad journals
    if any(bj.lower() in source.lower() for bj in BROAD_JOURNALS):
        return any(c in text for c in CONTEXTS)
        
    return True

# --- ABSTRACT ENRICHMENT ---

def extract_doi(url):
    """Extract DOI from article URL. Works for Frontiers, ASM, Wiley, ACS, Nature, MDPI, PLOS."""
    match = re.search(r'(10\.\d{4,9}/[^\s?#&]+)', url)
    if match:
        return match.group(1).rstrip('.')
    return None

def extract_pii(url):
    """Extract PII from ScienceDirect URLs."""
    match = re.search(r'/pii/([A-Z0-9]+)', url)
    if match:
        return match.group(1)
    return None

def resolve_pii_to_doi(pii, elsevier_key):
    """Resolve a ScienceDirect PII to a DOI via the Elsevier API."""
    if not elsevier_key:
        return None
    try:
        url = f"https://api.elsevier.com/content/article/pii/{pii}"
        headers = {'X-ELS-APIKey': elsevier_key, 'Accept': 'application/json'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            doi = data.get('full-text-retrieval-response', {}).get('coredata', {}).get('prism:doi')
            if doi:
                return doi
    except Exception as e:
        print(f"  Elsevier API error for PII {pii}: {e}")
    return None

def resolve_title_to_doi(title):
    """Resolve an article title to a DOI via CrossRef free API. No key needed."""
    try:
        url = "https://api.crossref.org/works"
        params = {'query.bibliographic': title, 'rows': 1}
        headers = {'User-Agent': 'MouldwireBot/1.0 (mailto:news@planetmould.com)'}
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            items = resp.json().get('message', {}).get('items', [])
            if items:
                candidate = items[0]
                candidate_title = candidate.get('title', [''])[0].lower()
                # Verify the match is close enough (prevent false positives)
                if _titles_match(title.lower(), candidate_title):
                    doi = candidate.get('DOI', '')
                    # Skip supplementary material DOIs (e.g. .s001, .s002)
                    if doi and not re.search(r'\.s\d{3}$', doi):
                        return doi
    except Exception as e:
        print(f"  CrossRef error for title lookup: {e}")
    return None

def _titles_match(a, b):
    """Check if two titles are similar enough to be the same paper.
    Handles truncated titles (RSS feeds often cut titles short)."""
    def norm(t):
        return re.sub(r'[^a-z0-9 ]', '', t.lower()).strip()
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    # Check if one title is a prefix/subset of the other (handles truncation)
    if na in nb or nb in na:
        return True
    # Check word overlap relative to the shorter title
    words_a, words_b = set(na.split()), set(nb.split())
    if not words_a or not words_b:
        return False
    overlap = len(words_a & words_b) / min(len(words_a), len(words_b))
    return overlap > 0.75

def fetch_abstract_semantic_scholar(doi, api_key=None):
    """Fetch abstract from Semantic Scholar. Authenticated calls get higher rate limits."""
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=abstract"
        headers = {'x-api-key': api_key} if api_key else {}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            abstract = data.get('abstract')
            if abstract and len(abstract) > 50:
                return abstract
    except Exception as e:
        print(f"  Semantic Scholar error for {doi}: {e}")
    return None

def reconstruct_abstract(inverted_index):
    """Reconstruct plaintext from OpenAlex inverted index format."""
    if not inverted_index:
        return None
    words = []
    for word, positions in inverted_index.items():
        for pos in positions:
            words.append((pos, word))
    words.sort(key=lambda x: x[0])
    return ' '.join(w for _, w in words)

def fetch_abstract_openalex(doi, api_key):
    """Fetch abstract from OpenAlex (requires free API key)."""
    if not api_key:
        return None
    try:
        url = f"https://api.openalex.org/works/doi:{doi}?api_key={api_key}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            inverted = data.get('abstract_inverted_index')
            if inverted:
                return reconstruct_abstract(inverted)
    except Exception as e:
        print(f"  OpenAlex error for {doi}: {e}")
    return None

def scrape_abstract_from_page(url):
    """Last-resort fallback: scrape the abstract directly from the paper's web page.
    Works for open-access publishers (MDPI, Frontiers, PLOS, ASM, Wiley, Nature, ACS, ScienceDirect)."""
    try:
        headers = {
            'User-Agent': 'MouldwireBot/1.0 (academic research aggregator; +https://news.planetmould.com)',
            'Accept': 'text/html'
        }
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            return None

        html = resp.text

        # Strategy 1: Look for <meta name="description"> or <meta property="og:description">
        # These often contain the abstract on publisher pages
        meta_patterns = [
            r'<meta\s+name=["\'](?:dc\.description|DC\.Description|description)["\'].*?content=["\'](.*?)["\']',
            r'<meta\s+property=["\']og:description["\'].*?content=["\'](.*?)["\']',
            r'<meta\s+content=["\'](.*?)["\']\s+name=["\']description["\']',
            r'<meta\s+content=["\'](.*?)["\']\s+property=["\']og:description["\']',
        ]
        for pattern in meta_patterns:
            match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if match:
                text = re.sub('<[^<]+?>', '', match.group(1)).strip()
                # Only accept if it's substantial (not just a journal tagline)
                if len(text) > 150:
                    return text[:2000]

        # Strategy 2: Look for common abstract containers in the HTML
        abstract_patterns = [
            # ScienceDirect (must be before generic abstract patterns)
            r'<div[^>]*class="[^"]*abstract author"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*abstracts"[^>]*>(.*?)</div>\s*</div>',
            # MDPI, Frontiers
            r'<div[^>]*class="[^"]*abstract[^"]*"[^>]*>(.*?)</div>',
            # PLOS
            r'<div[^>]*id="[^"]*abstract[^"]*"[^>]*>(.*?)</div>',
            # Nature
            r'<div[^>]*id="Abs1-content"[^>]*>(.*?)</div>',
            # Wiley
            r'<section[^>]*class="[^"]*abstract[^"]*"[^>]*>(.*?)</section>',
            # ASM journals
            r'<div[^>]*class="[^"]*abstractSection[^"]*"[^>]*>(.*?)</div>',
            # Generic <abstract> tag (some XML feeds)
            r'<abstract[^>]*>(.*?)</abstract>',
        ]
        for pattern in abstract_patterns:
            match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if match:
                text = re.sub('<[^<]+?>', '', match.group(1)).strip()
                # Remove "Abstract" heading if present
                text = re.sub(r'^(?:Abstract|ABSTRACT|Summary|SUMMARY)[:\s]*', '', text).strip()
                if len(text) > 150:
                    return text[:2000]

    except Exception as e:
        print(f"  Scrape error for {url[:60]}: {e}")
    return None


def is_thin_excerpt(excerpt):
    """Check if an excerpt is metadata-only and lacks real abstract content."""
    if not excerpt or len(excerpt) < 100:
        return True
    # Common metadata-only patterns from ScienceDirect, Wiley, ASM
    metadata_indicators = [
        r'^Publication date:',
        r'^Source:.*Volume \d+',
        r'^Author\(s\):',
        r'^Journal of .*, (Volume|Ahead)',
        r', Volume \d+, Issue \d+, Page',
    ]
    for pattern in metadata_indicators:
        if re.search(pattern, excerpt, re.IGNORECASE):
            return True
    return False

def enrich_abstracts(articles):
    """Enrich articles that have thin excerpts with real abstracts from academic APIs."""
    ss_key = os.getenv('SS2_KEY')
    openalex_key = os.getenv('OPENALEX_KEY')
    elsevier_key = os.getenv('ELSEVIER_KEY')
    enriched_count = 0
    skipped_count = 0

    for article in articles:
        # Skip articles that already have good excerpts
        if not is_thin_excerpt(article.get('excerpt', '')):
            continue
        # Retry: if excerpt is still thin despite a previous enrichment attempt,
        # clear the old source flag so we try again (APIs may have caught up)
        if article.get('abstract_source'):
            print(f"  ↻ Retrying (still thin): {article.get('title', '')[:50]}...")
            del article['abstract_source']

        url = article.get('url', '')
        title = article.get('title', '')
        doi = extract_doi(url)

        # For ScienceDirect, resolve PII to DOI via Elsevier API
        if not doi and 'sciencedirect.com' in url:
            pii = extract_pii(url)
            if pii:
                doi = resolve_pii_to_doi(pii, elsevier_key)
                if doi:
                    print(f"  Resolved PII → DOI (Elsevier): {doi}")

        # Fallback: resolve title to DOI via CrossRef (free, no key needed)
        if not doi and title:
            doi = resolve_title_to_doi(title)
            if doi:
                print(f"  Resolved title → DOI (CrossRef): {doi}")

        if not doi:
            # No DOI — try scraping the page directly as last resort
            abstract = scrape_abstract_from_page(url)
            if abstract:
                article['excerpt'] = abstract[:2000]
                article['abstract_source'] = 'web_scrape'
                enriched_count += 1
                print(f"  ✅ Enriched (scraped, no DOI): {title[:50]}...")
                time.sleep(0.3)
            else:
                print(f"  ⚠ No DOI or abstract found: {title[:50]}...")
            continue

        # Try Semantic Scholar first, then OpenAlex, then scrape the page
        abstract = fetch_abstract_semantic_scholar(doi, ss_key)
        source = 'semantic_scholar'
        if not abstract:
            abstract = fetch_abstract_openalex(doi, openalex_key)
            source = 'openalex'
        if not abstract:
            abstract = scrape_abstract_from_page(url)
            source = 'web_scrape'

        if abstract:
            article['excerpt'] = abstract[:2000]
            article['abstract_source'] = source
            enriched_count += 1
            print(f"  ✅ Enriched: {title[:50]}... ({source})")
        else:
            print(f"  ⚠ DOI found ({doi}) but no abstract from any source: {title[:50]}...")

        # Polite delay between API calls / page fetches
        time.sleep(0.3)

    print(f"Abstract enrichment: {enriched_count} enriched, {skipped_count} already enriched, {len(articles) - enriched_count - skipped_count} unchanged.")

    # Export manifest of articles still missing abstracts (for manual PDF enrichment)
    missing = []
    for article in articles:
        if is_thin_excerpt(article.get('excerpt', '')):
            doi = extract_doi(article.get('url', ''))
            if not doi:
                doi = article.get('doi', '')  # May have been resolved earlier
            missing.append({
                'doi': doi or '',
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'category': article.get('category', ''),
                'pubDate': article.get('pubDate', ''),
            })
    if missing:
        with open('missing_abstracts.json', 'w', encoding='utf-8') as f:
            json.dump(missing, f, indent=2, ensure_ascii=False)
        with open('missing_abstracts.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['doi', 'title', 'url', 'category', 'pubDate'])
            writer.writeheader()
            writer.writerows(missing)
        print(f"\n📋 Exported {len(missing)} articles still missing abstracts → missing_abstracts.json / .csv")
    else:
        print("\n✅ All articles have abstracts — no missing manifest needed.")
        # Clean up old manifests if they exist
        for f in ('missing_abstracts.json', 'missing_abstracts.csv'):
            if os.path.exists(f):
                os.remove(f)


def run_fetcher():
    # Load existing articles for rolling archive
    existing_articles = []
    if os.path.exists('mould_news.json'):
        try:
            with open('mould_news.json', 'r', encoding='utf-8') as f:
                existing_articles = json.load(f)
            print(f"Loaded {len(existing_articles)} existing articles from archive.")
        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: Could not load existing archive: {e}")
            existing_articles = []

    output = []
    for category, urls in RSS_FEEDS.items():
        for url in urls:
            try:
                feed = feedparser.parse(url)
                source_name = feed.feed.get('title', 'Unknown Source')
                for entry in feed.entries:
                    desc = entry.get('summary', entry.get('description', ''))
                    clean_desc = clean_text(desc)
                    if is_relevant(entry.title, clean_desc, source_name):
                        try:
                            dt = entry.get('published_parsed', entry.get('updated_parsed', time.gmtime()))
                            iso_date = time.strftime('%Y-%m-%dT%H:%M:%SZ', dt)
                        except:
                            iso_date = datetime.datetime.now().isoformat()
                        output.append({
                            "title": clean_text(entry.title),
                            "source": source_name,
                            "excerpt": clean_desc[:1200],
                            "url": entry.link,
                            "pubDate": iso_date,
                            "category": category
                        })
            except: continue
    # Merge: existing articles first, new articles overwrite (fresher metadata)
    merged = {article['url']: article for article in existing_articles}
    for article in output:
        merged[article['url']] = article
    sorted_output = list(sorted(merged.values(), key=lambda x: x['pubDate'], reverse=True))
    print(f"Archive now contains {len(sorted_output)} total articles ({len(sorted_output) - len(existing_articles)} new).")

    # Enrich thin excerpts with real abstracts from academic APIs
    print("\n--- Abstract Enrichment ---")
    enrich_abstracts(sorted_output)

    with open('mould_news.json', 'w', encoding='utf-8') as f:
        json.dump(sorted_output, f, indent=2)

if __name__ == "__main__":
    run_fetcher()
