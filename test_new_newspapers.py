#!/usr/bin/env python3
"""
Test Script for Newly Added Bengali Newspapers
Tests scraping functionality for: jai_jai_din, kaler_kantho, bd_pratidin, samakal, noya_diganta
"""

import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

sys.path.append('/home/bs01127/IMLI-Project')

# Import specific scraping functions for new newspapers
from app.routes.helpers import (
    scrape_jai_jai_din,
    scrape_kaler_kantho, 
    scrape_bd_pratidin,
    scrape_samakal,
    scrape_noya_diganta,
    robust_request
)

def test_single_newspaper(name, scrape_function, homepage_url):
    """Test a single newspaper scraping function"""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING: {name}")
    print(f"📰 Homepage: {homepage_url}")
    print(f"🔧 Function: {scrape_function.__name__}")
    print('='*60)
    
    try:
        # First test if homepage is accessible
        print(f"📡 Testing homepage connectivity...")
        response = robust_request(homepage_url)
        
        if not response:
            print(f"❌ Homepage not accessible: {homepage_url}")
            return False, 0, []
        
        if response.status_code != 200:
            print(f"❌ Homepage returned status: {response.status_code}")
            return False, 0, []
        
        print(f"✅ Homepage accessible (Status: {response.status_code})")
        
        # Test the homepage structure
        soup = BeautifulSoup(response.text, "html.parser")
        print(f"📄 Page title: {soup.title.text if soup.title else 'No title'}")
        
        # Count different types of links
        all_links = soup.find_all('a', href=True)
        news_links = soup.select("a[href*='/news/'], a[href*='/details/']")
        h_links = soup.select("h1 a, h2 a, h3 a")
        
        print(f"🔗 Total links found: {len(all_links)}")
        print(f"📰 News links (/news/, /details/): {len(news_links)}")
        print(f"📰 Heading links (h1/h2/h3 a): {len(h_links)}")
        
        # Show sample links
        if news_links or h_links:
            sample_links = (news_links + h_links)[:5]
            print(f"📋 Sample links:")
            for i, link in enumerate(sample_links, 1):
                href = link.get('href', '')
                text = link.text.strip()[:50]
                print(f"   {i}. {href} -> {text}...")
        
        # Now test the actual scraping function
        print(f"\n🚀 Running scraping function...")
        start_time = time.time()
        
        articles = scrape_function()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Scraping completed in {duration:.2f} seconds")
        print(f"📊 Articles scraped: {len(articles)}")
        
        if articles:
            print(f"✅ SUCCESS: {name} scraping is working!")
            
            # Show sample articles
            print(f"\n📰 Sample articles:")
            for i, article in enumerate(articles[:3], 1):
                title = article.get('title', 'No title')[:50]
                url = article.get('url', 'No URL')
                heading = article.get('heading', 'No heading')[:80]
                
                print(f"   {i}. Title: {title}...")
                print(f"      URL: {url}")
                print(f"      Heading: {heading}...")
                print(f"      Source: {article.get('source', 'Unknown')}")
                print()
            
            return True, len(articles), articles
        else:
            print(f"⚠️  WARNING: {name} function runs but returns no articles")
            return True, 0, []
    
    except Exception as e:
        print(f"❌ ERROR testing {name}: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, []

def main():
    """Main testing function"""
    print("🔍 TESTING NEWLY ADDED BENGALI NEWSPAPERS")
    print("=" * 80)
    
    # Define test cases for new newspapers
    test_cases = [
        ("Jai Jai Din", scrape_jai_jai_din, "https://www.jaijaidinbd.com/"),
        ("Kaler Kantho", scrape_kaler_kantho, "https://www.kalerkantho.com/"),
        ("Bangladesh Pratidin", scrape_bd_pratidin, "https://www.bd-pratidin.com/"),
        ("Samakal", scrape_samakal, "https://samakal.com/"),
        ("Noya Diganta", scrape_noya_diganta, "https://www.dailynayadiganta.com/")
    ]
    
    results = {}
    total_articles = 0
    successful_sources = 0
    
    # Test each newspaper
    for name, func, url in test_cases:
        success, article_count, articles = test_single_newspaper(name, func, url)
        
        results[name] = {
            'success': success,
            'article_count': article_count,
            'articles': articles
        }
        
        if success:
            successful_sources += 1
            total_articles += article_count
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"📊 TESTING SUMMARY")
    print(f"{'='*80}")
    
    print(f"🎯 Total newspapers tested: {len(test_cases)}")
    print(f"✅ Successfully working: {successful_sources}")
    print(f"❌ Failed/Issues: {len(test_cases) - successful_sources}")
    print(f"📰 Total articles scraped: {total_articles}")
    print()
    
    print(f"📈 Per-newspaper results:")
    for name, result in results.items():
        status = "✅ WORKING" if result['success'] else "❌ FAILED"
        count = result['article_count']
        print(f"  {name:<20}: {status} ({count} articles)")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    working_sources = [name for name, result in results.items() if result['success'] and result['article_count'] > 0]
    issues_sources = [name for name, result in results.items() if not result['success'] or result['article_count'] == 0]
    
    if working_sources:
        print(f"✅ Ready for production: {', '.join(working_sources)}")
    
    if issues_sources:
        print(f"⚠️  Need investigation: {', '.join(issues_sources)}")
        print(f"   - Check website structure changes")
        print(f"   - Verify CSS selectors")
        print(f"   - Test URL patterns")
    
    print(f"\n🎉 Testing completed!")
    
    return results

if __name__ == "__main__":
    main()
