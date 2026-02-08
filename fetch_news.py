import feedparser
import json
import datetime
import re
import time

# CATEGORIES AND FEEDS
RSS_FEEDS = {
    "science": [
        "https://www.nature.com/srep.rss", "https://www.nature.com/ncomms.rss",
        "https://journals.plos.org/plosone/feed/atom", "https://www.mdpi.com/rss/journal/jof",
        "https://www.mdpi.com/rss/journal/microorganisms", "https://www.mdpi.com/rss/journal/molecules",
        "https://www.mdpi.com/rss/journal/biomolecules", "https://journals.asm.org/action/showFeed?feed=rss&jc=MBIO&type=etoc",
        "https://journals.asm.org/action/showFeed?feed=rss&jc=SPECTRUM&type=etoc", "https://www.frontiersin.org/journals/microbiology/rss",
        "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=acsodf", "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=jacsat",
        "https://rss.sciencedirect.com/publication/science/01418130", "https://www.mdpi.com/rss/journal/ijms"
    ],
    "media": [
        "https://www.sciencedaily.com/rss/plants_animals/fungi.xml",
        "https://phys.org/rss-feed/biology-news/microbiology/"
    ],
    "health": [
        "https://www.mdpi.com/rss/journal/toxins", "https://www.cdc.gov/media/rss/topic/fungal.xml",
        "https://www.mdpi.com/rss/journal/animals", "https://www.mdpi.com/rss/journal/plants",
        "https://www.mdpi.com/rss/journal/agronomy", "https://www.frontiersin.org/journals/plant-science/rss",
        "https://www.frontiersin.org/journals/veterinary-science/rss", "https://www.mdpi.com/rss/journal/foods",
        "https://rss.sciencedirect.com/publication/science/03088146", "https://rss.sciencedirect.com/publication/science/09639969",
        "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=jafcau", "https://www.mdpi.com/rss/journal/marinedrugs"
    ],
    "indoor": [
        "https://journals.asm.org/action/showFeed?feed=rss&jc=AEM&type=etoc", "https://www.ashrae.org/RssFeeds/news-feed.xml",
        "https://www.gov.uk/search/news-and-communications.atom?content_store_document_type=news_story&organisations[]=department-for-levelling-up-housing-and-communities",
        "https://www.mdpi.com/rss/journal/fermentation", "https://www.mdpi.com/rss/journal/catalysts",
        "https://www.mdpi.com/rss/journal/applsci", "https://pubs.acs.org/action/showFeed?type=etoc&feed=rss&jc=jnprdf",
        "https://rss.sciencedirect.com/publication/science/09608524", "https://rss.sciencedirect.com/publication/science/00489697",
        "https://rss.sciencedirect.com/publication/science/02697491", "https://rss.sciencedirect.com/publication/science/09608524",
        "https://rss.sciencedirect.com/publication/science/03043894", "https://rss.sciencedirect.com/publication/science/13858947",
        "https://rss.sciencedirect.com/publication/science/09619534"
    ],
    "clinical": [
        "https://journals.plos.org/plospathogens/feed/atom", "https://www.mdpi.com/rss/journal/antibiotics",
        "https://www.mdpi.com/rss/journal/pathogens", "https://www.mdpi.com/rss/journal/pharmaceuticals",
        "https://www.mdpi.com/rss/journal/diagnostics", "https://journals.asm.org/action/showFeed?feed=rss&jc=AAC&type=etoc",
        "https://journals.asm.org/action/showFeed?feed=rss&jc=JCM&type=etoc", "https://www.frontiersin.org/journals/cellular-and-infection-microbiology/rss",
        "https://www.frontiersin.org/journals/medicine/rss", "https://www.frontiersin.org/journals/immunology/rss",
        "https://www.frontiersin.org/journals/pharmacology/rss"
    ]
}

SUBJECTS = ['mould', 'mold', 'mycotoxin', 'aflatoxin', 'aspergillus', 'penicillium', 'stachybotrys', 'cladosporium', 'alternaria', 'fusarium', 'mucor', 'filamentous']
CONTEXTS = ['resistance', 'amr', 'famr', 'infection', 'clinical', 'indoor air', 'housing', 'home', 'building', 'hvac', 'ventilation', 'azole', 'pathogen', 'humidity', 'condensation', 'iaq', 'antifungal', 'mask', 'surgical', 'degradation', 'environmental', 'fabric', 'damp', 'bioaerosol', 'environment', 'bioremediation', 'detection', 'exposure', 'public health', 'study', 'analysis', 'climate', 'heat', 'metabolic', 'metabolise', 'metabolize']
BROAD_JOURNALS = ['Scientific Reports', 'Nature Communications', 'PLOS ONE', 'ACS Omega', 'JACS', 'Chemical Engineering Journal', 'Science of the Total Environment']

def clean_text(text):
    return re.sub('<[^<]+?>', '', text).strip()

def is_relevant(title, excerpt, source):
    text = (title + " " + excerpt).lower()
    if not any(s in text for s in SUBJECTS): return False
    if any(bj.lower() in source.lower() for bj in BROAD_JOURNALS):
        return any(c in text for c in CONTEXTS)
    return True

def run_fetcher():
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
                            "excerpt": clean_desc[:600],
                            "url": entry.link,
                            "pubDate": iso_date,
                            "category": category
                        })
            except: continue
    unique_output = {v['url']: v for v in output}.values()
    sorted_output = sorted(unique_output, key=lambda x: x['pubDate'], reverse=True)
    with open('mould_news.json', 'w', encoding='utf-8') as f:
        json.dump(list(sorted_output), f, indent=2)

if __name__ == "__main__":
    run_fetcher()
