#!/usr/bin/env python3
"""
Complete Reddit Scraping to LLM Response Test
এই file run করলে:
1. Reddit data scrape করবে
2. Flair-wise categorization করবে  
3. Each flair এর জন্য LLM response পাবে
4. 2টি trending topic per flair output দিবে
"""

import sys
import os
import json
import time
import logging
from datetime import datetime
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

def complete_reddit_to_llm_test():
    """Complete test: Reddit scraping → Processing → LLM Response"""
    
    print("🚀 COMPLETE REDDIT TO LLM RESPONSE TEST")
    print("=" * 60)
    print("📋 Process Flow:")
    print("   1. ✅ Reddit Data Scraping")
    print("   2. ✅ Emoji Removal & Flair Categorization") 
    print("   3. ✅ Individual LLM Requests per Flair")
    print("   4. ✅ 2 Trending Topics per Flair Output")
    print("=" * 60)
    
    # Step 1: Reddit Data Scraping
    print(f"\n🔍 STEP 1: Reddit Data Scraping")
    print("-" * 40)
    
    try:
        from app.services.reddit_scraper import RedditScraper
        
        print("🤖 Initializing Reddit scraper...")
        scraper = RedditScraper()
        
        print("📡 Scraping Reddit posts from Bangladesh-related subreddits...")
        scraped_posts = scraper.scrape_all_bangladesh_subreddits_praw()
        
        if not scraped_posts:
            print("❌ No posts scraped! Using fallback test data...")
            # Fallback to existing data
            with open('reddit_all_posts_20250624_132233.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            scraped_posts = data.get('all_posts', [])
        
        print(f"✅ Successfully loaded {len(scraped_posts)} Reddit posts")
        
    except Exception as e:
        print(f"⚠️ Reddit scraping failed: {e}")
        print("📂 Using existing test data as fallback...")
        try:
            with open('reddit_all_posts_20250624_132233.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            scraped_posts = data.get('all_posts', [])
            print(f"✅ Loaded {len(scraped_posts)} posts from test file")
        except Exception as fallback_error:
            print(f"❌ Fallback failed: {fallback_error}")
            return
    
    # Step 2: Processing & Categorization
    print(f"\n🏷️ STEP 2: Processing & Flair Categorization")
    print("-" * 40)
    
    try:
        from app.services.reddit_integration import RedditIntegration
        
        print("🔧 Initializing Reddit integration...")
        reddit_integration = RedditIntegration()
        
        print("🧹 Removing emojis and categorizing by flair...")
        categorized_data = reddit_integration.categorize_by_flair(scraped_posts)
        
        print(f"📊 Categorization Results:")
        valid_flairs = []
        for flair, posts in categorized_data.items():
            if posts and flair != 'uncategorized':
                valid_flairs.append(flair)
                print(f"   ✅ {flair}: {len(posts)} posts")
            elif flair == 'uncategorized':
                print(f"   ⚪ {flair}: {len(posts)} posts (will skip)")
        
        print(f"🎯 Found {len(valid_flairs)} flairs with posts for LLM analysis")
        
    except Exception as e:
        print(f"❌ Categorization failed: {e}")
        return
    
    # Step 3: LLM Analysis per Flair
    print(f"\n🤖 STEP 3: LLM Analysis per Flair")
    print("-" * 40)
    
    try:
        from app.services.reddit_flair_trending import RedditFlairTrendingAnalyzer
        
        print("🧠 Initializing flair trending analyzer...")
        analyzer = RedditFlairTrendingAnalyzer()
        
        print(f"📤 Sending individual LLM requests for {len(valid_flairs)} flairs...")
        print("⏳ This will take some time due to rate limiting (3s between requests)...")
        
        start_time = time.time()
        llm_results = analyzer.analyze_flair_wise_trending(categorized_data)
        end_time = time.time()
        
        print(f"⏱️ LLM analysis completed in {end_time - start_time:.2f} seconds")
        print(f"✅ Overall success: {llm_results['success']}")
        print(f"📊 Flairs processed: {llm_results['total_flairs_processed']}")
        print(f"🔢 Total topics generated: {llm_results['total_topics_found']}")
        
    except Exception as e:
        print(f"❌ LLM analysis failed: {e}")
        return
    
    # Step 4: Output Results
    print(f"\n🔥 STEP 4: LLM RESPONSE OUTPUT")
    print("=" * 60)
    
    if llm_results['success'] and llm_results['total_topics_found'] > 0:
        
        print(f"🎉 SUCCESS! Generated {llm_results['total_topics_found']} trending topics")
        print(f"📋 Processing Summary: {llm_results['message']}")
        
        print(f"\n📊 TRENDING TOPICS BY FLAIR:")
        print("=" * 50)
        
        for flair_name, flair_result in llm_results.get('individual_flair_results', {}).items():
            print(f"\n🏷️ {flair_name.upper()}")
            print(f"   📊 Posts analyzed: {flair_result['posts_count']}")
            print(f"   ✅ Success: {flair_result['success']}")
            print(f"   ⏰ Processed at: {flair_result['processed_at']}")
            
            if flair_result['success'] and flair_result['trending_topics']:
                print(f"   🔥 TRENDING TOPICS:")
                for i, topic in enumerate(flair_result['trending_topics'], 1):
                    print(f"      {i}. {topic}")
            else:
                error_msg = flair_result.get('error', 'Unknown error')
                print(f"   ❌ Failed: {error_msg}")
            
            print(f"   {'-' * 45}")
        
        # Success Statistics
        successful_flairs = [f for f in llm_results['individual_flair_results'].values() if f['success']]
        failed_flairs = [f for f in llm_results['individual_flair_results'].values() if not f['success']]
        
        print(f"\n📈 SUCCESS STATISTICS:")
        print("=" * 30)
        print(f"✅ Successful flairs: {len(successful_flairs)}")
        print(f"❌ Failed flairs: {len(failed_flairs)}")
        print(f"📊 Success rate: {len(successful_flairs)/len(llm_results['individual_flair_results'])*100:.1f}%")
        print(f"🔢 Topics per successful flair: {llm_results['total_topics_found']/len(successful_flairs):.1f} average" if successful_flairs else "N/A")
        
        # Save results
        print(f"\n💾 SAVING RESULTS:")
        filename = analyzer.save_flair_analysis_results(llm_results)
        print(f"✅ Detailed results saved to: {filename}")
        
        # Summary for easy copy-paste
        print(f"\n📋 QUICK SUMMARY (Copy-Paste Ready):")
        print("=" * 40)
        print(f"Reddit Posts Scraped: {len(scraped_posts)}")
        print(f"Flairs with Posts: {len(valid_flairs)}")
        print(f"LLM Analysis Success: {len(successful_flairs)}/{len(llm_results['individual_flair_results'])}")
        print(f"Total Trending Topics: {llm_results['total_topics_found']}")
        
        print(f"\nFlair-wise Topics:")
        for flair_result in successful_flairs:
            topics_str = ", ".join(flair_result['trending_topics'])
            print(f"  {flair_result['flair_name']}: {topics_str}")
        
    else:
        print("❌ LLM analysis was not successful")
        print(f"Error: {llm_results.get('message', 'Unknown error')}")
    
    print(f"\n🎉 COMPLETE TEST FINISHED!")
    print("=" * 40)

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run complete test
    complete_reddit_to_llm_test()
