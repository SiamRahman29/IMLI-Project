#!/usr/bin/env python3
"""
Enhanced Category Detection System Test
Author: AI Assistant
Date: 2025-06-24

Test the integrated URL pattern-based category detection system
"""

import json
import sys
import os
from datetime import date
from collections import defaultdict

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.routes.helpers import detect_category_from_url
from app.services.category_service import CategoryTrendingService
from app.db.database import get_db


def test_enhanced_category_detection():
    """Test the enhanced category detection function"""
    
    print("🧪 Testing Enhanced Category Detection System")
    print("=" * 60)
    
    # Test URLs with known categories
    test_cases = [
        # National/Bangladesh
        {
            'url': 'https://www.prothomalo.com/bangladesh/district/abc123',
            'title': 'ঢাকায় নতুন সড়ক নির্মাণ শুরু',
            'content': 'বাংলাদেশের রাজধানী ঢাকায় একটি নতুন সড়ক নির্মাণের কাজ শুরু হয়েছে।',
            'expected': 'জাতীয়'
        },
        
        # International
        {
            'url': 'https://www.prothomalo.com/world/asia/def456',
            'title': 'ভারতে নতুন সরকার গঠন',
            'content': 'আন্তর্জাতিক রাজনীতিতে ভারতের নতুন সরকার গঠনের ঘটনা।',
            'expected': 'আন্তর্জাতিক'
        },
        
        # Politics
        {
            'url': 'https://example.com/politics/news123',
            'title': 'নির্বাচনী প্রচারণা শুরু',
            'content': 'আসন্ন নির্বাচনে রাজনৈতিক দলগুলোর প্রচারণা শুরু হয়েছে।',
            'expected': 'রাজনীতি'
        },
        
        # Sports
        {
            'url': 'https://example.com/sports/cricket/match789',
            'title': 'বাংলাদেশ ক্রিকেট দলের বিজয়',
            'content': 'টেস্ট ম্যাচে বাংলাদেশ ক্রিকেট দল ভারতকে হারিয়েছে।',
            'expected': 'খেলাধুলা'
        },
        
        # Technology
        {
            'url': 'https://example.com/tech/ai-news',
            'title': 'কৃত্রিম বুদ্ধিমত্তার নতুন আবিষ্কার',
            'content': 'প্রযুক্তি জগতে আর্টিফিশিয়াল ইন্টেলিজেন্সের নতুন উন্নতি।',
            'expected': 'প্রযুক্তি'
        },
        
        # Entertainment
        {
            'url': 'https://example.com/entertainment/bollywood',
            'title': 'নতুন বলিউড সিনেমা',
            'content': 'বিনোদন জগতে নতুন একটি সিনেমা মুক্তি পেয়েছে।',
            'expected': 'বিনোদন'
        },
        
        # Uncategorized URL (should create subcategory)
        {
            'url': 'https://www.prothomalo.com/abcdefghijklmn',
            'title': 'অজানা বিষয়ের সংবাদ',
            'content': 'এটি একটি সাধারণ সংবাদ যার কোনো নির্দিষ্ট বিভাগ নেই।',
            'expected': 'প্রথম আলো নিবন্ধ'  # Source-specific subcategory
        }
    ]
    
    results = {
        'correct': 0,
        'total': len(test_cases),
        'details': []
    }
    
    print("\n📋 Test Results:")
    print("-" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        detected_category = detect_category_from_url(
            test_case['url'],
            test_case['title'],
            test_case['content']
        )
        
        is_correct = detected_category == test_case['expected']
        if is_correct:
            results['correct'] += 1
        
        status = "✅" if is_correct else "❌"
        
        print(f"{status} Test {i}: {test_case['title'][:30]}...")
        print(f"   URL: {test_case['url']}")
        print(f"   Expected: {test_case['expected']}")
        print(f"   Detected: {detected_category}")
        print()
        
        results['details'].append({
            'test_number': i,
            'title': test_case['title'],
            'expected': test_case['expected'],
            'detected': detected_category,
            'correct': is_correct
        })
    
    accuracy = (results['correct'] / results['total']) * 100
    print(f"📊 Overall Accuracy: {accuracy:.1f}% ({results['correct']}/{results['total']})")
    
    return results


def test_with_real_data():
    """Test with real scraped newspaper data"""
    
    print("\n🗞️ Testing with Real Newspaper Data")
    print("=" * 60)
    
    # Load real data
    data_file = '/home/bs01127/IMLI-Project/scraped_urls_from_active_newspapers_20250624_015711.json'
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            real_data = json.load(f)
        
        print(f"📄 Loaded {len(real_data)} real URLs from newspapers")
        
        # Test a sample of URLs
        sample_size = min(50, len(real_data))
        sample_data = real_data[:sample_size]
        
        category_counts = defaultdict(int)
        
        print(f"\n🔍 Analyzing {sample_size} sample URLs...")
        
        for i, url_data in enumerate(sample_data):
            url = url_data.get('url', '')
            title = url_data.get('title', '')
            content = url_data.get('content', '') or url_data.get('description', '')
            
            category = detect_category_from_url(url, title, content)
            category_counts[category] += 1
            
            if i < 10:  # Show first 10 results
                print(f"  {i+1}. {category}: {title[:50]}...")
        
        print(f"\n📊 Category Distribution (Sample of {sample_size}):")
        print("-" * 40)
        
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        
        for category, count in sorted_categories:
            percentage = (count / sample_size) * 100
            print(f"  {category}: {count} ({percentage:.1f}%)")
        
        return category_counts
        
    except FileNotFoundError:
        print(f"❌ Real data file not found: {data_file}")
        return {}
    except Exception as e:
        print(f"❌ Error loading real data: {e}")
        return {}


def test_category_service():
    """Test the CategoryTrendingService"""
    
    print("\n🔧 Testing Category Service")
    print("=" * 60)
    
    try:
        # Get database session
        db = next(get_db())
        service = CategoryTrendingService(db)
        
        # Test data
        test_phrases = {
            'রাজনীতি': [
                {'phrase': 'নির্বাচন কমিশন', 'score': 95.5, 'frequency': 25, 'phrase_type': 'bigram'},
                {'phrase': 'সরকার পদক্ষেপ', 'score': 88.2, 'frequency': 18, 'phrase_type': 'bigram'}
            ],
            'খেলাধুলা': [
                {'phrase': 'ক্রিকেট দল', 'score': 92.1, 'frequency': 22, 'phrase_type': 'bigram'},
                {'phrase': 'বিশ্বকাপ', 'score': 85.7, 'frequency': 15, 'phrase_type': 'unigram'}
            ]
        }
        
        # Test saving category phrases
        saved_count = service.save_category_trending_phrases(
            test_phrases, 
            date.today(),
            source="test"
        )
        
        print(f"✅ Saved {saved_count} test phrases")
        
        # Test retrieving phrases
        politics_phrases = service.get_category_trending_phrases('রাজনীতি', limit=10)
        print(f"📋 Retrieved {len(politics_phrases)} politics phrases")
        
        if politics_phrases:
            print("  Sample phrases:")
            for phrase in politics_phrases[:3]:
                print(f"    - {phrase['phrase']} (score: {phrase['score']})")
        
        # Test category activity
        top_categories = service.get_top_categories_by_activity(limit=5)
        print(f"🏆 Top {len(top_categories)} active categories:")
        
        for cat_stat in top_categories:
            print(f"  - {cat_stat['category']}: {cat_stat['phrase_count']} phrases (avg score: {cat_stat['avg_score']:.1f})")
        
        print("✅ Category service tests completed successfully")
        
    except Exception as e:
        print(f"❌ Category service test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    
    print("🚀 Enhanced Category Detection System - Test Suite")
    print("=" * 80)
    
    # Test 1: Enhanced category detection function
    test_results = test_enhanced_category_detection()
    
    # Test 2: Real newspaper data
    real_data_results = test_with_real_data()
    
    # Test 3: Category service
    test_category_service()
    
    print("\n🎯 Test Summary")
    print("=" * 40)
    print(f"✅ Enhanced detection accuracy: {(test_results['correct']/test_results['total'])*100:.1f}%")
    
    if real_data_results:
        total_categorized = sum(real_data_results.values())
        uncategorized = real_data_results.get('সাধারণ', 0)
        categorization_rate = ((total_categorized - uncategorized) / total_categorized) * 100 if total_categorized > 0 else 0
        print(f"📊 Real data categorization rate: {categorization_rate:.1f}%")
        print(f"🏷️ Total categories detected: {len(real_data_results)}")
    
    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    main()
