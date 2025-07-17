#!/usr/bin/env python3
"""
Check the structure of all_newspapers_by_category.json to understand frequency issue
"""

import json
import os

def check_json_structure():
    json_file_path = "/home/bs01127/IMLI-Project/all_newspapers_by_category.json"
    
    if not os.path.exists(json_file_path):
        print("❌ JSON file not found!")
        return
    
    print("🔍 Checking JSON structure...")
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 JSON file loaded successfully")
        print(f"📂 Top-level keys: {list(data.keys())}")
        
        # Check structure for each category
        for category, articles in data.items():
            if isinstance(articles, list) and len(articles) > 0:
                print(f"\n📁 Category: {category}")
                print(f"   📄 Articles count: {len(articles)}")
                
                # Show structure of first article
                first_article = articles[0]
                print(f"   🔑 Article fields: {list(first_article.keys())}")
                
                # Show sample data
                for field in ['title', 'heading', 'content', 'description']:
                    if field in first_article:
                        value = first_article[field]
                        if value:
                            print(f"   📝 {field}: {str(value)[:50]}...")
                        else:
                            print(f"   ❌ {field}: Empty")
                    else:
                        print(f"   ❌ {field}: Not found")
            else:
                print(f"\n📁 Category: {category} - ❌ No articles or invalid format")
    
    except Exception as e:
        print(f"❌ Error reading JSON: {e}")

if __name__ == "__main__":
    check_json_structure()
