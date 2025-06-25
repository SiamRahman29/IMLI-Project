#!/usr/bin/env python3
"""
Newspaper Scraping & Categorization Verification Script
========================================================

This script verifies:
1. Whether newspaper scraping functions are working correctly
2. Whether URL categorization is working properly
3. Provides detailed statistics and accuracy metrics
4. No LLM calls - only categorization verification

Author: IMLI Project
Date: 2025-01-25
"""

import sys
import os
import time
import json
from datetime import datetime
from collections import defaultdict, Counter
from urllib.parse import urlparse

# Add the app directory to Python path to import helpers
sys.path.append('/home/bs01127/IMLI-Project/app')
from routes.helpers import scrape_bengali_news, detect_category_from_url, categorize_articles

def print_header():
    """Print script header"""
    print("=" * 80)
    print("🔍 NEWSPAPER SCRAPING & CATEGORIZATION VERIFICATION")
    print("=" * 80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Purpose: Verify newspaper scraping and categorization accuracy")
    print(f"📝 No LLM calls - Only categorization verification")
    print("=" * 80)

def test_scraping_functions():
    """Test newspaper scraping functions"""
    print("\n🚀 STEP 1: Testing Newspaper Scraping Functions")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        print("📰 Calling scrape_bengali_news()...")
        articles = scrape_bengali_news()
        
        scraping_time = time.time() - start_time
        
        print(f"\n✅ Scraping completed successfully!")
        print(f"⏱️  Time taken: {scraping_time:.2f} seconds")
        print(f"📊 Total articles scraped: {len(articles)}")
        
        # Analyze by source
        source_counts = Counter(article.get('source', 'unknown') for article in articles)
        
        print(f"\n📈 Source-wise breakdown:")
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {source:<20}: {count:4d} articles")
        
        # Sample some articles
        print(f"\n📝 Sample scraped articles:")
        for i, article in enumerate(articles[:5], 1):
            url = article.get('url', 'No URL')[:60]
            title = article.get('title', 'No Title')[:40]
            source = article.get('source', 'Unknown')
            print(f"   {i}. [{source}] {title}...")
            print(f"      URL: {url}...")
        
        return articles, True
    
    except Exception as e:
        print(f"❌ Scraping failed with error: {e}")
        return [], False

def test_categorization_function():
    """Test the categorization function with sample URLs"""
    print("\n🏷️  STEP 2: Testing Categorization Function")
    print("-" * 60)
    
    # Test URLs with known categories
    test_cases = [
        # জাতীয় (National)
        ("https://www.prothomalo.com/bangladesh/abc123", "", "", "জাতীয়"),
        ("https://www.dailyjanakantha.com/national/news/123456", "", "", "জাতীয়"),
        
        # আন্তর্জাতিক (International)
        ("https://www.prothomalo.com/world/abc123", "", "", "আন্তর্জাতিক"),
        ("https://www.ajkerpatrika.com/international/middle-east-1/ajp123", "", "", "আন্তর্জাতিক"),
        
        # খেলাধুলা (Sports)
        ("https://www.prothomalo.com/sports/cricket/abc123", "", "", "খেলাধুলা"),
        ("https://www.ajkerpatrika.com/sports/cricket/ajp123", "", "", "খেলাধুলা"),
        
        # বিনোদন (Entertainment)
        ("https://www.dailyjanakantha.com/entertainment/news/123456", "", "", "বিনোদন"),
        ("https://www.ajkerpatrika.com/entertainment/bollywood/ajp123", "", "", "বিনোদন"),
        
        # অর্থনীতি (Economy)
        ("https://www.ajkerpatrika.com/business/ajp123", "", "", "অর্থনীতি"),
        ("https://www.dailyjanakantha.com/economy/news/123456", "", "", "অর্থনীতি"),
        
        # প্রযুক্তি (Technology)
        ("https://www.ajkerpatrika.com/technology/ajp123", "", "", "প্রযুক্তি"),
        ("https://www.jugantor.com/tech", "", "", "প্রযুক্তি"),
        
        # শিক্ষা (Education)
        ("https://www.prothomalo.com/education/abc123", "", "", "শিক্ষা"),
        ("https://www.jugantor.com/campus", "", "", "শিক্ষা"),
        
        # রাজনীতি (Politics)
        ("https://www.prothomalo.com/politics/abc123", "", "", "রাজনীতি"),
        ("https://www.dailyjanakantha.com/politics/news/123456", "", "", "রাজনীতি"),
        
        # মতামত (Opinion)
        ("https://www.prothomalo.com/opinion/column/abc123", "", "", "মতামত"),
        ("https://www.ajkerpatrika.com/op-ed/editorial/ajp123", "", "", "মতামত"),
        
        # ধর্ম (Religion)
        ("https://www.ajkerpatrika.com/islam/ajp123", "", "", "ধর্ম"),
        ("https://www.jugantor.com/islam-life", "", "", "ধর্ম")
    ]
    
    correct_predictions = 0
    total_tests = len(test_cases)
    
    print(f"🧪 Testing {total_tests} categorization cases...")
    print(f"\n📋 Test Results:")
    
    for i, (url, title, content, expected) in enumerate(test_cases, 1):
        try:
            predicted = detect_category_from_url(url, title, content)
            is_correct = predicted == expected
            
            if is_correct:
                correct_predictions += 1
                status = "✅"
            else:
                status = "❌"
            
            domain = urlparse(url).netloc
            path_sample = urlparse(url).path[:25]
            
            print(f"   {i:2d}. {status} {domain} {path_sample}...")
            print(f"       Expected: {expected} | Got: {predicted}")
            
        except Exception as e:
            print(f"   {i:2d}. ❌ Error testing URL: {e}")
    
    accuracy = (correct_predictions / total_tests) * 100
    print(f"\n📊 Categorization Accuracy: {correct_predictions}/{total_tests} = {accuracy:.1f}%")
    
    if accuracy >= 80:
        print(f"✅ Categorization is working well (≥80% accuracy)")
    elif accuracy >= 60:
        print(f"⚠️  Categorization needs improvement (60-80% accuracy)")
    else:
        print(f"❌ Categorization needs major fixes (<60% accuracy)")
    
    return accuracy >= 60

def test_real_articles_categorization(articles):
    """Test categorization on real scraped articles"""
    print("\n🔍 STEP 3: Testing Categorization on Real Articles")
    print("-" * 60)
    
    if not articles:
        print("❌ No articles to test categorization")
        return False
    
    print(f"🏷️  Categorizing {len(articles)} real articles...")
    
    start_time = time.time()
    
    try:
        # Categorize all articles
        categorized_articles = categorize_articles(articles)
        
        categorization_time = time.time() - start_time
        
        # Analyze categories
        category_counts = Counter(article.get('category', 'অজানা') for article in categorized_articles)
        
        print(f"✅ Categorization completed!")
        print(f"⏱️  Time taken: {categorization_time:.2f} seconds")
        print(f"📊 Average time per article: {(categorization_time/len(articles)*1000):.1f}ms")
        
        print(f"\n📈 Category Distribution:")
        total_articles = len(categorized_articles)
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_articles) * 100
            bar_length = int(percentage / 2)
            bar = '█' * bar_length + '░' * (25 - bar_length)
            print(f"   {category:<15}: {count:4d} ({percentage:5.1f}%) {bar}")
        
        # Show samples from each major category
        print(f"\n📝 Sample categorized articles:")
        major_categories = [cat for cat, count in category_counts.most_common(5)]
        
        for category in major_categories:
            sample_articles = [art for art in categorized_articles if art.get('category') == category][:2]
            print(f"\n   🏷️  {category}:")
            for i, article in enumerate(sample_articles, 1):
                url = article.get('url', 'No URL')[:50]
                title = article.get('title', 'No Title')[:40]
                source = article.get('source', 'Unknown')
                print(f"      {i}. [{source}] {title}...")
                print(f"         URL: {url}...")
        
        # Check for uncategorized articles
        uncategorized = category_counts.get('সাধারণ', 0)
        uncategorized_pct = (uncategorized / total_articles) * 100
        
        print(f"\n📊 Categorization Quality Assessment:")
        print(f"   📋 Total articles: {total_articles}")
        print(f"   🏷️  Categorized: {total_articles - uncategorized} ({100-uncategorized_pct:.1f}%)")
        print(f"   ❓ Uncategorized: {uncategorized} ({uncategorized_pct:.1f}%)")
        print(f"   📈 Categories found: {len(category_counts)}")
        
        if uncategorized_pct <= 20:
            print(f"   ✅ Good categorization rate (≤20% uncategorized)")
        elif uncategorized_pct <= 40:
            print(f"   ⚠️  Moderate categorization rate (20-40% uncategorized)")
        else:
            print(f"   ❌ Poor categorization rate (>40% uncategorized)")
        
        return categorized_articles, uncategorized_pct <= 40
    
    except Exception as e:
        print(f"❌ Real article categorization failed: {e}")
        return [], False

