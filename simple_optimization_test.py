#!/usr/bin/env python3
"""
Simple test to verify the optimized scraper works
"""

import sys
import os
sys.path.insert(0, '.')

def main():
    try:
        print("🧪 Testing Optimized Reddit Scraper")
        
        from enhanced_reddit_category_scraper import EnhancedRedditCategoryScraper
        scraper = EnhancedRedditCategoryScraper()
        
        print("✅ Scraper initialized successfully")
        
        # Test text cleaning
        test_text = "Hello 👋 world!   Extra   spaces   and\n\nnewlines 🔥"
        cleaned = scraper.clean_text_for_llm(test_text)
        print(f"Text cleaning test:")
        print(f"  Before: '{test_text}'")
        print(f"  After:  '{cleaned}'")
        
        # Show categories
        print(f"\n📂 Categories ({len(scraper.subreddit_categories)}):")
        for key, info in scraper.subreddit_categories.items():
            print(f"   {info['name']} ({key}): {len(info['subreddits'])} subreddits")
        
        print(f"\n⚡ Key Optimizations:")
        print(f"   • Full title + content (no truncation)")
        print(f"   • Top 10 comments only")
        print(f"   • Emoji & whitespace removal")
        print(f"   • Shortened prompts")
        print(f"   • max_tokens: 400 (reduced from 800)")
        
        print(f"\n🎯 Ready for category-wise analysis with token optimization!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
