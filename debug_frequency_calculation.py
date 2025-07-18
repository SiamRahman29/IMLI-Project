#!/usr/bin/env python3
"""
Debug script to test frequency calculation directly
"""

import sys
import os
sys.path.append('/home/bs01127/IMLI-Project')

from app.services.filtered_newspaper_service import FilteredNewspaperScraper
from app.services.category_llm_analyzer import calculate_phrase_frequency_in_articles

# Target categories  
TARGET_CATEGORIES = [
    'জাতীয়',
    'আন্তর্জাতিক', 
    'অর্থনীতি',
    'রাজনীতি',
    'ক্ষুদ্র নৃগোষ্ঠী'
]

def debug_frequency_calculation():
    """Debug the frequency calculation step"""
    
    print("🔍 DEBUGGING FREQUENCY CALCULATION")
    print("="*50)
    
    # 1. Test scraping first
    print("\n1️⃣ Testing live scraping...")
    scraper = FilteredNewspaperScraper(TARGET_CATEGORIES)
    results = scraper.scrape_all_newspapers()
    
    print(f"📊 Total articles scraped: {results['scraping_info']['total_articles']}")
    print(f"📂 Category breakdown:")
    for category in TARGET_CATEGORIES:
        articles = results.get('category_wise_articles', {}).get(category, [])
        print(f"   {category}: {len(articles)} articles")
        
        # Show sample article structure for debugging
        if articles and category == 'ক্ষুদ্র নৃগোষ্ঠী':
            print(f"   📝 Sample article from '{category}':")
            sample = articles[0]
            for key, value in sample.items():
                if key in ['title', 'heading', 'description']:
                    print(f"      {key}: {str(value)[:100]}...")
    
    # 2. Test frequency calculation with a known phrase
    print("\n2️⃣ Testing frequency calculation...")
    
    # Test with 'ক্ষুদ্র নৃগোষ্ঠী' category
    category = 'ক্ষুদ্র নৃগোষ্ঠী'
    category_articles = results.get('category_wise_articles', {}).get(category, [])
    
    if category_articles:
        print(f"🔍 Testing frequency calculation for category '{category}' with {len(category_articles)} articles")
        
        # Test with common phrases that should appear
        test_phrases = [
            'ক্ষুদ্র নৃগোষ্ঠী',
            'আদিবাসী',
            'পার্বত্য',
            'চট্টগ্রাম'
        ]
        
        for phrase in test_phrases:
            print(f"\n🧮 Testing phrase: '{phrase}'")
            freq_stats = calculate_phrase_frequency_in_articles(phrase, category_articles)
            print(f"   Result: {freq_stats}")
            
            # Manual verification - count manually
            manual_count = 0
            for article in category_articles:
                article_text = ""
                for field in ['title', 'heading']:
                    if article.get(field):
                        article_text += " " + str(article[field])
                article_text = article_text.lower()
                
                if phrase.lower() in article_text:
                    manual_count += 1
            
            print(f"   Manual count: {manual_count}")
            print(f"   Function result: {freq_stats.get('frequency', 0)}")
            print(f"   Match: {'✅' if manual_count == freq_stats.get('frequency', 0) else '❌'}")
    else:
        print(f"❌ No articles found for category '{category}'")
    
    print("\n✅ Debug complete!")

if __name__ == "__main__":
    debug_frequency_calculation()
