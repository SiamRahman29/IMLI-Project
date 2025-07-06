#!/usr/bin/env python3
"""
Automatic Reddit Category Scraper Test (bypasses user input)
"""

import sys
import os
sys.path.insert(0, '.')

import json
import time
from datetime import datetime
from enhanced_reddit_category_scraper import EnhancedRedditCategoryScraper

def calculate_tokens(text):
    """Calculate approximate token count (1 token = 3 characters)"""
    return len(text) / 3

def auto_test_reddit_scraper():
    """Automatic test without user input"""
    
    print("🚀 REDDIT CATEGORY SCRAPER AUTO TEST")
    print("=" * 60)
    print("📊 Token Management: 10,000 tokens/min (~30,000 chars)")
    print("🧹 Text Cleaning: Emoji + Whitespace removal enabled")
    print("🔄 Auto mode: Running full test automatically")
    print("=" * 60)
    
    try:
        # Initialize scraper
        scraper = EnhancedRedditCategoryScraper()
        print("✅ Enhanced Reddit scraper initialized")
        
        # Process categories one by one with token tracking
        total_tokens_used = 0
        start_time = time.time()
        successful_categories = 0
        failed_categories = 0
        
        print(f"\n📂 PROCESSING {len(scraper.subreddit_categories)} CATEGORIES:")
        
        for category_key, category_info in scraper.subreddit_categories.items():
            category_name = category_info['name']
            subreddits = category_info['subreddits']
            
            print(f"\n" + "-" * 60)
            print(f"🏷️  CATEGORY: {category_name} ({category_key})")
            print(f"📡 Subreddits: {', '.join(subreddits)}")
            print("-" * 60)
            
            try:
                # Step 1: Scrape category content (minimal posts for testing)
                print(f"📡 Scraping subreddits...")
                category_posts = scraper.scrape_category_content(
                    category=category_key,
                    subreddits=subreddits,
                    posts_per_subreddit=3  # Small number for testing
                )
                
                if not category_posts:
                    print(f"⚠️  No posts found for {category_name}, skipping...")
                    failed_categories += 1
                    continue
                
                print(f"📄 Found {len(category_posts)} posts")
                
                # Step 2: Prepare content for LLM with token tracking
                print(f"🔧 Preparing content for LLM...")
                content_text = scraper.prepare_category_content_for_llm(category_posts, category_key)
                content_tokens = calculate_tokens(content_text)
                
                print(f"📊 Content prepared: {len(content_text)} chars (~{content_tokens:.0f} tokens)")
                
                # Step 3: Create optimized prompt
                prompt = scraper.create_category_llm_prompt(
                    content=content_text,
                    category=category_key,
                    category_name=category_name,
                    response_number=1
                )
                prompt_tokens = calculate_tokens(prompt)
                
                print(f"📝 Prompt created: {len(prompt)} chars (~{prompt_tokens:.0f} tokens)")
                
                # Check token limit before proceeding
                estimated_total_tokens = prompt_tokens + 400  # 400 max response tokens
                
                # Token rate limiting check
                elapsed_time = time.time() - start_time
                if elapsed_time < 60:  # Within 1 minute
                    if total_tokens_used + estimated_total_tokens > 10000:
                        wait_time = 60 - elapsed_time + 5  # Wait until next minute + buffer
                        print(f"⏰ Token limit reached ({total_tokens_used + estimated_total_tokens:.0f}/10000)")
                        print(f"⏳ Waiting {wait_time:.1f} seconds for rate limit reset...")
                        time.sleep(wait_time)
                        start_time = time.time()
                        total_tokens_used = 0
                else:
                    # Reset counter after 1 minute
                    start_time = time.time()
                    total_tokens_used = 0
                
                # Step 4: Get LLM response
                print(f"🤖 Getting LLM response...")
                llm_response = scraper.call_groq_llm_for_category_analysis(
                    prompt=prompt,
                    category=category_key,
                    response_number=1
                )
                
                # Update token usage
                total_tokens_used += estimated_total_tokens
                
                if llm_response:
                    # Parse trending words
                    trending_words = scraper.parse_llm_response(llm_response)
                    
                    print(f"✅ LLM Response received!")
                    print(f"📊 Token usage: +{estimated_total_tokens:.0f} (Total: {total_tokens_used:.0f}/10000)")
                    
                    # Display results
                    print(f"\n🔥 TRENDING WORDS FOR {category_name}:")
                    if trending_words:
                        for i, word in enumerate(trending_words, 1):
                            print(f"   {i}. {word}")
                    else:
                        print("   (No trending words extracted)")
                    
                    print(f"\n📋 RAW LLM RESPONSE:")
                    print(f"   \"{llm_response}\"")
                    
                    successful_categories += 1
                    
                else:
                    print(f"❌ LLM response failed for {category_name}")
                    failed_categories += 1
                
                # Short delay between categories
                time.sleep(3)
                
            except Exception as cat_error:
                print(f"❌ Error processing category {category_name}: {cat_error}")
                failed_categories += 1
                continue
        
        print(f"\n" + "=" * 60)
        print(f"🎉 AUTO TEST COMPLETED!")
        print(f"📊 Results:")
        print(f"   ✅ Successful categories: {successful_categories}")
        print(f"   ❌ Failed categories: {failed_categories}")
        print(f"   📈 Success rate: {(successful_categories / len(scraper.subreddit_categories) * 100):.1f}%")
        print(f"📊 Token usage: {total_tokens_used}/10000")
        print(f"⏱️  Total time: {time.time() - start_time:.1f} seconds")
        print("=" * 60)
        
        return successful_categories > 0
        
    except Exception as e:
        print(f"\n❌ Auto test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = auto_test_reddit_scraper()
    print(f"\n{'✅ Auto test completed successfully!' if success else '❌ Auto test failed!'}")
