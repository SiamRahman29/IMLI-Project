#!/usr/bin/env python3
"""
Reddit LLM Integration Test
Tests extracting Bengali trending words from Reddit data using LLM
"""

import sys
import os
sys.path.insert(0, '.')

import json
from dotenv import load_dotenv
from datetime import datetime
import time

# Load environment variables
load_dotenv()

def load_reddit_data():
    """Load Reddit data from the saved JSON file"""
    print("📂 Loading Reddit data...")
    
    # Find the most recent Reddit data file
    reddit_files = [f for f in os.listdir('.') if f.startswith('reddit_all_posts_') and f.endswith('.json')]
    
    if not reddit_files:
        print("❌ No Reddit data files found!")
        print("   Please run test_complete_reddit_posts.py first to generate Reddit data")
        return None
    
    # Get the most recent file
    latest_file = sorted(reddit_files)[-1]
    print(f"📁 Using file: {latest_file}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        posts = data.get('all_posts', [])
        print(f"✅ Loaded {len(posts)} Reddit posts")
        
        return posts
    except Exception as e:
        print(f"❌ Error loading Reddit data: {e}")
        return None

def prepare_reddit_content_for_llm(posts):
    """Prepare Reddit content for LLM analysis with 12000 token limit (~40k characters)"""
    print("🔧 Preparing content for LLM analysis (max 12000 tokens / ~40k characters)...")
    
    # Prioritize posts with higher engagement
    sorted_posts = sorted(posts, key=lambda x: x.get('score', 0) + x.get('comments_count', 0) * 2, reverse=True)
    
    # Take more posts to utilize full token capacity (increased from 30 to 60)
    top_posts = sorted_posts[:60]
    
    # Combine title, content, and comments for each post
    combined_texts = []
    
    for post in top_posts:
        # Get title and content
        title = post.get('title', '').strip()
        content = post.get('content', '').strip()
        
        # Get more comments for better analysis (increased from 3 to 5)
        comments = post.get('comments', [])
        top_comments = comments[:5] if comments else []
        
        # Combine all text with more content for better accuracy
        text_parts = []
        if title:
            text_parts.append(f"Title: {title}")
        if content and len(content) > 10:
            # Increased content length from 200 to 500 chars for more context
            short_content = content[:500] + "..." if len(content) > 500 else content
            text_parts.append(f"Content: {short_content}")
        if top_comments:
            # Increased comment length from 100 to 400 chars each for more context
            short_comments = [comment[:400] + "..." if len(comment) > 400 else comment for comment in top_comments]
            text_parts.append(f"Comments: {' | '.join(short_comments)}")
        
        # Add subreddit context
        subreddit = post.get('source', '').replace('reddit_r_', 'r/')
        if subreddit:
            text_parts.append(f"Source: {subreddit}")
        
        combined_text = " \n".join(text_parts)
        combined_texts.append(combined_text)
        
        # Check estimated token count (roughly 3.5 chars per token for mixed content)
        current_length = len("\n---\n".join(combined_texts))
        estimated_tokens = current_length / 3.5
        
        # Use more of the available token space (increased from 10K to 11K, leaving 1K for prompt)
        if estimated_tokens > 11000:
            print(f"⚠️ Reached token limit, using {len(combined_texts)} posts")
            break
    
    # Join posts with separators
    final_text = "\n" + "\n---\n".join(combined_texts)
    
    print(f"✅ Prepared {len(combined_texts)} top posts for analysis")
    print(f"📊 Total text length: {len(final_text)} characters (~{len(final_text) / 3.5:.0f} tokens)")
    print(f"🔢 Token utilization: {len(final_text) / 3.5 / 12000 * 100:.1f}% of 12K token limit")
    
    return final_text

def create_reddit_trending_llm_prompt(content_text):
    """Create LLM prompt for extracting Bengali trending words from mixed language Reddit content"""
    
    prompt = f"""
তুমি একজন বাংলাদেশি সোশ্যাল মিডিয়া ট্রেন্ড বিশ্লেষক। নিচের Reddit পোস্ট, কন্টেন্ট এবং মন্তব্যগুলো থেকে বর্তমানে সবচেয়ে জনপ্রিয় ও ট্রেন্ডিং বিষয়বস্তু চিহ্নিত করো এবং সেগুলোর জন্য বাংলা শব্দ বা বাক্যাংশ তৈরি করো।

**গুরুত্বপূর্ণ তথ্য:**
- Reddit content এ English, Banglish (রোমান অক্ষরে বাংলা), এবং বাংলা - তিনটি ভাষাই মিশ্রিত অবস্থায় থাকতে পারে
- তুমি সব ভাষার content বুঝতে পারবে কিন্তু response শুধুমাত্র বাংলায় দিতে হবে

**বিশ্লেষণের নিয়মাবলী:**
1. ট্রেন্ডিং বিষয়: সোশ্যাল মিডিয়ায় বর্তমানে জনপ্রিয় বিষয়গুলোতে ফোকাস করো
2. Stop words এড়াও
3. ব্যক্তির নাম নয়: ব্যক্তির নাম বাদ দাও, বিষয়বস্তুর উপর ফোকাস করো
4. একটি টপিক = একটি বাক্যাংশ**: প্রতিটি ট্রেন্ডিং টপিকের জন্য শুধুমাত্র একটি প্রতিনিধিত্বকারী বাংলা শব্দ/বাক্যাংশ দাও
5. সংক্ষিপ্ত বাক্যাংশ: ২-৪ শব্দের মধ্যে সংক্ষিপ্ত ও স্পষ্ট বাংলা বাক্যাংশ দাও
6. আলোচনার ভিত্তি: Reddit এর আলোচনার ভিত্তিতে যেসব বিষয় মানুষ বেশি কথা বলছে সেগুলো চিহ্নিত করো
7. প্রাসঙ্গিকতা: বর্তমান সামাজিক, রাজনৈতিক, অর্থনৈতিক, শিক্ষা, প্রযুক্তি বা সাংস্কৃতিক প্রসঙ্গ বিবেচনা করো

**Reddit বিষয়বস্তু (Mixed Language):**
{content_text}

**আউটপুট ফরম্যাট (শুধুমাত্র বাংলায়):**
Reddit ট্রেন্ডিং শব্দ/বাক্যাংশ (৮টি):
১. [বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
২. [বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
৩. [বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
৪. [বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
৫. [বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
৬. [বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
৭. [বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
৮. [বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
"""
    
    return prompt

def call_groq_llm_for_reddit_analysis(prompt):
    """Call Groq LLM API for Reddit trending analysis"""
    print("🤖 Calling Groq LLM for Reddit trending analysis...")
    
    try:
        from groq import Groq
        
        # Get API key
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("❌ GROQ_API_KEY not found in environment variables!")
            return None
        
        # Initialize Groq client
        client = Groq(api_key=api_key)
        
        print(f"📤 Sending prompt to Groq API...")
        print(f"📊 Prompt length: {len(prompt)} characters")
        
        # Call Groq API with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",  # Updated model with 12K token support
                    messages=[
                        {
                            "role": "system", 
                            "content": "তুমি একজন বিশেষজ্ঞ বাংলা ভাষা বিশ্লেষক এবং সোশ্যাল মিডিয়া ট্রেন্ড গবেষক। তুমি ইংরেজি, বাংলিশ (রোমান অক্ষরে বাংলা) এবং বাংলা - সব ভাষাই বুঝতে পারো কিন্তু response সবসময় বাংলায় দিবে।"
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    temperature=0.3,  # Lower temperature for more focused results
                    max_tokens=1200,  # Increased for better Bengali response
                    top_p=0.9
                )
                
                llm_response = response.choices[0].message.content.strip()
                print(f"✅ Received response from Groq API ({len(llm_response)} characters)")
                
                return llm_response
                
            except Exception as api_error:
                print(f"⚠️ Attempt {attempt + 1} failed: {api_error}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"🔄 Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ All {max_retries} attempts failed")
                    return None
    
    except ImportError:
        print("❌ Groq library not found! Install with: pip install groq")
        return None
    except Exception as e:
        print(f"❌ Error calling Groq API: {e}")
        return None

def parse_llm_response(llm_response):
    """Parse LLM response to extract trending words"""
    print("🔍 Parsing LLM response...")
    
    if not llm_response:
        return []
    
    trending_words = []
    lines = llm_response.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Look for numbered items
        if any(char in line for char in ['১', '২', '৩', '৪', '৫', '৬', '৭', '৮']) or line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.')):
            # Remove numbering
            clean_line = line
            for num in ['১.', '২.', '৩.', '৪.', '৫.', '৬.', '৭.', '৮.', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.']:
                clean_line = clean_line.replace(num, '').strip()
            
            if clean_line and len(clean_line) > 1:
                trending_words.append(clean_line)
    
    print(f"✅ Extracted {len(trending_words)} trending words")
    return trending_words

def save_reddit_llm_results(reddit_posts_count, llm_response, trending_words):
    """Save Reddit LLM analysis results"""
    print("💾 Saving results...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"reddit_llm_trending_analysis_{timestamp}.json"
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "reddit_posts_analyzed": reddit_posts_count,
        "llm_model": "llama-3.3-70b-versatile",  # Updated model name
        "llm_response_raw": llm_response,
        "extracted_trending_words": trending_words,
        "analysis_summary": {
            "total_trending_words": len(trending_words),
            "analysis_type": "Reddit Social Media Trending Analysis (Mixed Language Input, Bengali Output)",
            "language": "Bengali",
            "input_languages": ["English", "Banglish", "Bengali"]
        }
    }
    
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Results saved to: {results_file}")
        
        return results_file
    except Exception as e:
        print(f"❌ Error saving results: {e}")
        return None

def main():
    """Main function to test Reddit LLM integration"""
    print("🚀 Reddit LLM Trending Analysis Test")
    print("=" * 60)
    
    # Step 1: Load Reddit data
    posts = load_reddit_data()
    if not posts:
        return
    
    # Step 2: Prepare content for LLM
    content_text = prepare_reddit_content_for_llm(posts)
    
    # Show content preview
    print(f"\n📋 Content Preview (first 15000 chars):")
    print(f"{content_text[:15000]}...")
    
    # Step 3: Create LLM prompt
    prompt = create_reddit_trending_llm_prompt(content_text)
    
    # Step 4: Call LLM
    llm_response = call_groq_llm_for_reddit_analysis(prompt)
    
    if not llm_response:
        print("❌ LLM analysis failed")
        return
    
    # Step 5: Parse response
    trending_words = parse_llm_response(llm_response)
    
    # Step 6: Display results
    print(f"\n" + "=" * 60)
    print(f"🔥 Reddit থেকে LLM নির্বাচিত ট্রেন্ডিং শব্দ:")
    print(f"=" * 60)
    
    for i, word in enumerate(trending_words, 1):
        print(f"   {i:2d}. {word}")
    
    # Step 7: Show full LLM response
    print(f"\n🤖 সম্পূর্ণ LLM Response:")
    print(f"-" * 50)
    print(llm_response)
    print(f"-" * 50)
    
    # Step 8: Save results
    results_file = save_reddit_llm_results(len(posts), llm_response, trending_words)
    
    # Step 9: Summary
    print(f"\n📊 Analysis Summary:")
    print(f"   Reddit Posts Analyzed: {len(posts)}")
    print(f"   Trending Words Found: {len(trending_words)}")
    print(f"   Results File: {results_file}")
    print(f"   Status: {'✅ Success' if trending_words else '❌ Failed'}")
    
    print(f"\n🎉 Reddit LLM integration test completed!")

if __name__ == "__main__":
    main()
