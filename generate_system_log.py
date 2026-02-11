#!/usr/bin/env python3
"""
Mouldwire System Log Generator

Generates a system_log.json file that records:
- Pipeline run statistics (articles fetched, enriched, enhanced)
- Inference engine changes (prompt revisions, model updates)
- System milestones and errors

The log is read by the frontend JS to render the System Log section dynamically.
"""

import json
import os
import re
from datetime import datetime, timezone


LOG_FILE = 'system_log.json'
NEWS_FILE = 'mould_news.json'
ENHANCED_FILE = 'articles_enhanced.json'
ENHANCE_SCRIPT = 'enhance_articles.py'


def load_log():
    """Load existing system log or initialise with seed entries."""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            pass

    # Seed log with historical entries (matches the hardcoded HTML)
    return {
        "entries": [
            {
                "date": "2026-02-01",
                "type": "milestone",
                "event": "Mouldwire v0.3 active: 50+ journals integrated."
            },
            {
                "date": "2026-02-07",
                "type": "calibration",
                "event": "Calibration: \"Patchy Anthropocene\" field guide logic implemented."
            },
            {
                "date": "2026-02-10",
                "type": "engine",
                "event": "Updated instruction set for Llama-3-8B-Instruct inference engine to maintain scientific register."
            }
        ],
        "run_history": []
    }


def count_articles_by_date(articles, target_date):
    """Count articles published on a specific date."""
    count = 0
    for article in articles:
        pub = article.get('pubDate', '')
        if pub and pub[:10] == target_date:
            count += 1
    return count


def count_enrichment_sources(articles):
    """Count articles by abstract enrichment source."""
    sources = {"semantic_scholar": 0, "openalex": 0, "none": 0}
    for article in articles:
        src = article.get('abstract_source', '')
        if src in sources:
            sources[src] += 1
        else:
            sources['none'] += 1
    return sources


def detect_engine_changes(log_entries):
    """Detect changes to the inference engine by hashing key prompt sections.
    Returns a list of change descriptions if the engine has been modified
    since the last recorded engine event."""

    if not os.path.exists(ENHANCE_SCRIPT):
        return []

    with open(ENHANCE_SCRIPT, 'r', encoding='utf-8') as f:
        source = f.read()

    changes = []

    # Detect model changes
    model_match = re.search(r'model_id\s*=\s*"([^"]+)"', source)
    current_model = model_match.group(1) if model_match else "unknown"

    # Check if model changed since last engine log
    last_engine = None
    for entry in reversed(log_entries):
        if entry.get('type') == 'engine':
            last_engine = entry
            break

    if last_engine:
        # Check if current model is mentioned in the last engine entry
        if current_model not in last_engine.get('event', ''):
            model_short = current_model.split('/')[-1]
            changes.append(f"Inference engine updated to {model_short}.")

    # Detect prompt structure changes
    sentence_match = re.search(r'Write (\d+[\s\w]*\d*) sentences', source)
    if sentence_match:
        sentence_spec = sentence_match.group(1)
        # Check if this is new
        if last_engine and sentence_spec not in last_engine.get('_meta', {}).get('sentence_spec', ''):
            changes.append(f"Summary structure updated to {sentence_spec} sentences.")

    # Detect JARGON_MAP presence (readability feature)
    has_jargon = 'JARGON_MAP' in source
    if has_jargon:
        if last_engine and not last_engine.get('_meta', {}).get('has_jargon', False):
            changes.append("Readability layer added: specialist jargon mapped to plain language.")

    # Detect ACRONYM_MAP size changes
    acronym_count = source.count("r'\\b")
    if last_engine:
        prev_count = last_engine.get('_meta', {}).get('acronym_count', 0)
        if acronym_count > prev_count + 5:
            changes.append(f"Acronym expansion dictionary updated ({acronym_count} patterns).")

    # Detect readability prompt section
    has_readability = 'READABILITY:' in source
    if has_readability:
        if last_engine and not last_engine.get('_meta', {}).get('has_readability', False):
            changes.append("Readability instructions embedded in inference prompt for non-specialist audiences.")

    return changes


def get_engine_meta():
    """Capture current engine metadata for future diff comparisons."""
    if not os.path.exists(ENHANCE_SCRIPT):
        return {}

    with open(ENHANCE_SCRIPT, 'r', encoding='utf-8') as f:
        source = f.read()

    meta = {}

    model_match = re.search(r'model_id\s*=\s*"([^"]+)"', source)
    meta['model'] = model_match.group(1) if model_match else "unknown"

    sentence_match = re.search(r'Write (\d+[\s\w]*\d*) sentences', source)
    meta['sentence_spec'] = sentence_match.group(1) if sentence_match else ""

    meta['has_jargon'] = 'JARGON_MAP' in source
    meta['has_readability'] = 'READABILITY:' in source
    meta['acronym_count'] = source.count("r'\\b")

    return meta


