#!/usr/bin/env python3
"""
Direct Test for New Newspapers - Manual Implementation
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

def robust_request(url, timeout=30):
    """Robust request function with error handling"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        return requests.get(url, timeout=timeout, headers=headers)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def test_jai_jai_din():
    """Test Jai Jai Din manually"""
    print("🧪 Testing Jai Jai Din")
    print("-" * 40)
    
    articles = []
    try:
        homepage = "https://www.jaijaidinbd.com/"
        print(f"📡 Fetching homepage: {homepage}")
        
        res = robust_request(homepage)
        if not res:
            print("❌ Failed to fetch homepage")
            return articles
        
        print(f"✅ Homepage loaded (Status: {res.status_code})")
        
        soup = BeautifulSoup(res.text, "html.parser")
        print(f"📄 Page title: {soup.title.text if soup.title else 'No title'}")
        
        # Test different link selectors
        selectors = [
            "h2 a",
            "h3 a", 
            "a[href*='/news/']",
            "a[href*='/details/']",
            ".news-title a",
            ".headline a"
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            print(f"🔍 Selector '{selector}': {len(links)} links found")
            
            if links:
                # Show sample links
                for i, link in enumerate(links[:3], 1):
                    href = link.get('href', '')
                    text = link.text.strip()[:50]
                    print(f"   {i}. {href} -> {text}...")
        
        # Try scraping with most promising selector
        all_links = soup.select("h2 a, h3 a, a[href*='/news/'], a[href*='/details/']")
        print(f"\n📰 Found {len(all_links)} potential article links")
        
        # Test scraping first few articles
        for i, link in enumerate(all_links[:5], 1):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            
            print(f"\n📖 Testing article {i}: {url}")
            
            article_res = robust_request(url)
            if not article_res:
                print(f"   ❌ Failed to fetch article")
                continue
            
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                headings = []
                for tag in article_soup.find_all(['h1', 'h2']):
                    if tag.text.strip():
                        headings.append(tag.text.strip())
                
                heading_text = ' '.join(headings)
                
                if headings:
                    print(f"   ✅ Headings found: {headings[0][:50]}...")
                    articles.append({
                        "title": headings[0] if headings else "",
                        "heading": heading_text,
                        "url": url,
                        "published_date": datetime.now().date(),
                        "source": "jai_jai_din"
                    })
                else:
                    print(f"   ⚠️  No headings found")
                    
            except Exception as e:
                print(f"   ❌ Error parsing article: {e}")
        
        print(f"\n📊 Successfully scraped: {len(articles)} articles")
        return articles
        
    except Exception as e:
        print(f"❌ Error scraping Jai Jai Din: {e}")
        return articles

def test_kaler_kantho():
    """Test Kaler Kantho manually"""
    print("\n🧪 Testing Kaler Kantho")
    print("-" * 40)
    
    articles = []
    try:
        homepage = "https://www.kalerkantho.com/"
        print(f"📡 Fetching homepage: {homepage}")
        
        res = robust_request(homepage)
        if not res:
            print("❌ Failed to fetch homepage")
            return articles
        
        print(f"✅ Homepage loaded (Status: {res.status_code})")
        
        soup = BeautifulSoup(res.text, "html.parser")
        print(f"📄 Page title: {soup.title.text if soup.title else 'No title'}")
        
        # Test different selectors for Kaler Kantho
        selectors = [
            "a[href*='/online/']",
            "h2 a",
            "h3 a",
            ".news-title a",
            ".kt-post a"
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            print(f"🔍 Selector '{selector}': {len(links)} links found")
        
        # Use best selector
        links = soup.select("a[href*='/online/']")
        print(f"\n📰 Found {len(links)} potential article links")
        
        # Test first few articles
        for i, link in enumerate(links[:3], 1):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            
            print(f"\n📖 Testing article {i}: {url}")
            
            article_res = robust_request(url)
            if not article_res:
                print(f"   ❌ Failed to fetch article")
                continue
            
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
                heading_text = ' '.join(headings)
                
                if headings:
                    print(f"   ✅ Headings found: {headings[0][:50]}...")
                    articles.append({
                        "title": headings[0] if headings else "",
                        "heading": heading_text,
                        "url": url,
                        "published_date": datetime.now().date(),
                        "source": "kaler_kantho"
                    })
                else:
                    print(f"   ⚠️  No headings found")
                    
            except Exception as e:
                print(f"   ❌ Error parsing article: {e}")
        
        print(f"\n📊 Successfully scraped: {len(articles)} articles")
        return articles
        
    except Exception as e:
        print(f"❌ Error scraping Kaler Kantho: {e}")
        return articles

def main():
    """Main testing function"""
    print("🔍 MANUAL TESTING OF NEW NEWSPAPERS")
    print("=" * 60)
    
    results = {}
    
    # Test Jai Jai Din
    jai_articles = test_jai_jai_din()
    results['Jai Jai Din'] = len(jai_articles)
    
    # Test Kaler Kantho  
    kaler_articles = test_kaler_kantho()
    results['Kaler Kantho'] = len(kaler_articles)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 TESTING RESULTS SUMMARY")
    print(f"{'='*60}")
    
    total_articles = 0
    for name, count in results.items():
        status = "✅ WORKING" if count > 0 else "❌ NO ARTICLES"
        print(f"{name:<20}: {status} ({count} articles)")
        total_articles += count
    
    print(f"\nTotal articles scraped: {total_articles}")
    print(f"🎉 Manual testing completed!")

if __name__ == "__main__":
    main()