def test_source_specific_patterns(articles):
    """Test source-specific URL patterns"""
    print("\n🌐 STEP 4: Testing Source-Specific URL Patterns")
    print("-" * 60)
    
    if not articles:
        print("❌ No articles to analyze patterns")
        return
    
    # Group by source
    source_articles = defaultdict(list)
    for article in articles:
        source = article.get('source', 'unknown')
        source_articles[source].append(article)
    
    print(f"🔍 Analyzing URL patterns by source...")
    
    for source, source_arts in source_articles.items():
        print(f"\n📰 {source.upper()} ({len(source_arts)} articles):")
        
        # Analyze URL patterns
        domains = set()
        path_patterns = Counter()
        
        for article in source_arts[:10]:  # Sample first 10
            url = article.get('url', '')
            if url:
                parsed = urlparse(url)
                domains.add(parsed.netloc)
                
                # Extract path pattern
                path = parsed.path
                # Generalize patterns
                import re
                path = re.sub(r'/\d+', '/[ID]', path)  # Replace numbers
                path = re.sub(r'/ajp[a-z0-9]+', '/[AJP_ID]', path)  # Ajker Patrika IDs
                path = re.sub(r'/[a-z0-9]{10,}', '/[LONG_ID]', path)  # Long IDs
                
                path_patterns[path] += 1
        
        # Show domains
        print(f"   🌐 Domains: {', '.join(sorted(domains))}")
        
        # Show common patterns
        print(f"   🔗 Common URL patterns:")
        for pattern, count in path_patterns.most_common(3):
            print(f"      {pattern} (appears {count} times)")
        
        # Test categorization on this source
        categorized = 0
        for article in source_arts[:5]:  # Test first 5
            url = article.get('url', '')
            title = article.get('title', '')
            category = detect_category_from_url(url, title)
            if category != 'সাধারণ':
                categorized += 1
        
        cat_rate = (categorized / min(5, len(source_arts))) * 100
        print(f"   📊 Categorization rate: {categorized}/{min(5, len(source_arts))} = {cat_rate:.0f}%")

