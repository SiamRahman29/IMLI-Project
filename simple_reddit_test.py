#!/usr/bin/env python3
"""
Simple Reddit Test - Quick verification
"""

import os
import sys
from dotenv import load_dotenv

def test_env_loading():
    """Test environment variable loading"""
    print("🔧 Testing environment variables...")
    
    # Load environment
    load_dotenv()
    
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT')
    
    print(f"   Client ID: {'✅ Found' if client_id else '❌ Missing'}")
    print(f"   Client Secret: {'✅ Found' if client_secret else '❌ Missing'}")
    print(f"   User Agent: {'✅ Found' if user_agent else '❌ Missing'}")
    
    if client_id:
        print(f"   Client ID (partial): {client_id[:10]}...")
    
    return bool(client_id and client_secret and user_agent)

def test_reddit_import():
    """Test Reddit module imports"""
    print("\n📦 Testing Reddit imports...")
    
    try:
        import praw
        print("   ✅ PRAW imported successfully")
        
        import requests
        print("   ✅ Requests imported successfully")
        
        return True
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False

def test_basic_reddit_connection():
    """Test basic Reddit API connection"""
    print("\n🌐 Testing Reddit API connection...")
    
    try:
        import praw
        from dotenv import load_dotenv
        
        load_dotenv()
        
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT')
        
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        print("   ✅ Reddit client created successfully")
        
        # Test basic API call
        print("   🔍 Testing basic subreddit access...")
        subreddit = reddit.subreddit('test')
        print(f"   ✅ Subreddit access successful: r/{subreddit.display_name}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Reddit connection error: {e}")
        return False

def test_bangladesh_subreddit():
    """Test Bangladesh subreddit access"""
    print("\n🇧🇩 Testing Bangladesh subreddit access...")
    
    try:
        import praw
        from dotenv import load_dotenv
        
        load_dotenv()
        
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )
        
        # Test Bangladesh subreddit
        bangladesh = reddit.subreddit('bangladesh')
        print(f"   ✅ r/bangladesh access successful")
        print(f"   📊 Subscribers: {bangladesh.subscribers}")
        
        # Get one post for testing
        posts = list(bangladesh.hot(limit=1))
        if posts:
            post = posts[0]
            print(f"   📄 Sample post: {post.title[:50]}...")
            print(f"   📈 Score: {post.score}")
            return True
        else:
            print("   ⚠️ No posts found")
            return False
            
    except Exception as e:
        print(f"   ❌ Bangladesh subreddit error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Simple Reddit API Test")
    print("=" * 40)
    
    # Test 1: Environment variables
    env_ok = test_env_loading()
    if not env_ok:
        print("\n❌ Environment setup failed")
        return
    
    # Test 2: Imports
    import_ok = test_reddit_import()
    if not import_ok:
        print("\n❌ Import setup failed")
        return
    
    # Test 3: Basic connection
    connection_ok = test_basic_reddit_connection()
    if not connection_ok:
        print("\n❌ Reddit connection failed")
        return
    
    # Test 4: Bangladesh subreddit
    bangladesh_ok = test_bangladesh_subreddit()
    
    print("\n" + "=" * 40)
    if bangladesh_ok:
        print("✅ All tests passed! Reddit integration ready.")
    else:
        print("⚠️ Basic connection works, but Bangladesh subreddit had issues.")

if __name__ == "__main__":
    main()
