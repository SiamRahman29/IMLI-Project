#!/usr/bin/env python3
"""
Temporary URL Extraction Tool
Extract all URLs from scraping and save to file for category analysis
This is a ONE-TIME utility function
"""

import json
import os
from datetime import datetime
from typing import List, Dict
from collections import defaultdict, Counter

def extract_and_save_urls_from_scraping():
    """
    Extract all URLs from current scraping process and save to file
    This function will be called once to collect URL patterns
    """
    print("🔍 Starting URL extraction from scraping process...")
    
    # Import your existing scraping functions
    try:
        from app.routes.helpers import scrape_bengali_news
        
        # Run full scraping to get all URLs
        print("📰 Running full newspaper scraping...")
        articles = scrape_bengali_news()
        
        if not articles:
            print("❌ No articles found!")
            return
        
        print(f"✅ Found {len(articles)} articles from scraping")
        
        # Extract URL data with metadata
        url_data = []
        source_stats = Counter()
        
        for article in articles:
            url = article.get('url', '')
            source = article.get('source', 'unknown')
            title = article.get('title', '')
            heading = article.get('heading', '')
            
            if url:
                url_data.append({
                    'url': url,
                    'source': source,
                    'title': title,
                    'heading': heading,
                    'scraped_at': datetime.now().isoformat()
                })
                source_stats[source] += 1
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"extracted_urls_{timestamp}.json"
        filepath = os.path.join(os.getcwd(), filename)
        
        # Create comprehensive data structure
        output_data = {
            'extraction_info': {
                'total_urls': len(url_data),
                'extraction_date': datetime.now().isoformat(),
                'sources_count': dict(source_stats),
                'total_sources': len(source_stats)
            },
            'urls': url_data,
            'source_breakdown': dict(source_stats)
        }
        
        # Save to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ URLs saved to: {filepath}")
        print(f"📊 Total URLs extracted: {len(url_data)}")
        print(f"📰 Sources found: {len(source_stats)}")
        
        # Print source breakdown
        print("\n📊 Source Breakdown:")
        for source, count in source_stats.most_common():
            print(f"  {source:<20}: {count:3d} articles")
        
        # Analyze URL patterns (preview)
        print("\n🔍 URL Pattern Preview (first 10):")
        for i, item in enumerate(url_data[:10], 1):
            print(f"  {i:2d}. {item['source']:<15} | {item['url']}")
        
        # Create a separate simple URL list file for easy sharing
        simple_urls_file = f"simple_urls_{timestamp}.txt"
        with open(simple_urls_file, 'w', encoding='utf-8') as f:
            for item in url_data:
                f.write(f"{item['url']}\n")
        
        print(f"📝 Simple URL list saved to: {simple_urls_file}")
        
        return {
            'main_file': filepath,
            'simple_file': simple_urls_file,
            'total_urls': len(url_data),
            'sources': dict(source_stats)
        }
        
    except Exception as e:
        print(f"❌ Error during URL extraction: {e}")
        return None

def analyze_url_patterns(filepath: str):
    """
    Analyze URL patterns from saved file to detect category patterns
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        urls = [item['url'] for item in data['urls']]
        
        print(f"🔍 Analyzing {len(urls)} URLs for patterns...")
        
        # Common category patterns to look for
        pattern_categories = {
            'রাজনীতি': ['politics', 'rajniti', 'national', 'govt', 'government', 'political'],
            'অর্থনীতি': ['economy', 'business', 'bank', 'orthoniti', 'economic', 'finance'],
            'খেলাধুলা': ['sports', 'khela', 'cricket', 'football', 'game', 'match'],
            'আন্তর্জাতিক': ['international', 'world', 'global', 'foreign', 'antorjatik'],
            'বিনোদন': ['entertainment', 'binodun', 'cinema', 'movie', 'culture'],
            'প্রযুক্তি': ['technology', 'tech', 'computer', 'mobile', 'internet'],
            'স্বাস্থ্য': ['health', 'medical', 'hospital', 'doctor', 'shasto'],
            'শিক্ষা': ['education', 'school', 'university', 'student', 'shikkha']
        }
        
        # Count pattern matches
        pattern_matches = defaultdict(list)
        
        for url in urls:
            url_lower = url.lower()
            for category, patterns in pattern_categories.items():
                for pattern in patterns:
                    if pattern in url_lower:
                        pattern_matches[category].append(url)
                        break
        
        # Print analysis
        print("\n📊 URL Pattern Analysis:")
        for category, matched_urls in pattern_matches.items():
            print(f"  {category:<15}: {len(matched_urls):3d} URLs")
            if matched_urls:
                print(f"    Sample: {matched_urls[0]}")
        
        return pattern_matches
        
    except Exception as e:
        print(f"❌ Error analyzing patterns: {e}")
        return {}

# Integration function for your existing route
def add_to_generate_candidates_route():
    """
    Function to integrate with your existing generate_candidates route
    """
    print("🔧 Adding URL extraction to generate_candidates route...")
    
    result = extract_and_save_urls_from_scraping()
    
    if result:
        print(f"✅ URL extraction completed!")
        print(f"📁 Main file: {result['main_file']}")
        print(f"📄 Simple file: {result['simple_file']}")
        print(f"📊 Total: {result['total_urls']} URLs from {len(result['sources'])} sources")
        return result
    else:
        print("❌ URL extraction failed!")
        return None

if __name__ == "__main__":
    # Run directly for testing
    print("🚀 Running URL Extraction Tool...")
    result = extract_and_save_urls_from_scraping()
    
    if result:
        # Also run pattern analysis
        analyze_url_patterns(result['main_file'])