def save_verification_results(articles, categorized_articles=None):
    """Save verification results to file"""
    print("\n💾 STEP 5: Saving Verification Results")
    print("-" * 60)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"newspaper_verification_results_{timestamp}.json"
    filepath = f"/home/bs01127/IMLI-Project/{filename}"
    
    # Prepare results data
    results = {
        "verification_info": {
            "timestamp": datetime.now().isoformat(),
            "total_articles_scraped": len(articles),
            "scraping_sources": list(set(art.get('source', 'unknown') for art in articles)),
            "verification_type": "scraping_and_categorization_only",
            "llm_used": False
        },
        "scraping_results": {
            "total_articles": len(articles),
            "sources_breakdown": dict(Counter(art.get('source', 'unknown') for art in articles)),
            "sample_articles": articles[:10]  # Save first 10 as samples
        }
    }
    
    if categorized_articles:
        category_counts = Counter(art.get('category', 'অজানা') for art in categorized_articles)
        results["categorization_results"] = {
            "total_categorized": len(categorized_articles),
            "category_distribution": dict(category_counts),
            "uncategorized_count": category_counts.get('সাধারণ', 0),
            "uncategorized_percentage": (category_counts.get('সাধারণ', 0) / len(categorized_articles)) * 100,
            "total_categories_found": len(category_counts),
            "sample_categorized_articles": categorized_articles[:10]
        }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ Results saved to: {filename}")
        print(f"📁 Full path: {filepath}")
        print(f"📊 Data includes:")
        print(f"   • Scraping results and source breakdown")
        print(f"   • Categorization statistics")
        print(f"   • Sample articles with categories")
        
        return filepath
    
    except Exception as e:
        print(f"❌ Failed to save results: {e}")
        return None

def print_final_summary(scraping_success, categorization_success, real_test_success):
    """Print final verification summary"""
    print("\n" + "=" * 80)
    print("📋 FINAL VERIFICATION SUMMARY")
    print("=" * 80)
    
    print(f"🔍 Test Results:")
    print(f"   1. Newspaper Scraping:     {'✅ PASS' if scraping_success else '❌ FAIL'}")
    print(f"   2. URL Categorization:     {'✅ PASS' if categorization_success else '❌ FAIL'}")
    print(f"   3. Real Article Testing:   {'✅ PASS' if real_test_success else '❌ FAIL'}")
    
    overall_success = scraping_success and categorization_success and real_test_success
    
    print(f"\n🎯 Overall Status: {'✅ ALL SYSTEMS WORKING' if overall_success else '❌ ISSUES DETECTED'}")
    
    if overall_success:
        print(f"\n✅ Your newspaper scraping and categorization system is working correctly!")
        print(f"   • All scraping functions are operational")
        print(f"   • URL categorization is accurate")
        print(f"   • Real articles are being properly categorized")
    else:
        print(f"\n⚠️  Issues detected in your system:")
        if not scraping_success:
            print(f"   • Newspaper scraping functions need fixing")
        if not categorization_success:
            print(f"   • URL categorization function needs improvement")
        if not real_test_success:
            print(f"   • Real article categorization has issues")
    
    print("=" * 80)

def main():
    """Main verification function"""
    print_header()
    
    # Step 1: Test scraping functions
    articles, scraping_success = test_scraping_functions()
    
    # Step 2: Test categorization function
    categorization_success = test_categorization_function()
    
    # Step 3: Test real articles (if scraping worked)
    real_test_success = False
    categorized_articles = []
    
    if scraping_success and articles:
        categorized_articles, real_test_success = test_real_articles_categorization(articles)
        
        # Step 4: Test source-specific patterns
        test_source_specific_patterns(articles)
    
    # Step 5: Save results
    save_verification_results(articles, categorized_articles if isinstance(categorized_articles, list) else None)
    
    # Final summary
    print_final_summary(scraping_success, categorization_success, real_test_success)

if __name__ == "__main__":
    main()
