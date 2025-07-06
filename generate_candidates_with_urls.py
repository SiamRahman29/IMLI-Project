#!/usr/bin/env python3
"""
Generate Candidates and Extract URLs to JSON
This script calls the generate_candidate route and extracts all scraped URLs to a JSON file
"""

import sys
import json
import requests
from datetime import datetime
import os

sys.path.append('/home/bs01127/IMLI-Project')

# Import required modules
from app.routes.helpers import scrape_bengali_news
import sqlite3

def collect_scraped_urls_and_save():
    """
    Call scrape_bengali_news and collect all scraped URLs
    """
    print("🚀 Starting URL Collection from Active Newspapers")
    print("=" * 70)
    
    try:
        # Step 1: Call scrape_bengali_news to get articles
        print("\n📰 STEP 1: Scraping Bengali News Sources")
        print("-" * 50)
        
        articles = scrape_bengali_news()
        
        print(f"\n📊 Scraping Summary:")
        print(f"   Total articles collected: {len(articles)}")
        
        # Group articles by source
        sources_summary = {}
        urls_by_source = {}
        
        for article in articles:
            source = article.get('source', 'unknown')
            url = article.get('url', '')
            
            # Count by source
            sources_summary[source] = sources_summary.get(source, 0) + 1
            
            # Collect URLs by source
            if source not in urls_by_source:
                urls_by_source[source] = []
            
            if url:
                urls_by_source[source].append({
                    'url': url,
                    'title': article.get('title', ''),
                    'heading': article.get('heading', ''),
                    'published_date': str(article.get('published_date', '')),
                    'scraped_at': datetime.now().isoformat()
                })
        
        # Display source summary
        print(f"\n📈 Per-source breakdown:")
        total_urls = 0
        for source, count in sorted(sources_summary.items(), key=lambda x: x[1], reverse=True):
            print(f"   {source:<20}: {count:3d} articles")
            total_urls += count
        
        # Step 2: Save URLs to JSON file
        print(f"\n💾 STEP 2: Saving URLs to JSON File")
        print("-" * 50)
        
        # Create comprehensive data structure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scraped_urls_from_active_newspapers_{timestamp}.json"
        filepath = f"/home/bs01127/IMLI-Project/{filename}"
        
        # Prepare complete data
        output_data = {
            "extraction_info": {
                "extraction_method": "active_newspapers_scraping",
                "total_urls": total_urls,
                "extraction_date": datetime.now().isoformat(),
                "sources_count": sources_summary,
                "total_sources": len(sources_summary),
                "active_newspapers": list(sources_summary.keys())
            },
            "urls_by_source": urls_by_source,
            "all_urls": []
        }
        
        # Flatten all URLs into a single list for easy access
        for source, source_urls in urls_by_source.items():
            for url_data in source_urls:
                url_data['source'] = source  # Ensure source is included
                output_data["all_urls"].append(url_data)
        
        # Save to JSON file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ URLs saved to: {filename}")
            print(f"   File path: {filepath}")
            print(f"   Total URLs: {len(output_data['all_urls'])}")
            
            # Create simple text file for easy viewing
            txt_filename = f"simple_urls_from_active_newspapers_{timestamp}.txt"
            txt_filepath = f"/home/bs01127/IMLI-Project/{txt_filename}"
            
            with open(txt_filepath, 'w', encoding='utf-8') as f:
                for url_data in output_data["all_urls"]:
                    f.write(f"{url_data['url']}\n")
            
            print(f"✅ Simple URLs saved to: {txt_filename}")
            
            return filepath, len(output_data['all_urls'])
            
        except Exception as e:
            print(f"❌ Error saving URLs: {e}")
            return None, 0
    
    except Exception as e:
        print(f"❌ Error in main process: {e}")
        import traceback
        traceback.print_exc()
        return None, 0

def display_final_summary(filepath, total_urls):
    """Display final summary of the process"""
    
    print(f"\n🎉 PROCESS COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print(f"📄 JSON file created: {os.path.basename(filepath) if filepath else 'None'}")
    print(f"🔗 Total URLs extracted: {total_urls}")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if filepath and os.path.exists(filepath):
        file_size = os.path.getsize(filepath)
        print(f"📦 File size: {file_size:,} bytes")
        
        # Show file content preview
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            print(f"\n📊 File Content Summary:")
            print(f"   Sources: {data['extraction_info']['total_sources']}")
            print(f"   Active newspapers: {', '.join(data['extraction_info']['active_newspapers'])}")
            
            # Show sample URLs from each source
            print(f"\n🔍 Sample URLs by Source:")
            for source, urls in data['urls_by_source'].items():
                print(f"   {source} ({len(urls)} URLs):")
                for i, url_data in enumerate(urls[:2], 1):  # Show first 2 URLs
                    print(f"     {i}. {url_data['url']}")
                    print(f"        Title: {url_data['title'][:50]}...")
                if len(urls) > 2:
                    print(f"     ... and {len(urls)-2} more URLs")
                print()
        
        except Exception as e:
            print(f"⚠️  Could not read file content: {e}")

def main():
    """Main execution function"""
    print("🔥 Active Newspapers URL Extraction Tool")
    print("=" * 50)
    print("This tool will:")
    print("1. Scrape all active Bengali newspapers") 
    print("2. Extract all URLs to a comprehensive JSON file")
    print("3. Create a simple text file with just URLs")
    print()
    
    # Execute the main process
    filepath, total_urls = collect_scraped_urls_and_save()
    
    # Display final summary
    display_final_summary(filepath, total_urls)
    
    if filepath:
        print(f"\n✨ Success! Check these files:")
        print(f"   📄 Complete data: {os.path.basename(filepath)}")
        print(f"   📝 Simple URLs: simple_urls_from_active_newspapers_*.txt")
    else:
        print(f"\n❌ Process failed. Check error messages above.")

if __name__ == "__main__":
    main()
