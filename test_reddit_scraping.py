#!/usr/bin/env python3
"""
Standalone Reddit Scraper Test
Test Reddit API integration without running the full pipeline
"""

import sys
import os
sys.path.insert(0, '.')

from app.services.reddit_scraper import RedditScraper
from datetime import datetime
import json

def test_reddit_scraping():
    """Test Reddit scraping functionality"""
    
    print("🔴 Reddit Scraper Test Started")
    print("=" * 60)
    
    # Check if .env file exists
    env_file = '.env'
    if not os.path.exists(env_file):
        print(f"❌ .env file not found!")
        print(f"   Please create a .env file with your Reddit API credentials:")
        print(f"   REDDIT_CLIENT_ID=your_client_id")
        print(f"   REDDIT_CLIENT_SECRET=your_client_secret")
        print(f"   REDDIT_USER_AGENT=BangladeshTrendingAnalyzer/1.0")
        print(f"\n   Get credentials from: https://www.reddit.com/prefs/apps")
        return
    
    try:
        # Initialize Reddit scraper
        print("🔧 Initializing Reddit scraper...")
        scraper = RedditScraper()
        print("✅ Reddit scraper initialized successfully")
        
        # Test single subreddit scraping
        print("\n📊 Testing single subreddit scraping (r/bangladesh)...")
        posts = scraper.scrape_posts_with_praw('bangladesh', limit=5)
        
        print(f"✅ Retrieved {len(posts)} posts from r/bangladesh")
        
        if posts:
            print("\n📋 Sample post details:")
            sample_post = posts[0]
            print(f"   Title: {sample_post.title[:80]}...")
            print(f"   Author: {sample_post.author}")
            print(f"   Score: {sample_post.score}")
            print(f"   Comments: {sample_post.num_comments}")
            print(f"   Created: {datetime.fromtimestamp(sample_post.created_utc)}")
            print(f"   URL: {sample_post.permalink}")
            
            if sample_post.content:
                print(f"   Content: {sample_post.content[:100]}...")
            
            if sample_post.comments:
                print(f"   Top Comment: {sample_post.comments[0][:80]}...")
        
        # Test multiple subreddits
        print(f"\n🌐 Testing multiple Bangladesh subreddits (getting all available posts)...")
        all_posts = scraper.scrape_all_bangladesh_subreddits_praw(limit_per_subreddit=25)
        
        print(f"✅ Total posts from all subreddits: {len(all_posts)}")
        
        # Show subreddit breakdown
        subreddit_counts = {}
        for post in all_posts:
            source = post['source']
            subreddit_counts[source] = subreddit_counts.get(source, 0) + 1
        
        print(f"\n📈 Posts by subreddit:")
        for subreddit, count in subreddit_counts.items():
            print(f"   {subreddit}: {count} posts")
        
        # Save ALL data to file for inspection
        sample_file = 'reddit_scraping_test_output.json'
        sample_data = {
            'timestamp': datetime.now().isoformat(),
            'total_posts': len(all_posts),
            'subreddit_breakdown': subreddit_counts,
            'all_posts': all_posts  # Save ALL posts
        }
        
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 Sample data saved to: {sample_file}")
        
        # Show content quality check
        print(f"\n🔍 Content Quality Analysis:")
        bengali_posts = 0
        english_posts = 0
        
        for post in all_posts[:10]:  # Check first 10 posts
            title = post.get('title', '')
            content = post.get('content', '')
            full_text = f"{title} {content}"
            
            # Simple check for Bengali characters
            if any('\u0980' <= char <= '\u09FF' for char in full_text):
                bengali_posts += 1
            else:
                english_posts += 1
        
        print(f"   Bengali content posts: {bengali_posts}")
        print(f"   English content posts: {english_posts}")
        
        print(f"\n✅ Reddit scraping test completed successfully!")
        print(f"   Ready for integration with main pipeline")
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print(f"\n   Please check your .env file and Reddit API credentials")
    except Exception as e:
        print(f"❌ Error during Reddit scraping test: {e}")
        print(f"   Check your internet connection and API credentials")

if __name__ == "__main__":
    test_reddit_scraping()
