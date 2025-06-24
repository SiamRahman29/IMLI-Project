#!/usr/bin/env python3
"""
Quick test for the updated comprehensive Reddit data scrapper
"""

import sys
import os
sys.path.insert(0, '.')

from reddit_data_scrapping import RedditDataScrapper

def quick_test_updated_scrapper():
    """Quick test with the updated token limits"""
    print("🧪 TESTING UPDATED REDDIT COMPREHENSIVE SCRAPPER")
    print("=" * 60)
    print("📊 Updates:")
    print("   - Posts per analysis: 30 → 50")
    print("   - Content length: 500 → 800 chars")
    print("   - Comments per post: 5 → 8")
    print("   - Comment length: 200 → 300 chars")
    print("   - Total content limit: 30K → 50K chars")
    print("   - LLM max_tokens: 500 → 800")
    print("=" * 60)
    
    try:
        # Initialize scraper
        print("\n📝 Step 1: Initializing scraper...")
        scraper = RedditDataScrapper()
        print("✅ Scraper initialized successfully")
        
        # Test scraping only (no LLM for quick test)
        print("\n📝 Step 2: Testing scraping with updated limits...")
        all_posts = scraper.scrape_all_subreddits(posts_per_subreddit=3)
        
        if all_posts:
            print(f"✅ Scraping successful: {len(all_posts)} posts")
            
            # Test content preparation
            print("\n📝 Step 3: Testing content preparation...")
            content_text = scraper.prepare_comprehensive_content_for_llm(all_posts)
            
            if content_text:
                print(f"✅ Content preparation successful: {len(content_text)} characters")
                print(f"📊 Token estimate: ~{len(content_text) // 3.5:.0f} tokens")
                
                # Test prompt creation
                print("\n📝 Step 4: Testing prompt creation...")
                prompt = scraper.create_comprehensive_llm_prompt(content_text)
                print(f"✅ Prompt created: {len(prompt)} characters")
                print(f"📊 Total prompt tokens: ~{len(prompt) // 3.5:.0f} tokens")
                
                print("\n🎯 Ready for LLM analysis with increased token limits!")
                print("💡 Run the full analysis with: python reddit_data_scrapping.py")
                
            else:
                print("❌ Content preparation failed")
        else:
            print("❌ Scraping failed")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_test_updated_scrapper()
