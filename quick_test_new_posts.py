#!/usr/bin/env python3
"""
Quick test for Reddit Data Scrapping with New Posts
"""

import sys
import os
sys.path.insert(0, '.')

from reddit_data_scrapping import RedditDataScrapper

def quick_test():
    """Quick test of the Reddit scrapper with new posts"""
    print("🧪 Quick Test: Reddit Data Scrapping (New Posts)")
    print("=" * 60)
    
    try:
        # Initialize scraper
        print("📝 Initializing scraper...")
        scraper = RedditDataScrapper()
        print("✅ Scraper initialized successfully")
        
        # Test with very limited data for speed
        print("\n📝 Running quick analysis (2 posts per subreddit)...")
        results = scraper.run_comprehensive_analysis(posts_per_subreddit=2)
        
        if results.get('summary', {}).get('status') == 'success':
            print("✅ Quick analysis completed successfully!")
            
            # Show key results
            summary = results.get('summary', {})
            print(f"\n📊 Quick Summary:")
            print(f"   Subreddits: {summary.get('successful_subreddits', 0)}")
            print(f"   Posts: {summary.get('total_posts', 0)}")
            print(f"   LLM Responses: {summary.get('successful_llm_responses', 0)}")
            
            # Show consolidated trending words
            consolidated = results.get('consolidated_trending_words', [])
            if consolidated:
                print(f"\n🔥 Top Trending Words:")
                for i, word in enumerate(consolidated[:5], 1):
                    print(f"   {i}. {word}")
            
            # Show LLM responses
            llm_responses = results.get('llm_responses', [])
            if llm_responses:
                print(f"\n🤖 LLM Response Sample:")
                for response in llm_responses[:2]:  # Show first 2 responses
                    if response['status'] == 'success':
                        print(f"\n   📝 Response #{response['response_number']}:")
                        for i, word in enumerate(response['trending_words'], 1):
                            print(f"      {i}. {word}")
                            
        else:
            print(f"❌ Quick analysis failed: {results.get('summary', {}).get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_test()
