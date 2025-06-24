#!/usr/bin/env python3
"""
Test script to verify category integration in the LLM text processing pipeline
"""

import sys
import os
sys.path.insert(0, '.')

from app.routes.helpers import optimize_text_for_ai_analysis_with_categories, detect_category_from_url
from app.services.advanced_bengali_nlp import TrendingBengaliAnalyzer

def test_category_integration():
    """Test if category system is working in text optimization"""
    
    print("🧪 Testing Category Integration in LLM Pipeline")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = TrendingBengaliAnalyzer()
    
    # Create sample articles with metadata (similar to actual pipeline)
    sample_articles = [
        {
            'url': 'https://www.prothomalo.com/politics/something',
            'title': 'সরকারি নীতি নিয়ে নতুন আলোচনা',
            'content': 'রাজনৈতিক পরিস্থিতি নিয়ে আজ আলোচনা হয়েছে।',
            'source': 'prothom-alo'
        },
        {
            'url': 'https://www.prothomalo.com/sports/cricket',
            'title': 'ক্রিকেট ম্যাচের ফলাফল',
            'content': 'আজকের ক্রিকেট ম্যাচে দুর্দান্ত পারফরমেন্স।',
            'source': 'prothom-alo'
        },
        {
            'url': 'https://www.prothomalo.com/business/economy',
            'title': 'অর্থনৈতিক প্রবৃদ্ধির নতুন দিক',
            'content': 'দেশের অর্থনীতিতে ইতিবাচক পরিবর্তন দেখা যাচ্ছে।',
            'source': 'prothom-alo'
        },
        {
            'url': 'https://www.prothomalo.com/technology/latest',
            'title': 'নতুন প্রযুক্তির উদ্ভাবন',
            'content': 'প্রযুক্তি ক্ষেত্রে বাংলাদেশের নতুন অগ্রগতি।',
            'source': 'prothom-alo'
        }
    ]
    
    print(f"📊 Testing with {len(sample_articles)} sample articles")
    print()
    
    # Test individual category detection
    print("1️⃣ Testing Individual Category Detection:")
    for i, article in enumerate(sample_articles, 1):
        category = detect_category_from_url(article['url'], article.get('title', ''))
        print(f"   {i}. URL: {article['url']}")
        print(f"      Title: {article['title']}")
        print(f"      Detected Category: {category}")
        # Add category to article for next test
        article['category'] = category
        print()
    
    # Test category-aware text optimization
    print("2️⃣ Testing Category-Aware Text Optimization:")
    optimized_text = optimize_text_for_ai_analysis_with_categories(
        sample_articles, 
        analyzer, 
        max_chars=2000,
        max_articles=10,
        enable_categories=True
    )
    
    print(f"📄 Optimized Text Length: {len(optimized_text)} chars")
    print(f"📄 Category-optimized Text:")
    print("-" * 50)
    print(optimized_text)
    print("-" * 50)
    print()
    
    # Check if categories are present in the output
    categories_found = []
    expected_categories = ['রাজনীতি', 'খেলাধুলা', 'অর্থনীতি', 'প্রযুক্তি']
    
    for cat in expected_categories:
        if cat in optimized_text:
            categories_found.append(cat)
    
    print("3️⃣ Category Analysis Results:")
    print(f"   Expected Categories: {expected_categories}")
    print(f"   Found in Output: {categories_found}")
    print(f"   Success Rate: {len(categories_found)}/{len(expected_categories)} ({len(categories_found)/len(expected_categories)*100:.1f}%)")
    
    # Test if the format matches LLM expected input
    print()
    print("4️⃣ LLM Input Format Verification:")
    if " | " in optimized_text:
        sections = optimized_text.split(" | ")
        print(f"   ✅ Text properly formatted with {len(sections)} category sections")
        for i, section in enumerate(sections, 1):
            category_name = section.split(":")[0] if ":" in section else "Unknown"
            print(f"      Section {i}: {category_name}")
    else:
        print(f"   ❌ Text not properly formatted for categories")
    
    print()
    print("=" * 60)
    if len(categories_found) >= len(expected_categories) * 0.75:
        print("✅ CATEGORY INTEGRATION TEST: PASSED")
    else:
        print("❌ CATEGORY INTEGRATION TEST: FAILED")
    print("=" * 60)

if __name__ == "__main__":
    test_category_integration()
