#!/usr/bin/env python3
"""
Complete Reddit Posts Test - Save ALL posts
Tests Reddit scraping and saves all retrieved posts to JSON
"""

import sys
import os
sys.path.insert(0, '.')

from app.services.reddit_scraper import RedditScraper
import json
from datetime import datetime

def test_save_all_reddit_posts():
    """Test Reddit scraping and save ALL posts"""
    
    print("🔥 Reddit Complete Posts Test")
    print("=" * 50)
    
    try:
        # Initialize scraper
        scraper = RedditScraper()
        print("✅ Reddit scraper initialized")
        
        # Test with medium limits to get good coverage but not too slow
        print("\n🌐 Scraping all Bangladesh subreddits...")
        all_posts = scraper.scrape_all_bangladesh_subreddits_praw(limit_per_subreddit=15)
        
        print(f"✅ Total posts collected: {len(all_posts)}")
        
        # Show subreddit breakdown
        subreddit_counts = {}
        for post in all_posts:
            source = post['source']
            subreddit_counts[source] = subreddit_counts.get(source, 0) + 1
        
        print(f"\n📊 Posts by subreddit:")
        for subreddit, count in subreddit_counts.items():
            print(f"   {subreddit}: {count} posts")
        
        # Save ALL posts to JSON
        output_file = f'reddit_all_posts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'total_posts': len(all_posts),
            'subreddit_breakdown': subreddit_counts,
            'all_posts': all_posts  # Save ALL posts, not just sample
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 ALL {len(all_posts)} posts saved to: {output_file}")
        
        # Show some sample posts
        print(f"\n📋 Sample posts preview:")
        for i, post in enumerate(all_posts[:3], 1):
            print(f"   {i}. {post['title'][:60]}...")
            print(f"      Source: {post['source']} | Score: {post['score']}")
        
        # Content analysis
        bengali_posts = 0
        english_posts = 0
        for post in all_posts:
            content = f"{post.get('title', '')} {post.get('content', '')}"
            if any('\u0980' <= char <= '\u09FF' for char in content):
                bengali_posts += 1
            else:
                english_posts += 1
        
        print(f"\n📈 Content Analysis:")
        print(f"   Bengali content posts: {bengali_posts}")
        print(f"   English content posts: {english_posts}")
        
        print(f"\n✅ Complete Reddit test successful!")
        print(f"📁 File: {output_file}")
        print(f"📊 Total posts saved: {len(all_posts)}")
        
        return output_file, len(all_posts)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, 0

if __name__ == "__main__":
    test_save_all_reddit_posts()
