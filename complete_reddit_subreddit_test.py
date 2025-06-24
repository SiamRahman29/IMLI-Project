#!/usr/bin/env python3
"""
Complete Reddit Subreddit-wise Scrape to LLM Test
Tests: Reddit scraping → Subreddit categorization → Individual LLM analysis → Bengali trending topics
"""

import json
import logging
import sys
from datetime import datetime

def main():
    """Test complete Reddit subreddit-wise pipeline"""
    print("🚀 COMPLETE REDDIT SUBREDDIT-WISE TO LLM TEST")
    print("=" * 60)
    print("📋 Process Flow:")
    print("   1. ✅ Reddit Data Scraping")
    print("   2. ✅ Subreddit-wise Categorization")
    print("   3. ✅ Individual LLM Requests per Subreddit")
    print("   4. ✅ 2 Trending Topics per Subreddit Output")
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
            print(f"✅ Loaded {len(scraped_posts)} posts from fallback data")
        except Exception as fallback_error:
            print(f"❌ Fallback failed: {fallback_error}")
            return
    
    # Step 2: Subreddit-wise Processing
    print(f"\n🏷️ STEP 2: Subreddit-wise Categorization")
    print("-" * 40)
    
    try:
        from app.services.reddit_subreddit_trending import RedditSubredditTrendingAnalyzer
        
        print("🔧 Initializing Reddit subreddit analyzer...")
        analyzer = RedditSubredditTrendingAnalyzer()
        
        print("📊 Categorizing posts by subreddit...")
        categorized_data = analyzer.categorize_posts_by_subreddit(scraped_posts)
        
        print(f"📊 Subreddit Categorization Results:")
        total_subreddits_with_posts = 0
        for subreddit, posts_list in categorized_data.items():
            if subreddit != 'uncategorized':
                subreddit_info = analyzer.subreddit_categories.get(subreddit, {})
                category = subreddit_info.get('category', subreddit)
                print(f"   ✅ r/{subreddit} ({category}): {len(posts_list)} posts")
                total_subreddits_with_posts += 1
            else:
                print(f"   ⚪ {subreddit}: {len(posts_list)} posts (will skip)")
        
        print(f"🎯 Found {total_subreddits_with_posts} subreddits with posts for LLM analysis")
        
    except Exception as e:
        print(f"❌ Subreddit categorization failed: {e}")
        return
    
    # Step 3: LLM Analysis per Subreddit
    print(f"\n🤖 STEP 3: LLM Analysis per Subreddit")
    print("-" * 40)
    
    try:
        print("🧠 Starting subreddit-wise trending analysis...")
        print(f"📤 Sending individual LLM requests for {total_subreddits_with_posts} subreddits...")
        print("⏳ This will take some time due to rate limiting (3s between requests)...")
        
        # Start timing
        start_time = datetime.now()
        
        # Analyze subreddit-wise trending
        results = analyzer.analyze_subreddit_wise_trending(scraped_posts)
        
        # End timing
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"⏱️ LLM analysis completed in {duration:.2f} seconds")
        print(f"✅ Overall success: {results['success']}")
        print(f"📊 Subreddits processed: {results['total_subreddits_processed']}")
        print(f"🔢 Total topics generated: {results['total_topics_found']}")
        
    except Exception as e:
        print(f"❌ LLM analysis failed: {e}")
        return
    
    # Step 4: Display Results
    print(f"\n🔥 STEP 4: LLM RESPONSE OUTPUT")
    print("=" * 60)
    
    if results['success']:
        print(f"🎉 SUCCESS! Generated {results['total_topics_found']} trending topics")
        print(f"📋 Processing Summary: {results['message']}")
        
        print(f"\n📊 TRENDING TOPICS BY SUBREDDIT:")
        print("=" * 50)
        
        for subreddit, analysis in results['subreddit_analysis'].items():
            print(f"\n🏷️ r/{subreddit.upper()} - {analysis['category']}")
            print(f"   📊 Posts analyzed: {analysis['posts_count']}")
            print(f"   ✅ Success: {analysis['success']}")
            
            # Get individual result for timestamp
            individual_result = results['individual_subreddit_results'].get(subreddit, {})
            processed_at = individual_result.get('processed_at', 'Unknown')
            print(f"   ⏰ Processed at: {processed_at}")
            
            print(f"   🔥 TRENDING TOPICS:")
            if analysis['trending_topics']:
                for i, topic in enumerate(analysis['trending_topics'], 1):
                    print(f"      {i}. {topic}")
            else:
                print(f"      ❌ No topics found")
            print("   " + "-" * 45)
        
        # Success Statistics
        successful_subreddits = len([s for s in results['individual_subreddit_results'].values() if s['success']])
        failed_subreddits = results['total_subreddits_processed'] - successful_subreddits
        success_rate = (successful_subreddits / results['total_subreddits_processed'] * 100) if results['total_subreddits_processed'] > 0 else 0
        avg_topics = results['total_topics_found'] / successful_subreddits if successful_subreddits > 0 else 0
        
        print(f"\n📈 SUCCESS STATISTICS:")
        print("=" * 30)
        print(f"✅ Successful subreddits: {successful_subreddits}")
        print(f"❌ Failed subreddits: {failed_subreddits}")
        print(f"📊 Success rate: {success_rate:.1f}%")
        print(f"🔢 Topics per successful subreddit: {avg_topics:.1f} average")
        
        # Save Results
        print(f"\n💾 SAVING RESULTS:")
        filename = analyzer.save_subreddit_analysis_results(results)
        print(f"✅ Detailed results saved to: {filename}")
        
        # Quick Summary
        print(f"\n📋 QUICK SUMMARY (Copy-Paste Ready):")
        print("=" * 40)
        print(f"Reddit Posts Scraped: {len(scraped_posts)}")
        print(f"Subreddits with Posts: {total_subreddits_with_posts}")
        print(f"LLM Analysis Success: {successful_subreddits}/{results['total_subreddits_processed']}")
        print(f"Total Trending Topics: {results['total_topics_found']}")
        print()
        print("Subreddit-wise Topics:")
        for subreddit, analysis in results['subreddit_analysis'].items():
            if analysis['trending_topics']:
                topics_str = ', '.join(analysis['trending_topics'])
                print(f"  r/{subreddit}: {topics_str}")
        
    else:
        print(f"❌ FAILED! {results.get('message', 'Unknown error')}")
    
    print(f"\n🎉 COMPLETE SUBREDDIT-WISE TEST FINISHED!")
    print("=" * 40)

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    main()