def generate_run_entry(news_articles, enhanced_articles):
    """Generate a run statistics entry for the current pipeline execution."""
    now = datetime.now(timezone.utc)
    today = now.strftime('%Y-%m-%d')

    # Count new articles today
    new_today = count_articles_by_date(news_articles, today)

    # Count enrichment sources
    enrichment = count_enrichment_sources(news_articles)

    # Count total enhanced
    total_enhanced = len([a for a in enhanced_articles if a.get('enhanced')])

    # Count new enhanced (enhanced_at matches today)
    new_enhanced = 0
    for article in enhanced_articles:
        enhanced_at = article.get('enhanced_at', '')
        if enhanced_at and enhanced_at[:10] == today:
            new_enhanced += 1

    return {
        "timestamp": now.isoformat(),
        "date": today,
        "total_articles": len(news_articles),
        "new_today": new_today,
        "total_enhanced": total_enhanced,
        "new_enhanced": new_enhanced,
        "enrichment_sources": enrichment
    }


def main():
    """Main log generation routine. Called after fetch_news.py and enhance_articles.py."""
    print("=" * 60)
    print("Mouldwire System Log Generator")
    print("=" * 60)

    log = load_log()
    now = datetime.now(timezone.utc)
    today = now.strftime('%Y-%m-%d')

    # Load article data
    news_articles = []
    enhanced_articles = []

    if os.path.exists(NEWS_FILE):
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            news_articles = json.load(f)

    if os.path.exists(ENHANCED_FILE):
        with open(ENHANCED_FILE, 'r', encoding='utf-8') as f:
            enhanced_articles = json.load(f)

    # 1. Generate run statistics
    run_entry = generate_run_entry(news_articles, enhanced_articles)
    log['run_history'].append(run_entry)

    # Keep last 100 run entries to prevent unbounded growth
    if len(log['run_history']) > 100:
        log['run_history'] = log['run_history'][-100:]

    print(f"  Archive: {run_entry['total_articles']} articles")
    print(f"  New today: {run_entry['new_today']}")
    print(f"  Enhanced: {run_entry['total_enhanced']} total, {run_entry['new_enhanced']} new")

    # 2. Detect and log inference engine changes
    engine_changes = detect_engine_changes(log['entries'])
    if engine_changes:
        engine_meta = get_engine_meta()
        for change in engine_changes:
            entry = {
                "date": today,
                "type": "engine",
                "event": change,
                "_meta": engine_meta
            }
            log['entries'].append(entry)
            print(f"  Engine change logged: {change}")

    # 3. Log new article milestone if significant
    total = run_entry['total_articles']
    milestones = [50, 100, 200, 500, 1000, 2000, 5000]
    logged_milestones = set()
    for entry in log['entries']:
        if entry.get('type') == 'milestone' and 'articles' in entry.get('event', '').lower():
            # Extract number from milestone
            nums = re.findall(r'(\d+)\s*articles', entry['event'])
            for n in nums:
                logged_milestones.add(int(n))

    for milestone in milestones:
        if total >= milestone and milestone not in logged_milestones:
            log['entries'].append({
                "date": today,
                "type": "milestone",
                "event": f"Archive reached {milestone} articles."
            })
            print(f"  Milestone logged: {milestone} articles")

    # 4. Generate daily summary entry (one per day)
    existing_daily = [e for e in log['entries'] if e.get('type') == 'daily' and e.get('date') == today]
    if not existing_daily:
        new_today = run_entry['new_today']
        if new_today > 0:
            log['entries'].append({
                "date": today,
                "type": "daily",
                "event": f"{new_today} new article{'s' if new_today != 1 else ''} collected today."
            })

    # Sort entries by date descending
    log['entries'].sort(key=lambda x: x.get('date', ''), reverse=True)

    # 5. Compute summary stats for the frontend
    log['summary'] = {
        "total_articles": len(news_articles),
        "total_enhanced": len([a for a in enhanced_articles if a.get('enhanced')]),
        "last_updated": now.isoformat(),
        "enrichment_sources": count_enrichment_sources(news_articles)
    }

    # Write log
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    print(f"\n✅ System log updated: {len(log['entries'])} entries, {len(log['run_history'])} run records.")


if __name__ == '__main__':
    main()
