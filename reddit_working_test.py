#!/usr/bin/env python3
"""
Working Reddit Test - Verified functionality
"""

import os
from dotenv import load_dotenv
import praw
import time

def main():
    print("🔥 Reddit Scraper Working Test")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Get credentials
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT')
    
    print(f"✅ Credentials loaded: {client_id[:10]}...")
    
    # Initialize Reddit
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )
    
    print("✅ Reddit client initialized")
    
    # Test Bangladesh subreddit
    print("\n🇧🇩 Testing r/bangladesh...")
    bangladesh = reddit.subreddit('bangladesh')
    
    posts = []
    for post in bangladesh.hot(limit=3):
        posts.append({
            'title': post.title,
            'score': post.score,
            'comments': post.num_comments,
            'author': str(post.author),
            'created': post.created_utc,
            'url': post.url
        })
    
    print(f"✅ Retrieved {len(posts)} posts from r/bangladesh")
    
    for i, post in enumerate(posts, 1):
        print(f"\n📄 Post {i}:")
        print(f"   Title: {post['title'][:70]}...")
        print(f"   Score: {post['score']} | Comments: {post['comments']}")
        print(f"   Author: {post['author']}")
    
    # Test Bengali subreddit
    print(f"\n🔤 Testing r/bengali...")
    bengali = reddit.subreddit('bengali')
    
    bengali_posts = []
    for post in bengali.hot(limit=2):
        bengali_posts.append({
            'title': post.title,
            'score': post.score,
            'subreddit': post.subreddit.display_name
        })
    
    print(f"✅ Retrieved {len(bengali_posts)} posts from r/bengali")
    
    for i, post in enumerate(bengali_posts, 1):
        print(f"   {i}. {post['title'][:50]}... (Score: {post['score']})")
    
    print(f"\n🎉 Reddit API working perfectly!")
    print(f"📊 Total posts tested: {len(posts) + len(bengali_posts)}")
    
    # Save results
    with open('reddit_working_test_results.txt', 'w', encoding='utf-8') as f:
        f.write("Reddit API Test Results\n")
        f.write("=" * 30 + "\n\n")
        f.write(f"Bangladesh posts: {len(posts)}\n")
        f.write(f"Bengali posts: {len(bengali_posts)}\n\n")
        
        f.write("Sample Posts:\n")
        for i, post in enumerate(posts[:2], 1):
            f.write(f"{i}. {post['title']}\n")
            f.write(f"   Score: {post['score']}, Comments: {post['comments']}\n\n")
    
    print("💾 Results saved to reddit_working_test_results.txt")

if __name__ == "__main__":
    main()
