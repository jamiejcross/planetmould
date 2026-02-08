#!/usr/bin/env python3
print("Script started")

import json
print("✓ json imported")

import os
print("✓ os imported")

# Check if input file exists
if os.path.exists('mould_news.json'):
    print("✓ mould_news.json found")
    with open('mould_news.json', 'r') as f:
        data = json.load(f)
    print(f"✓ Loaded {len(data)} articles")
else:
    print("❌ mould_news.json NOT FOUND")
    exit(1)

# Try creating output file
test_data = [{"test": "data"}]
with open('articles_enhanced.json', 'w') as f:
    json.dump(test_data, f)
print("✓ articles_enhanced.json created")

# Verify it exists
if os.path.exists('articles_enhanced.json'):
    print("✅ SUCCESS - File creation works!")
else:
    print("❌ FAILED - File not created")
