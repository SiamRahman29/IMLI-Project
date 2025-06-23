#!/usr/bin/env python3
"""
Comprehensive URL Extractor for Active Bengali Newspapers
Extracts URLs from all active sources (non-commented) in helpers.py
"""

import sys
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re

sys.path.append('/home/bs01127/IMLI-Project')

# Import scraping functions from helpers
from app.routes.helpers import (
    scrape_prothom_alo,
    scrape_kaler_kantho, 
    scrape_jugantor,
    scrape_bd_pratidin,
    scrape_samakal,
    scrape_janakantha,
    scrape_inqilab,
    scrape_noya_diganta,
    scrape_jai_jai_din,
    scrape_manobkantha,
    scrape_ajker_patrika,
    scrape_protidiner_sangbad
)

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

def extract_urls_from_all_sources():
    """Extract URLs from all active newspaper sources"""
    
    # Active sources based on helpers.py (non-commented)
    active_sources = [
        ("prothom_alo", scrape_prothom_alo),
        ("kaler_kantho", scrape_kaler_kantho),
        ("jugantor", scrape_jugantor),
        ("bd_pratidin", scrape_bd_pratidin),
        ("samakal", scrape_samakal),
        ("janakantha", scrape_janakantha),
        ("inqilab", scrape_inqilab),
        ("noya_diganta", scrape_noya_diganta),
        ("jai_jai_din", scrape_jai_jai_din),
        ("manobkantha", scrape_manobkantha),
        ("ajker_patrika", scrape_ajker_patrika),
        ("protidiner_sangbad", scrape_protidiner_sangbad)
    ]
    
    print(f"🚀 Starting URL extraction from {len(active_sources)} active sources...")
    print("=" * 60)
    
    all_urls = []
    sources_count = {}
    
    for source_name, scrape_func in active_sources:
        print(f"\n📰 Processing {source_name}...")
        print("-" * 40)
        
        try:
            # Call the scraping function
            articles = scrape_func()
            source_urls = []
            
            for article in articles:
                url = article.get('url', '')
                title = article.get('title', '')
                heading = article.get('heading', '')
                
                if url:
                    url_data = {
                        "url": url,
                        "source": source_name,
                        "title": title,
                        "heading": heading,
                        "scraped_at": datetime.now().isoformat()
                    }
                    source_urls.append(url_data)
                    all_urls.append(url_data)
            
            sources_count[source_name] = len(source_urls)
            print(f"✅ {source_name}: {len(source_urls)} URLs extracted")
            
            # Show sample URLs
            if source_urls:
                print(f"   Sample URLs:")
                for i, url_data in enumerate(source_urls[:3], 1):
                    print(f"   {i}. {url_data['url']}")
                    print(f"      Title: {url_data['title'][:50]}...")
            
            # Small delay between sources
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Error processing {source_name}: {e}")
            sources_count[source_name] = 0
    
    return all_urls, sources_count

def save_extracted_urls(urls_data, sources_count):
    """Save extracted URLs to JSON file"""
    
    # Create filename with current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"extracted_urls_{timestamp}.json"
    filepath = f"/home/bs01127/IMLI-Project/{filename}"
    
    # Prepare data structure similar to existing format
    output_data = {
        "extraction_info": {
            "total_urls": len(urls_data),
            "extraction_date": datetime.now().isoformat(),
            "sources_count": sources_count,
            "total_sources": len(sources_count)
        },
        "urls": urls_data
    }
    
    # Save to JSON file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 URLs saved to: {filename}")
        return filepath
        
    except Exception as e:
        print(f"❌ Error saving URLs: {e}")
        return None

def create_simple_urls_file(urls_data):
    """Create simple text file with just URLs"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"simple_urls_{timestamp}.txt"
    filepath = f"/home/bs01127/IMLI-Project/{filename}"
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            for url_data in urls_data:
                f.write(f"{url_data['url']}\n")
        
        print(f"📄 Simple URLs saved to: {filename}")
        return filepath
        
    except Exception as e:
        print(f"❌ Error saving simple URLs: {e}")
        return None

def main():
    """Main extraction process"""
    print("🔍 Bengali Newspaper URL Extraction Tool")
    print("=" * 50)
    
    # Extract URLs from all active sources
    urls_data, sources_count = extract_urls_from_all_sources()
    
    if not urls_data:
        print("❌ No URLs extracted from any source!")
        return
    
    # Print summary
    print(f"\n📊 EXTRACTION SUMMARY")
    print("=" * 30)
    print(f"Total URLs extracted: {len(urls_data)}")
    print(f"Active sources: {len(sources_count)}")
    print()
    
    print("📈 Per-source breakdown:")
    for source, count in sorted(sources_count.items(), key=lambda x: x[1], reverse=True):
        percentage = (count/len(urls_data))*100 if len(urls_data) > 0 else 0
        print(f"  {source:<20}: {count:3d} URLs ({percentage:5.1f}%)")
    
    # Save files
    print(f"\n💾 SAVING FILES...")
    print("-" * 20)
    
    json_file = save_extracted_urls(urls_data, sources_count)
    txt_file = create_simple_urls_file(urls_data)
    
    if json_file:
        print(f"✅ Complete data: {json_file}")
    if txt_file:
        print(f"✅ Simple URLs: {txt_file}")
    
    print(f"\n🎉 URL extraction completed successfully!")
    print(f"📊 Total: {len(urls_data)} URLs from {len(sources_count)} sources")

if __name__ == "__main__":
    main()
