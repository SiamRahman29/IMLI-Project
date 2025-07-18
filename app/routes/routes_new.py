from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import date, datetime, timedelta
from typing import Optional, List
import os
import re
import json
import asyncio
import traceback
import os
import json
import re
import asyncio
import traceback
import time
import builtins
import os
import json
import re
import traceback
import time
import builtins
import asyncio
import io
import sys
import io
import sys
import random

from app.db.database import SessionLocal
from app.models.word import Word, TrendingPhrase
from app.models.user import User
from app.routes.helpers import get_trending_words
from app.dto.dtos import TrendingWordsResponse, TrendingPhraseResponse, DailyTrendingResponse, TrendingPhrasesRequest
from app.auth.dependencies import get_current_admin_user, get_optional_current_user
# from app.services.social_media_scraper import print_scraped_posts_pretty, scrape_social_media_content

router = APIRouter()

# Dependency for getting DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", summary="Get today's word of the day")
def get_word_of_the_day(db: Session = Depends(get_db)):
    """Get the word of the day for today with all selected words"""
    today = date.today()
    word_entry = db.query(Word).filter(Word.date == today).first()
    
    if word_entry:
        return TrendingWordsResponse(
            date=str(word_entry.date),
            words=word_entry.word,
            selected_words=word_entry.selected_words
        )
    else:
        # Instead of raising 404, return a default response
        return {
            "date": str(today),
            "words": None,
            "selected_words": None,
            "message": "Today's word is not yet set"
        }

@router.post("/generate_candidates", summary="Generate category-wise trending words from newspapers using LLM")
async def generate_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Generate trending word candidates using saved newspaper data and category-wise LLM analysis (Admin only)"""
    import json
    import os
    import re
    from datetime import datetime
    from groq import Groq
    from app.services.filtered_newspaper_service import FilteredNewspaperScraper
    from app.services.category_llm_analyzer import (
        get_জাতীয়_trending_words, get_অর্থনীতি_trending_words, get_রাজনীতি_trending_words,
        get_বিনোদন_trending_words, get_খেলাধুলা_trending_words,
        get_শিক্ষা_trending_words,
        get_স্বাস্থ্য_trending_words, get_বিজ্ঞান_trending_words,
        get_আন্তর্জাতিক_trending_words, get_প্রযুক্তি_trending_words,
        get_সাহিত্য_সংস্কৃতি_trending_words, get_ক্ষুদ্র_নৃগোষ্ঠী_trending_words
    )
    
    try:
        # Target categories as requested
        TARGET_CATEGORIES = [
            'জাতীয়', 'আন্তর্জাতিক', 'অর্থনীতি', 'রাজনীতি', 'বিনোদন', 
            'খেলাধুলা',  'শিক্ষা', 'স্বাস্থ্য',  'বিজ্ঞান', 'প্রযুক্তি',
            'সাহিত্য-সংস্কৃতি', 'ক্ষুদ্র নৃগোষ্ঠী'
        ]
        
        print(f"🚀 Starting trending word generation for {len(TARGET_CATEGORIES)} categories...")
        
        # Always use live scraping for frequency calculation (temporary in-memory storage)
        print(f"🔴 LIVE SCRAPING: Using fresh scraping for accurate frequency calculation...")
        print(f"🧠 MEMORY OPTIMIZATION: Storing articles temporarily in memory only (not in DB)")
        scraper = FilteredNewspaperScraper(TARGET_CATEGORIES)
        results = scraper.scrape_all_newspapers()
        
        print(f"📊 Scraped {results['scraping_info']['total_articles']} articles")
        print(f"📂 Category-wise breakdown:")
        for category in TARGET_CATEGORIES:
            count = len(results['category_wise_articles'].get(category, []))
            print(f"   {category}: {count} articles")
        
        # Define category functions mapping
        category_functions = {
            'জাতীয়': get_জাতীয়_trending_words,
            'আন্তর্জাতিক': get_আন্তর্জাতিক_trending_words,
            'অর্থনীতি': get_অর্থনীতি_trending_words,
            'রাজনীতি': get_রাজনীতি_trending_words,
            # 'লাইফস্টাইল': get_লাইফস্টাইল_trending_words,
            'বিনোদন': get_বিনোদন_trending_words,
            'খেলাধুলা': get_খেলাধুলা_trending_words,
            # 'ধর্ম': get_ধর্ম_trending_words,
            # 'চাকরি': get_চাকরি_trending_words,
            'শিক্ষা': get_শিক্ষা_trending_words,
            'স্বাস্থ্য': get_স্বাস্থ্য_trending_words,
            # 'মতামত': get_মতামত_trending_words,
            'বিজ্ঞান': get_বিজ্ঞান_trending_words,
            'প্রযুক্তি': get_প্রযুক্তি_trending_words,
            'সাহিত্য-সংস্কৃতি': get_সাহিত্য_সংস্কৃতি_trending_words,
            'ক্ষুদ্র নৃগোষ্ঠী': get_ক্ষুদ্র_নৃগোষ্ঠী_trending_words
        }

        # Category-wise LLM trending word extraction (sequential, with delay)
        all_trending_words = []
        category_wise_trending = {}
        for category in TARGET_CATEGORIES:
            articles = results['category_wise_articles'][category]
            if articles:
                # Call the LLM function for this category, requesting 8 trending words
                try:
                    trending_func = category_functions[category]
                    # Pass articles and set limit=15 if supported
                    trending_words = trending_func(articles)  # Remove await since functions are synchronous
                    # Ensure only 15 words
                    trending_words = trending_words[:15]
                    category_wise_trending[category] = trending_words
                    all_trending_words.extend(trending_words)
                    print(f"✅ [{category}] Got {len(trending_words)} trending words: {trending_words}")
                except Exception as e:
                    print(f"⚠️ [{category}] LLM extraction failed: {e}")
                    category_wise_trending[category] = []
                # Wait 50 seconds before next category (except after last)
                if category != TARGET_CATEGORIES[-1]:
                    print(f"⏳ Waiting 50 seconds before next category...")
                    await asyncio.sleep(50)
            else:
                print(f"❌ [{category}] No articles found, skipping LLM call.")
                category_wise_trending[category] = []

        # --- Reddit Per-Subreddit Processing (AFTER newspaper processing) ---
        try:
            from enhanced_reddit_category_scraper import EnhancedRedditCategoryScraper
            
            reddit_scraper = EnhancedRedditCategoryScraper()
            reddit_client = Groq(api_key=os.getenv('GROQ_API_KEY_NEWSPAPER'))
            all_reddit_words = []
            
            # Process each subreddit individually to get 2 words each
            subreddits_to_process = ['bangladesh', 'dhaka', 'news', 'worldnews', 'technology', 'bengalimemes']
            
            print(f"🔄 Processing {len(subreddits_to_process)} subreddits individually...")
            
            for subreddit in subreddits_to_process:
                try:
                    # Scrape individual subreddit
                    posts = reddit_scraper.reddit_scraper.scrape_subreddit(subreddit, posts_limit=15)
                    
                    if posts and len(posts) > 0:
                        # Prepare content for LLM
                        content_parts = []
                        for post in posts[:10]:  # Take top 10 posts
                            title = post.get('title', '').strip()
                            text = post.get('text', '').strip()
                            if title:
                                content_parts.append(f"Title: {title}")
                            if text and len(text) > 20:
                                content_parts.append(f"Text: {text[:200]}...")
                        
                        if content_parts:
                            subreddit_content = "\n\n".join(content_parts)
                            
                            # LLM prompt for individual subreddit
                            subreddit_prompt = f"""তুমি একজন বিশেষজ্ঞ বাংলাদেশি সংবাদ বিশ্লেষক। নিচের Reddit r/{subreddit} থেকে পোস্টগুলো বিশ্লেষণ করে ঠিক 2টি ট্রেন্ডিং শব্দ/বাক্যাংশ বের করো।

Reddit Content from r/{subreddit}:
{subreddit_content}

নির্দেশনা:
1. ঠিক 2টি সবচেয়ে প্রাসঙ্গিক ট্রেন্ডিং শব্দ/বাক্যাংশ বের করো
2. প্রতিটি শব্দ/বাক্যাংশ 2-4 শব্দের মধ্যে হতে হবে
3. শব্দগুলো বাংলা বা ইংরেজি হতে পারে, কিন্তু অর্থবহ হতে হবে
4. ব্যক্তিগত নাম এড়িয়ে চলো, বিষয়বস্তুর উপর ফোকাস করো
5. সাম্প্রতিক ও আলোচিত বিষয়গুলো অগ্রাধিকার দাও

আউটপুট ফরম্যাট:
1. শব্দ১
2. শব্দ২

শুধুমাত্র উপরের ফরম্যাটে 2টি শব্দ দাও। অতিরিক্ত ব্যাখ্যা যোগ করো না।"""

                            # Call LLM for this subreddit
                            completion = reddit_client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[{"role": "user", "content": subreddit_prompt}],
                                temperature=0.3,
                                max_tokens=100
                            )
                            
                            llm_response = completion.choices[0].message.content.strip()
                            
                            # Parse the 2 words from response
                            subreddit_words = []
                            for line in llm_response.split('\n'):
                                line = line.strip()
                                if re.match(r'^[12১২][\.\)]\s*', line):
                                    word = re.sub(r'^[12১২][\.\)]\s*', '', line).strip()
                                    word = re.sub(r'[।\.]+$', '', word).strip()
                                    if word and len(word) > 1:
                                        subreddit_words.append(word)
                            
                            # Take exactly 2 words
                            subreddit_words = subreddit_words[:2]
                            all_reddit_words.extend(subreddit_words)
                            
                            print(f"✅ r/{subreddit}: Got {len(subreddit_words)} words: {subreddit_words}")
                            
                            # Wait between subreddits (smaller delay)
                            if subreddit != subreddits_to_process[-1]:
                                print(f"⏳ Waiting 15 seconds before next subreddit...")
                                await asyncio.sleep(15)
                    else:
                        print(f"❌ r/{subreddit}: No posts found")
                
                except Exception as subreddit_error:
                    print(f"⚠️ Error processing r/{subreddit}: {subreddit_error}")
                    continue
            
            # Merge all Reddit words with newspaper 'আন্তর্জাতিক' category
            if all_reddit_words:
                if 'আন্তর্জাতিক' in category_wise_trending:
                    existing_international_words = category_wise_trending['আন্তর্জাতিক']
                    combined_words = existing_international_words + all_reddit_words
                    # Remove duplicates while preserving order
                    unique_words = []
                    seen = set()
                    for word in combined_words:
                        if word not in seen:
                            unique_words.append(word)
                            seen.add(word)
                    category_wise_trending['আন্তর্জাতিক'] = unique_words
                    print(f"🌍 Enhanced আন্তর্জাতিক category with {len(all_reddit_words)} Reddit words from {len(subreddits_to_process)} subreddits")
                
                # Also update all_trending_words for completeness
                all_trending_words.extend([w for w in all_reddit_words if w not in all_trending_words])
        
        except Exception as e:
            print(f"⚠️ Could not integrate Reddit per-subreddit trending words: {e}")

        # --- Final LLM Selection: Get 5 words per category ---
        category_wise_final = {}
        final_trending_words = []
        llm_selection_stats = {}
        
        try:
            # Create category-wise prompt for final selection
            category_prompt_sections = []
            total_input_words = 0
            
            for category, words in category_wise_trending.items():
                if words and len(words) > 0:
                    # Take up to 15 words per category (or 25 for আন্তর্জাতিক)
                    word_limit = 25 if category == 'আন্তর্জাতিক' else 15
                    limited_words = words[:word_limit]
                    total_input_words += len(limited_words)
                    
                    words_text = "\n".join([f"  {i}. {word}" for i, word in enumerate(limited_words, 1)])
                    section = f"{category} ({len(limited_words)}টি):\n{words_text}"
                    category_prompt_sections.append(section)
                
            if category_prompt_sections:
                categories_text = "\n\n".join(category_prompt_sections)
                
                client = Groq(api_key=os.getenv('GROQ_API_KEY_NEWSPAPER'))
                    
                final_selection_prompt = f"""তুমি একজন বিশেষজ্ঞ বাংলাদেশি সংবাদ বিশ্লেষক।আপনাকে নিম্নলিখিত ক্যাটেগরি অনুযায়ী ট্রেন্ডিং শব্দগুলো থেকে প্রতিটি ক্যাটেগরি থেকে সবচেয়ে গুরুত্বপূর্ণ 10টি করে শব্দ বেছে নিতে হবে। এমন শব্দ/বাক্যাংশ দাও যেটা শুনলে মানুষ বুঝতে পারবে যে এটা কীসের সাথে সম্পর্কিত। যার একটা অর্থ থাকবে, এমন কিছু দেবে না যেটা অর্থহীন এবং যেটা দেখলে কনটেক্সট বোঝা যাবে না।
ক্যাটেগরি অনুযায়ী ট্রেন্ডিং শব্দ:
{categories_text}
নির্বাচনের নিয়মাবলী:
1. প্রতিটি ক্যাটেগরি থেকে সবচেয়ে প্রাসঙ্গিক ১০টি শব্দ নির্বাচন করুন
2. প্রতিটি শব্দ/বাক্যাংশ ২-৪ শব্দের মধ্যে এবং স্পষ্ট অর্থবোধক হতে হবে
3. এক ক্যাটেগরিতে একই টপিক বা অর্থের কাছাকাছি শব্দ থাকবে না, প্রতিটি শব্দ ইউনিক ও প্রসঙ্গভিত্তিক অর্থবহ হতে হবে
4. response শুধুমাত্র bangla language a deo
5. ব্যক্তিগত নাম এড়িয়ে চলুন, বিষয়বস্তুর উপর ফোকাস করুন
6. সাম্প্রতিক ও জনপ্রিয় বিষয়গুলো অগ্রাধিকার দিন

আউটপুট ফরম্যাট:
প্রতিটি ক্যাটেগরির জন্য নিম্নরূপ ফরম্যাটে দিন:

ক্যাটেগরি নাম:
1. শব্দ১
2. শব্দ২
3. শব্দ৩
4. শব্দ৪
...
10. শব্দ১০

অন্য ক্যাটেগরি নাম:
1. শব্দ১
2. শব্দ২
...
...
10. শব্দ১০

শুধুমাত্র উপরের ফরম্যাটে উত্তর দিন। অতিরিক্ত ব্যাখ্যা বা মন্তব্য যোগ করবেন না।"""
                
                print(f"🤖 Generating final category-wise selection from {len(category_prompt_sections)} categories using LLM...")
                print(f"🔍 Final selection prompt: {final_selection_prompt}...")
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "user",
                            "content": final_selection_prompt
                        }
                    ],
                    temperature=0.2,
                    max_tokens=1200
                )
                
                llm_response = completion.choices[0].message.content.strip()
                
                # Enhanced category-wise parsing for better frontend integration
                print(f"🔍 Raw LLM Response:\n{llm_response}")
                print("=" * 50)
                
                current_category = None
                lines = llm_response.split('\n')
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    print(f"Processing line {i}: '{line}'")
                    
                    # Check if this is a category header (ends with colon and doesn't start with number)
                    if line.endswith(':') and not re.match(r'^[১২৩৪৫৬৭৮৯১০1-9][\.\)]\s*', line):
                        current_category = line.replace(':', '').strip()
                        if current_category not in category_wise_final:
                            category_wise_final[current_category] = []
                        print(f"✅ Found category: '{current_category}'")
                        continue
                    
                    # Extract numbered items for current category (support both English and Bengali numbers, including 10)
                    if current_category and (re.match(r'^([১২৩৪৫৬৭৮৯১০]|1[0]|[1-9])[\.\)]\s*', line) or re.match(r'^১০[\.\)]\s*', line)):
                        # Remove number prefix and clean up (handle both single digits and 10)
                        word = re.sub(r'^([১২৩৪৫৬৭৮৯১০]|1[0]|[1-9])[\.\)]\s*', '', line).strip()
                        word = re.sub(r'^১০[\.\)]\s*', '', word).strip()  # Extra cleanup for Bengali 10
                        # Remove any trailing punctuation or extra spaces
                        word = re.sub(r'[।\.]+$', '', word).strip()
                        
                        if word and len(word) > 1:
                            # Check if word already exists in the list
                            word_exists = False
                            for existing_word_info in category_wise_final[current_category]:
                                if isinstance(existing_word_info, dict) and existing_word_info.get('word') == word:
                                    word_exists = True
                                    break
                                elif isinstance(existing_word_info, str) and existing_word_info == word:
                                    word_exists = True
                                    break
                            
                            if not word_exists:
                                # Add word without frequency calculation (will be calculated later in batch)
                                word_info = {
                                    'word': word,
                                    'frequency': 1,  # Temporary default, will be calculated later
                                    'category': current_category,
                                    'source': 'final_llm_selection'
                                }
                                
                                category_wise_final[current_category].append(word_info)
                                
                                # Also add to final_trending_words for backward compatibility
                                final_trending_words.append(word)
                                
                                print(f"✅ Added word to {current_category}: '{word}' (temp frequency: 1) ({len(category_wise_final[current_category])}/10)")
                            else:
                                print(f"❌ Skipped duplicate word: '{word}'")
                        else:
                            print(f"❌ Skipped invalid word: '{word}'")
                
                # Final validation and cleanup for frontend consumption
                print("\n🎯 Final Category-wise Results (Before Cleanup):")
                for category, words in category_wise_final.items():
                    print(f"📂 {category}: {len(words)} words")
                    for j, word in enumerate(words, 1):
                        print(f"  {j}. {word}")
                
                # Ensure each category has exactly 10 words (pad with fallback if needed)
                for category in list(category_wise_final.keys()):
                    words = category_wise_final[category]
                    if len(words) < 10:
                        # Try to get fallback words from category_wise_trending
                        fallback_words = category_wise_trending.get(category, [])
                        for fallback_word in fallback_words:
                            if len(words) >= 10:
                                break
                            
                            # Check if word already exists
                            word_text = fallback_word if isinstance(fallback_word, str) else fallback_word.get('word', '') if isinstance(fallback_word, dict) else str(fallback_word)
                            
                            word_exists = False
                            for existing_word_info in words:
                                existing_word_text = existing_word_info.get('word') if isinstance(existing_word_info, dict) else str(existing_word_info)
                                if existing_word_text == word_text:
                                    word_exists = True
                                    break
                            
                            if not word_exists:
                                # Add fallback word without frequency calculation (will be calculated later in batch)
                                word_info = {
                                    'word': word_text,
                                    'frequency': 1,  # Temporary default, will be calculated later
                                    'category': category,
                                    'source': 'fallback_selection'
                                }
                                words.append(word_info)
                                print(f"🔄 Added fallback word to {category}: '{word_text}' (temp frequency: 1)")
                    
                    # Ensure exactly 10 words
                    category_wise_final[category] = words[:10]
                
                
                print("\n🎯 Final Category-wise Results (After Cleanup):")
                for category, words in category_wise_final.items():
                    print(f"📂 {category}: {len(words)} words")
                    for j, word_info in enumerate(words, 1):
                        if isinstance(word_info, dict):
                            word_text = word_info.get('word', '')
                            frequency = word_info.get('frequency', 1)
                            print(f"  {j}. {word_text} (freq: {frequency})")
                        else:
                            print(f"  {j}. {word_info} (freq: N/A)")
                print("=" * 50)
                
                # Store LLM selection statistics
                llm_selection_stats = {
                    "total_input_categories": len(category_prompt_sections),
                    "total_input_words": total_input_words,
                    "selected_words": len(final_trending_words),
                    "categories_processed": len(category_wise_final),
                    "selection_method": "Enhanced category-wise LLM selection (5 per category)",
                    "llm_response": llm_response
                }
                
                print(f"✅ LLM selected {len(final_trending_words)} words across {len(category_wise_final)} categories")
                for category, words in category_wise_final.items():
                    print(f"📊 {category}: {len(words)} words - {', '.join(words[:3])}..." if words else f"📊 {category}: No words")
        
        except Exception as e:
            print(f"⚠️ Could not use LLM for final selection: {e}")
            # Fallback: Use top words from each category without frequency calculation (will be calculated later)
            for category, words in category_wise_trending.items():
                if words:
                    fallback_words_with_freq = []
                    for word in words[:10]:
                        word_text = word if isinstance(word, str) else str(word)
                        
                        word_info = {
                            'word': word_text,
                            'frequency': 1,  # Temporary default, will be calculated later in batch
                            'category': category,
                            'source': 'fallback_primary'
                        }
                        fallback_words_with_freq.append(word_info)
                    
                    category_wise_final[category] = fallback_words_with_freq
                    # Extract just word text for final_trending_words backward compatibility
                    final_trending_words.extend([w['word'] for w in fallback_words_with_freq])
            
            llm_selection_stats = {
                "selection_method": "Fallback: Top 5 per category without LLM",
                "selected_words": len(final_trending_words),
                "categories_processed": len(category_wise_final)
            }

        print(f"🎉 Total trending words extracted: {len(all_trending_words)}")
        print(f"🎯 Final selected words: {len(final_trending_words)}")
        print(f"🔧 DEBUG: About to start frequency calculation section...")
        print(f"🔧 DEBUG: category_wise_final has {len(category_wise_final)} categories")
        
        # 🔍 FREQUENCY CALCULATION: Calculate frequency for all selected phrases in batch
        print(f"🔍 FREQUENCY CALCULATION: Calculating frequency for all selected phrases...")
        print(f"🔍 DEBUG: results object exists: {bool(results)}")
        print(f"🔍 DEBUG: category_wise_articles exists: {bool(results.get('category_wise_articles') if results else False)}")
        
        total_phrases_to_calculate = sum(len(words) for words in category_wise_final.values())
        phrases_calculated = 0
        
        print(f"🔧 DEBUG: About to import calculate_phrase_frequency_in_articles...")
        from app.services.category_llm_analyzer import calculate_phrase_frequency_in_articles
        print(f"🔧 DEBUG: Import successful!")
        
        for category, words in category_wise_final.items():
            print(f"🔍 Processing category '{category}' with {len(words)} words...")
            
            # Get articles for this category with better debugging
            category_articles = []
            if results and 'category_wise_articles' in results:
                category_articles = results['category_wise_articles'].get(category, [])
                print(f"🔍 DEBUG: Found {len(category_articles)} articles for category '{category}'")
            else:
                print(f"🔍 DEBUG: No articles found for category '{category}' - results or category_wise_articles missing")
            
            for word_info in words:
                if isinstance(word_info, dict):
                    word_text = word_info.get('word', '')
                    
                    if word_text and category_articles:
                        # Calculate frequency for this phrase
                        freq_stats = calculate_phrase_frequency_in_articles(word_text, category_articles)
                        actual_frequency = freq_stats.get('frequency', 1)
                        
                        # Update frequency in word_info
                        word_info['frequency'] = actual_frequency
                        
                        phrases_calculated += 1
                        print(f"🔍 [{phrases_calculated}/{total_phrases_to_calculate}] '{word_text}' → frequency: {actual_frequency}")
                    else:
                        # Keep default frequency if no articles or invalid word
                        word_info['frequency'] = 1
                        phrases_calculated += 1
                        print(f"🔍 [{phrases_calculated}/{total_phrases_to_calculate}] '{word_text}' → default frequency: 1 (no articles available)")
        
        print(f"✅ FREQUENCY CALCULATION COMPLETE: {phrases_calculated} phrases processed")
        
        # 🧠 MEMORY OPTIMIZATION: Clear scraped articles from memory after frequency calculation
        print(f"🗑️ MEMORY CLEANUP: Removing {results['scraping_info']['total_articles']} scraped articles from memory...")
        
        # Clear category-wise articles (main memory consumer)
        if 'category_wise_articles' in results:
            for category in results['category_wise_articles']:
                results['category_wise_articles'][category].clear()
            results['category_wise_articles'].clear()
        
        # Keep only essential data for response (statistics and metadata)
        scraping_stats = results['scraping_info'].copy()
        
        # Clear the full results object
        results.clear()
        
        print(f"✅ MEMORY CLEANUP: Articles removed from memory, DB size optimized")
        
        return {
            "message": "Category-wise trending words generated successfully using filtered newspaper scraping and LLM analysis!",
            "scraping_info": scraping_stats,
            "category_wise_trending_words": category_wise_trending,
            "all_trending_words": all_trending_words,
            "category_wise_final": category_wise_final,
            "final_trending_words": final_trending_words,
            "llm_selection": llm_selection_stats,
            "statistics": {
                "total_articles_scraped": scraping_stats['total_articles'],
                "categories_processed": len([c for c in TARGET_CATEGORIES if category_wise_trending.get(c, [])]),
                "total_trending_words": len(all_trending_words),
                "final_selected_words": len(final_trending_words),
                "scraping_time_seconds": scraping_stats.get('scraping_time_seconds', 0)
            },
            "memory_optimization": {
                "articles_removed_from_memory": scraping_stats['total_articles'],
                "memory_optimized": True,
                "db_storage_skipped": True
            }
        }
        
    except Exception as e:
        import traceback
        detail = f"Error generating category-wise candidates: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=detail)

@router.get("/trending-phrases", summary="Get trending phrases for a specific date range")
def get_trending_phrases(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    limit: int = Query(10, description="Maximum number of phrases to return (default: 10)"),
    offset: int = Query(0, description="Number of results to skip for pagination (default: 0)"),
    source: Optional[str] = Query(None, description="Filter by source (news, social_media, etc.)"),
    phrase_type: Optional[str] = Query(None, description="Filter by phrase type"),
    db: Session = Depends(get_db)
):
    """Get trending phrases for a specific date range with filtering options"""
    
    # Set default date range (last 7 days)
    if not start_date:
        start_date = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = date.today().strftime("%Y-%m-%d")
    
    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Build query
    query = db.query(TrendingPhrase).filter(
        and_(
            TrendingPhrase.date >= start_date_obj,
            TrendingPhrase.date <= end_date_obj
        )
    )
    
    # Apply filters
    if source:
        query = query.filter(TrendingPhrase.source == source)
    if phrase_type:
        query = query.filter(TrendingPhrase.phrase_type == phrase_type)
    
    # Get total count for pagination
    total_count = query.count()
    
    # Order by date descending (latest first), then by score descending
    phrases = query.order_by(desc(TrendingPhrase.date), desc(TrendingPhrase.score)).offset(offset).limit(limit).all()
    
    # Convert to response format
    trending_phrases = []
    for phrase in phrases:
        trending_phrases.append(TrendingPhraseResponse(
            id=phrase.id,
            date=str(phrase.date),
            phrase=phrase.phrase,
            score=phrase.score,
            frequency=phrase.frequency,
            phrase_type=phrase.phrase_type,
            source=phrase.source
        ))
    
    return { 
        "start_date": start_date,
        "end_date": end_date,
        "phrases": trending_phrases,
        "pagination": {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_next": (offset + limit) < total_count,
            "has_prev": offset > 0
        }
    }

@router.delete("/trending-phrases/{phrase_id}")
def delete_trending_phrase(
    phrase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a trending phrase (Admin only) - Smart frequency handling"""
    phrase = db.query(TrendingPhrase).filter(TrendingPhrase.id == phrase_id).first()
    if not phrase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trending phrase not found"
        )
    
    # If frequency > 1, just decrease frequency
    if phrase.frequency > 1:
        phrase.frequency -= 1
        # Optionally adjust score proportionally
        phrase.score = phrase.score * (phrase.frequency / (phrase.frequency + 1))
        db.commit()
        return {
            "message": f"Phrase frequency decreased to {phrase.frequency}",
            "action": "frequency_decreased",
            "remaining_frequency": phrase.frequency
        }
    else:
        # If frequency = 1, delete the entire entry
        db.delete(phrase)
        db.commit()
        return {
            "message": "Trending phrase deleted completely",
            "action": "phrase_deleted"
        }

@router.get("/daily-trending", summary="Get daily trending summary")
def get_daily_trending(
    target_date: Optional[str] = Query(None, description="Target date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """Get trending phrases summary for a specific day"""
    
    if not target_date:
        target_date = date.today().strftime("%Y-%m-%d")
    
    try:
        target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get phrases for the target date
    phrases = db.query(TrendingPhrase).filter(
        TrendingPhrase.date == target_date_obj
    ).order_by(desc(TrendingPhrase.score)).all()
    
    # Group by source and phrase type
    sources = {}
    phrase_types = {}
    
    for phrase in phrases:
        # Group by source
        if phrase.source not in sources:
            sources[phrase.source] = []
        sources[phrase.source].append({
            "phrase": phrase.phrase,
            "score": phrase.score,
            "frequency": phrase.frequency
        })
        
        # Group by phrase type
        if phrase.phrase_type not in phrase_types:
            phrase_types[phrase.phrase_type] = []
        phrase_types[phrase.phrase_type].append({
            "phrase": phrase.phrase,
            "score": phrase.score,
            "frequency": phrase.frequency
        })
    
    return DailyTrendingResponse(
        date=target_date,
        total_phrases=len(phrases),
        by_source=sources,
        by_phrase_type=phrase_types,
        top_phrases=[{
            "phrase": p.phrase,
            "score": p.score,
            "frequency": p.frequency,
            "source": p.source,
            "phrase_type": p.phrase_type
        } for p in phrases[:10]]
    )

@router.post("/analyze", summary="Run trending analysis for current data")
def run_trending_analysis(
    request: Optional[TrendingPhrasesRequest] = None,
    db: Session = Depends(get_db)
):
    """Run comprehensive trending analysis on collected data"""
    try:
        # Run the analysis
        result = get_trending_words(db)
        
        return {
            "message": "Trending analysis completed successfully",
            "analysis_date": date.today().strftime("%Y-%m-%d"),
            "phrases_analyzed": result.get("phrases_count", 0) if isinstance(result, dict) else 0,
            "note": "Check /trending-phrases endpoint for results"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/analyze-progressive", summary="Run trending analysis with step-by-step progress")
async def run_progressive_analysis(
    db: Session = Depends(get_db)
):
    
    async def generate_progress():
        try:
            # Step 1: Initialize analysis system
            yield f"data: {json.dumps({'step': 1, 'message': 'বিশ্লেষণ সিস্টেম প্রস্তুত করা হচ্ছে...', 'progress': 5, 'details': {'status': 'initializing'}})}\n\n"
            time.sleep(0.5)
            
            # Step 2: Fetch news data
            yield f"data: {json.dumps({'step': 2, 'message': 'সংবাদ ও কন্টেন্ট সংগ্রহ করা হচ্ছে...', 'progress': 15, 'details': {'source': 'news_apis'}})}\n\n"
            print("=== Starting news data collection ===")
            
            from app.routes.helpers import fetch_news
            news_articles = fetch_news()
            print(f"=== Fetched {len(news_articles)} news articles ===")
            
            # Step 3: Analyze articles in memory (no DB storage needed)
            yield f"data: {json.dumps({'step': 3, 'message': 'মেমরিতে কন্টেন্ট বিশ্লেষণ প্রস্তুত করা হচ্ছে...', 'progress': 25, 'details': {'analyzing': 'articles', 'articles_collected': len(news_articles)}})}\n\n"
            print("=== Analyzing articles in memory for trending word extraction ===")
            
            # Note: Articles are kept in memory only, no database storage to optimize DB size
            
            # Step 4: Initialize advanced Bengali NLP analyzer
            yield f"data: {json.dumps({'step': 4, 'message': 'উন্নত বাংলা এনএলপি সিস্টেম চালু করা হচ্ছে...', 'progress': 35, 'details': {'initializing': 'bengali_nlp'}})}\n\n"
            
            # Here's where we integrate with the advanced_bengali_nlp analysis
            if news_articles:
                from app.services.advanced_bengali_nlp import TrendingBengaliAnalyzer
                
                # Custom output capturing to get step-by-step data
                captured_steps = {}
                original_print = print
                step_data = {'current_step': None, 'current_data': []}
                
                def custom_print(*args, **kwargs):
                    """Custom print function to capture step-by-step analysis output"""
                    message = ' '.join(str(arg) for arg in args)
                    original_print(*args, **kwargs)  # Still print to console
                    
                    # Parse step markers
                    if 'Step 1 - Extracted Texts:' in message:
                        if step_data['current_step']:
                            captured_steps[step_data['current_step']] = step_data['current_data'].copy()
                        step_data['current_step'] = 'extracted_texts'
                        step_data['current_data'] = []
                    elif 'Step 2 - Word Frequency Cache:' in message:
                        if step_data['current_step']:
                            captured_steps[step_data['current_step']] = step_data['current_data'].copy()
                        step_data['current_step'] = 'word_frequency'
                        step_data['current_data'] = []
                    elif 'Step 3 - Trending Keywords:' in message:
                        if step_data['current_step']:
                            captured_steps[step_data['current_step']] = step_data['current_data'].copy()
                        step_data['current_step'] = 'trending_keywords'
                        step_data['current_data'] = []
                    elif 'Step 4 - Named Entities (raw):' in message:
                        if step_data['current_step']:
                            captured_steps[step_data['current_step']] = step_data['current_data'].copy()
                        step_data['current_step'] = 'named_entities_raw'
                        step_data['current_data'] = []
                    elif 'Step 5 - Named Entities (deduped, counted):' in message:
                        if step_data['current_step']:
                            captured_steps[step_data['current_step']] = step_data['current_data'].copy()
                        step_data['current_step'] = 'named_entities_final'
                        step_data['current_data'] = []
                    elif 'Step 6 - Sentiment Scores:' in message:
                        if step_data['current_step']:
                            captured_steps[step_data['current_step']] = step_data['current_data'].copy()
                        step_data['current_step'] = 'sentiment_scores'
                        step_data['current_data'] = []
                    elif 'Step 7 - Average Sentiment:' in message:
                        if step_data['current_step']:
                            captured_steps[step_data['current_step']] = step_data['current_data'].copy()
                        step_data['current_step'] = 'average_sentiment'
                        step_data['current_data'] = []
                    elif 'Step 8 - Clustered Phrases:' in message:
                        if step_data['current_step']:
                            captured_steps[step_data['current_step']] = step_data['current_data'].copy()
                        step_data['current_step'] = 'clustered_phrases'
                        step_data['current_data'] = []
                    elif step_data['current_step'] and message.strip() and not message.startswith(' Incoming') and not message.startswith(' Number of') and not message.startswith('==='):
                        step_data['current_data'].append(message.strip())
                
                # Temporarily replace print with our custom function
                import builtins
                builtins.print = custom_print
                
                try:
                    bengali_analyzer = TrendingBengaliAnalyzer()
                    
                    # Step 5: Text extraction and preprocessing
                    yield f"data: {json.dumps({'step': 5, 'message': 'বাংলা টেক্সট এক্সট্র্যাকশন ও প্রক্রিয়াকরণ...', 'progress': 45, 'details': {'processing': 'text_extraction'}})}\n\n"
                    
                    # Step 6: Run comprehensive Bengali analysis
                    yield f"data: {json.dumps({'step': 6, 'message': 'সম্পূর্ণ বাংলা এনএলপি বিশ্লেষণ চালু করা হচ্ছে...', 'progress': 55, 'details': {'processing': 'comprehensive_analysis'}})}\n\n"
                    
                    # Perform the actual analysis (this will capture all steps)
                    bengali_analysis = bengali_analyzer.analyze_trending_content(news_articles, 'news')
                    
                    # Add final step data
                    if step_data['current_step'] and step_data['current_data']:
                        captured_steps[step_data['current_step']] = step_data['current_data']
                    
                finally:
                    # Restore original print function
                    builtins.print = original_print
                
                # Step 7: Process and format captured step data for frontend
                yield f"data: {json.dumps({'step': 7, 'message': 'বিশ্লেষণ ফলাফল ফরম্যাট করা হচ্ছে...', 'progress': 65, 'details': {'formatting': 'step_results'}})}\n\n"
                
                # Format step results for beautiful frontend display
                step_results = {
                    'step_by_step_analysis': {
                        'step_1_text_extraction': {
                            'title': '১. টেক্সট এক্সট্র্যাকশন',
                            'description': 'সংবাদ নিবন্ধ থেকে বাংলা টেক্সট নিষ্কাশন',
                            'data': captured_steps.get('extracted_texts', [])[:8],  # Show first 8 texts
                            'total_count': len(captured_steps.get('extracted_texts', [])),
                            'sample_preview': captured_steps.get('extracted_texts', [''])[0][:100] + '...' if captured_steps.get('extracted_texts') else ''
                        },
                        'step_2_word_frequency': {
                            'title': '২. শব্দ ফ্রিকোয়েন্সি ক্যাশ আপডেট',
                            'description': 'বাংলা শব্দের ব্যবহার ফ্রিকোয়েন্সি ক্যাশে সংরক্ষণ',
                            'status': 'updated',
                            'cache_size': 'আপডেট সম্পন্ন',
                            'data_preview': 'ফ্রিকোয়েন্সি ডেটা সফলভাবে আপডেট হয়েছে'
                        },
                        'step_3_trending_keywords': {
                            'title': '৩. ট্রেন্ডিং কীওয়ার্ড নিষ্কাশন',
                            'description': 'TF-IDF অ্যালগরিদম ব্যবহার করে গুরুত্বপূর্ণ কীওয়ার্ড খুঁজে বের করা',
                            'data': bengali_analysis.get('trending_keywords', [])[:20],  # Top 20 keywords
                            'total_keywords': len(bengali_analysis.get('trending_keywords', [])),
                            'top_keywords_preview': [{'keyword': kw[0], 'score': round(kw[1], 4)} for kw in bengali_analysis.get('trending_keywords', [])[:5]]
                        },
                        'step_4_named_entities_raw': {
                            'title': '৪. নামযুক্ত সত্তা শনাক্তকরণ (প্রাথমিক)',
                            'description': 'ব্যক্তি, স্থান, সংস্থা এবং তারিখ শনাক্তকরণ',
                            'entity_types': ['ব্যক্তি', 'স্থান', 'সংস্থা', 'তারিখ'],
                            'raw_extraction_status': 'সম্পন্ন'
                        },
                        'step_5_named_entities_final': {
                            'title': '৫. নামযুক্ত সত্তা (চূড়ান্ত ও গণনাকৃত)',
                            'description': 'ডুপ্লিকেট অপসারণ এবং ফ্রিকোয়েন্সি গণনা',
                            'data': bengali_analysis.get('named_entities', {}),
                            'processed': True,
                            'entity_summary': {
                                'persons': len(bengali_analysis.get('named_entities', {}).get('persons', [])),
                                'places': len(bengali_analysis.get('named_entities', {}).get('places', [])),
                                'organizations': len(bengali_analysis.get('named_entities', {}).get('organizations', [])),
                                'dates': len(bengali_analysis.get('named_entities', {}).get('dates', []))
                            }
                        },
                        'step_6_sentiment_analysis': {
                            'title': '৬. অনুভূতি বিশ্লেষণ',
                            'description': 'প্রতিটি নিবন্ধের ইতিবাচক, নেতিবাচক ও নিরপেক্ষ অনুভূতি পরিমাপ',
                            'individual_scores_sample': captured_steps.get('sentiment_scores', [])[:5],  # Show first 5 scores
                            'total_analyzed': len(captured_steps.get('sentiment_scores', [])),
                            'average_sentiment': bengali_analysis.get('sentiment_analysis', {}),
                            'sentiment_summary': {
                                'positive': f"{bengali_analysis.get('sentiment_analysis', {}).get('positive', 0)*100:.1f}%",
                                'negative': f"{bengali_analysis.get('sentiment_analysis', {}).get('negative', 0)*100:.1f}%",
                                'neutral': f"{bengali_analysis.get('sentiment_analysis', {}).get('neutral', 0)*100:.1f}%"
                            }
                        },
                        'step_7_phrase_clustering': {
                            'title': '৭. ফ্রেজ ক্লাস্টারিং',
                            'description': 'সমজাতীয় ফ্রেজ ও কীওয়ার্ড গ্রুপিং',
                            'clusters': bengali_analysis.get('phrase_clusters', {}),
                            'cluster_count': len(bengali_analysis.get('phrase_clusters', {})),
                            'cluster_summary': [
                                {
                                    'cluster_id': cluster_id, 
                                    'phrase_count': len(phrases),
                                    'sample_phrases': phrases[:3]
                                } 
                                for cluster_id, phrases in bengali_analysis.get('phrase_clusters', {}).items()
                            ]
                        }
                    },
                    'content_statistics': bengali_analysis.get('content_statistics', {}),
                    'analysis_summary': {
                        'total_keywords_extracted': len(bengali_analysis.get('trending_keywords', [])),
                        'named_entities_found': sum(len(entities) for entities in bengali_analysis.get('named_entities', {}).values()),
                        'phrase_clusters_created': len(bengali_analysis.get('phrase_clusters', {})),
                        'articles_processed': len(news_articles),
                        'overall_sentiment': bengali_analysis.get('sentiment_analysis', {})
                    }
                }
                
                # Step 8: Store trending phrases in database
                yield f"data: {json.dumps({'step': 8, 'message': 'ট্রেন্ডিং ফ্রেজ ডেটাবেসে সংরক্ষণ...', 'progress': 75, 'details': {'storing': 'trending_phrases'}, 'step_results': step_results})}\n\n"
                
                from app.routes.helpers import TrendingAnalyzer, analyze_and_store_trends
                from datetime import date
                
                analyzer = TrendingAnalyzer()
                today = date.today()
                
                # Clear existing data for today
                db.query(TrendingPhrase).filter(TrendingPhrase.date == today).delete()
                
                # Store trending analysis results
                analyze_and_store_trends(db, analyzer, news_articles, 'news', today)
                
                # Step 9: Database commit
                yield f"data: {json.dumps({'step': 9, 'message': 'ডেটাবেস আপডেট সম্পন্ন করা হচ্ছে...', 'progress': 85, 'details': {'saving': 'final_results'}})}\n\n"
                db.commit()
                
                # Step 10: Generate final summary
                yield f"data: {json.dumps({'step': 10, 'message': 'চূড়ান্ত ফলাফল প্রস্তুত করা হচ্ছে...', 'progress': 95, 'details': {'generating': 'summary'}})}\n\n"
                
                # Get final database stats
                total_phrases = db.query(TrendingPhrase).filter(TrendingPhrase.date == today).count()
                
                # Add final summary to step results
                step_results['final_summary'] = {
                    'total_phrases_generated': total_phrases,
                    'articles_processed': len(news_articles),
                    'analysis_date': str(today),
                    'status': 'completed',
                    'database_records_created': total_phrases
                }
                
                # Final completion message
                final_result = {
                    'step': 11,
                    'message': 'বিশ্লেষণ সফলভাবে সম্পন্ন হয়েছে! 🎉',
                    'progress': 100,
                    'completed': True,
                    'step_results': step_results,
                    'completion_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                yield f"data: {json.dumps(final_result)}\n\n"
                print("=== ✅ Progressive analysis with step-by-step integration completed ===")
                
            else:
                # No articles found
                error_result = {
                    'error': True,
                    'message': 'কোনো সংবাদ নিবন্ধ পাওয়া যায়নি। দয়া করে পরে আবার চেষ্টা করুন।',
                    'step': 'no_data'
                }
                yield f"data: {json.dumps(error_result)}\n\n"
                
        except Exception as e:
            print(f"Error in progressive analysis: {e}")
            traceback.print_exc()
            error_result = {
                'error': True,
                'message': f'বিশ্লেষণে ত্রুটি ঘটেছে: {str(e)}',
                'step': 'error',
                'error_details': traceback.format_exc()
            }
            yield f"data: {json.dumps(error_result)}\n\n"
    
    return StreamingResponse(
        generate_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "*"
        }
    )

@router.get("/sources", summary="Get available data sources")
def get_available_sources(db: Session = Depends(get_db)):
    """Get list of available data sources with detailed information"""
    from sqlalchemy import func
    
    # Get basic distinct sources and phrase types
    sources = db.query(TrendingPhrase.source).distinct().all()
    phrase_types = db.query(TrendingPhrase.phrase_type).distinct().all()
    
    # Get detailed source statistics
    source_stats = db.query(
        TrendingPhrase.source,
        func.count(TrendingPhrase.id).label('count'),
        func.avg(TrendingPhrase.score).label('avg_score'),
        func.max(TrendingPhrase.date).label('latest_date')
    ).group_by(TrendingPhrase.source).all()
    
    # Get phrase type statistics
    phrase_type_stats = db.query(
        TrendingPhrase.phrase_type,
        func.count(TrendingPhrase.id).label('count'),
        func.avg(TrendingPhrase.score).label('avg_score')
    ).group_by(TrendingPhrase.phrase_type).all()
    
    # Get date range
    first_record = db.query(TrendingPhrase).first()
    date_range = {
        "earliest": None,
        "latest": None
    }
    
    if first_record:
        earliest = db.query(func.min(TrendingPhrase.date)).scalar()
        latest = db.query(func.max(TrendingPhrase.date)).scalar()
        date_range = {
            "earliest": str(earliest) if earliest else None,
            "latest": str(latest) if latest else None
        }
    
    return {
        "sources": [source[0] for source in sources],
        "phrase_types": [phrase_type[0] for phrase_type in phrase_types],
        "date_range": date_range,
        "source_details": [
            {
                "source": stat.source,
                "count": stat.count,
                "avg_score": round(stat.avg_score, 3),
                "latest_date": str(stat.latest_date)
            } for stat in source_stats
        ],
        "phrase_type_details": [
            {
                "phrase_type": stat.phrase_type,
                "count": stat.count,
                "avg_score": round(stat.avg_score, 3)
            } for stat in phrase_type_stats
        ]
    }

@router.get("/stats", summary="Get trending analysis statistics")
def get_trending_stats(db: Session = Depends(get_db)):
    """Get comprehensive statistics about trending phrases"""
    total_phrases = db.query(TrendingPhrase).count()
    
    if total_phrases == 0:
        return {
            "total_phrases": 0,
            "message": "No trending phrases found. Run analysis first."
        }
    
    # Get stats by source
    from sqlalchemy import func
    source_stats = db.query(
        TrendingPhrase.source,
        func.count(TrendingPhrase.id).label('count'),
        func.avg(TrendingPhrase.score).label('avg_score')
    ).group_by(TrendingPhrase.source).all()
    
    # Get stats by phrase type
    type_stats = db.query(
        TrendingPhrase.phrase_type,
        func.count(TrendingPhrase.id).label('count'),
        func.avg(TrendingPhrase.score).label('avg_score')
    ).group_by(TrendingPhrase.phrase_type).all()
    
    # Get recent activity (last 7 days)
    week_ago = date.today() - timedelta(days=7)
    recent_count = db.query(TrendingPhrase).filter(
        TrendingPhrase.date >= week_ago
    ).count()
    
    return {
        "total_phrases": total_phrases,
        "recent_phrases_7_days": recent_count,
        "by_source": [
            {
                "source": stat.source,
                "count": stat.count,
                "avg_score": round(stat.avg_score, 3)
            } for stat in source_stats
        ],
        "by_phrase_type": [
            {
                "phrase_type": stat.phrase_type,
                "count": stat.count,
                "avg_score": round(stat.avg_score, 3)
            } for stat in type_stats
        ]
    }

@router.get("/weekly-trending", summary="Get weekly trending summary")
def get_weekly_trending(
    target_week: Optional[str] = Query(None, description="Target week start date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """Get trending phrases summary for previous 7 days (default) or a specific week"""
    
    if not target_week:
        # Previous 7 days from today
        today = date.today()
        week_end = today
        week_start = today - timedelta(days=6)  # Previous 7 days including today
    else:
        try:
            week_start = datetime.strptime(target_week, "%Y-%m-%d").date()
            week_end = week_start + timedelta(days=6)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get phrases for the target week
    phrases = db.query(TrendingPhrase).filter(
        and_(
            TrendingPhrase.date >= week_start,
            TrendingPhrase.date <= week_end
        )
    ).order_by(desc(TrendingPhrase.date), desc(TrendingPhrase.score)).all()
    
    # Group by day
    daily_data = {}
    for phrase in phrases:
        day_key = str(phrase.date)
        if day_key not in daily_data:
            daily_data[day_key] = []
        daily_data[day_key].append({
            "phrase": phrase.phrase,
            "score": phrase.score,
            "frequency": phrase.frequency,
            "phrase_type": phrase.phrase_type,
            "source": phrase.source
        })
    
    # Get top phrases of the week
    top_weekly = phrases[:20]
    
    return {
        "week_start": str(week_start),
        "week_end": str(week_end),
        "total_phrases": len(phrases),
        "daily_breakdown": daily_data,
        "top_weekly_phrases": [{
            "phrase": p.phrase,
            "score": p.score,
            "frequency": p.frequency,
            "phrase_type": p.phrase_type,
            "source": p.source,
            "date": str(p.date)
        } for p in top_weekly]
    }

@router.get("/monthly-trending", summary="Get monthly trending summary")
def get_monthly_trending(
    target_month: Optional[str] = Query(None, description="Target month start date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """Get trending phrases summary for a specific month"""
    
    if not target_month:
        # Current month start
        today = date.today()
        month_start = today.replace(day=1)
    else:
        try:
            month_start = datetime.strptime(target_month, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Calculate month end
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
    
    # Get all phrases for the month
    monthly_phrases = db.query(TrendingPhrase).filter(
        and_(
            TrendingPhrase.date >= month_start,
            TrendingPhrase.date <= month_end
        )
    ).all()
    
    if not monthly_phrases:
        return {
            "month_start": str(month_start),
            "month_end": str(month_end),
            "total_phrases": 0,
            "message": "No trending phrases found for this month"
        }
    
    # Group and aggregate phrases
    phrase_aggregation = {}
    daily_breakdown = {}
    
    for phrase in monthly_phrases:
        phrase_key = phrase.phrase
        phrase_date = str(phrase.date)
        
        # Aggregate monthly data
        if phrase_key not in phrase_aggregation:
            phrase_aggregation[phrase_key] = {
                "phrase": phrase.phrase,
                "total_score": 0.0,
                "total_frequency": 0,
                "count": 0,
                "phrase_type": phrase.phrase_type,
                "source": phrase.source,
                "dates": []
            }
        
        phrase_aggregation[phrase_key]["total_score"] += phrase.score
        phrase_aggregation[phrase_key]["total_frequency"] += phrase.frequency
        phrase_aggregation[phrase_key]["count"] += 1
        phrase_aggregation[phrase_key]["dates"].append(phrase_date)
        
        # Daily breakdown
        if phrase_date not in daily_breakdown:
            daily_breakdown[phrase_date] = []
        daily_breakdown[phrase_date].append({
            "phrase": phrase.phrase,
            "score": phrase.score,
            "frequency": phrase.frequency,
            "phrase_type": phrase.phrase_type,
            "source": phrase.source
        })
    
    # Calculate averages and filter top phrases (appeared at least 3 days)
    top_monthly_phrases = []
    for phrase_data in phrase_aggregation.values():
        if phrase_data["count"] >= 3:  # Must appear at least 3 days in the month
            avg_score = phrase_data["total_score"] / phrase_data["count"]
            top_monthly_phrases.append({
                "phrase": phrase_data["phrase"],
                "score": avg_score,
                "frequency": phrase_data["total_frequency"],
                "phrase_type": phrase_data["phrase_type"],
                "source": phrase_data["source"],
                "days_appeared": phrase_data["count"],
                "dates": phrase_data["dates"]
            })
    
    # Sort by score and limit to top 50
    top_monthly_phrases.sort(key=lambda x: x["score"], reverse=True)
    top_monthly_phrases = top_monthly_phrases[:50]
    
    return {
        "month_start": str(month_start),
        "month_end": str(month_end),
        "total_phrases": len(top_monthly_phrases),
        "daily_breakdown": daily_breakdown,
        "top_monthly_phrases": top_monthly_phrases
    }


@router.get("/categories/detect", summary="🏷️ Test category detection for a URL", tags=["Category Analysis"])
def test_category_detection(
    url: str = Query(..., description="URL to analyze for category detection"),
    title: str = Query("", description="Article title (optional, helps with detection accuracy)"),
    content: str = Query("", description="Article content (optional, helps with detection accuracy)"),
):
    """
    Test the enhanced category detection system with URL patterns and content analysis
    
    **Primary Detection Method**: URL Pattern Analysis (87.2% accuracy)
    **Secondary Method**: Bengali Content Analysis
    **Tertiary Method**: Source-specific subcategorization
    
    **Supported Categories**: রাজনীতি, আন্তর্জাতিক, খেলাধুলা, অর্থনীতি, প্রযুক্তি, বিনোদন, স্বাস্থ্য, শিক্ষা, etc.
    """
    try:
        from app.routes.helpers import detect_category_from_url
        
        # Detect category using enhanced algorithm
        detected_category = detect_category_from_url(url, title, content)
        
        # Determine detection method used
        from urllib.parse import urlparse
        import re
        
        detection_method = "Unknown"
        if re.search(r'/(sports|cricket|football|politics|international|business|technology|entertainment|health|education)/', url.lower()):
            detection_method = "URL Pattern (Primary)"
        elif title or content:
            detection_method = "Content Analysis (Secondary)" 
        else:
            detection_method = "Source-specific Pattern (Tertiary)"
        
        return {
            "url": url,
            "title": title[:100] + "..." if len(title) > 100 else title,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "detected_category": detected_category,
            "detection_method": detection_method,
            "confidence": "High" if "Pattern" in detection_method else "Medium",
            "timestamp": datetime.now().isoformat(),
            "supported_categories": [
                "রাজনীতি", "আন্তর্জাতিক", "খেলাধুলা", "অর্থনীতি", "প্রযুক্তি", 
                "বিনোদন", "স্বাস্থ্য", "শিক্ষা", "মতামত", "লাইফস্টাইল", 
                "ধর্ম", "পরিবেশ", "বিজ্ঞান", "চাকরি", "ছবি", "ভিডিও"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting category: {str(e)}")

@router.get("/categories/trending", summary="📈 Get trending phrases by category", tags=["Category Analysis"])
def get_category_trending_phrases(
    category: str = Query(..., description="Category name in Bengali (e.g., রাজনীতি, খেলাধুলা, অর্থনীতি)"),
    days: int = Query(7, description="Number of days to analyze (default: 7)"),
    limit: int = Query(20, description="Maximum number of phrases to return (default: 20)"),
    phrase_type: Optional[str] = Query(None, description="Filter by phrase type: unigram, bigram, trigram"),
    db: Session = Depends(get_db)
):
    """
    Get trending phrases for a specific category with advanced filtering
    
    **Popular Categories**:
    - রাজনীতি (Politics)
    - খেলাধুলা (Sports) 
    - অর্থনীতি (Economics)
    - আন্তর্জাতিক (International)
    - প্রযুক্তি (Technology)
    - বিনোদন (Entertainment)
    
    **Usage Example**: Get trending sports phrases from last 3 days
    """
    try:
        from app.services.category_service import CategoryTrendingService
        
        service = CategoryTrendingService(db)
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get category phrases
        phrases = service.get_category_trending_phrases(
            category=category,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        # Filter by phrase type if specified
        if phrase_type:
            phrases = [p for p in phrases if p.get('phrase_type') == phrase_type]
        
        return {
            "category": category,
            "phrases": phrases,
            "period": f"Last {days} days",
            "date_range": f"{start_date} to {end_date}",
            "total_count": len(phrases),
            "phrase_type_filter": phrase_type,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting category phrases: {str(e)}")

@router.get("/categories/activity", summary="🔥 Get top categories by trending activity", tags=["Category Analysis"])
def get_top_categories_activity(
    days: int = Query(7, description="Number of days to analyze activity (default: 7)"),
    limit: int = Query(10, description="Number of top categories to return (default: 10)"),
    db: Session = Depends(get_db)
):
    """
    Get top categories ranked by trending phrase activity and engagement
    
    **Metrics Included**:
    - Total trending phrases per category
    - Average trend score
    - Total frequency across newspapers
    - Activity ranking
    
    **Use Cases**:
    - Identify most active news categories
    - Track category engagement trends
    - Editorial decision making
    """
    try:
        from app.services.category_service import CategoryTrendingService
        
        service = CategoryTrendingService(db)
        
        # Get today's activity analysis
        top_categories = service.get_top_categories_by_activity(
            analysis_date=date.today(),
            limit=limit
        )
        
        # Add ranking and additional metrics
        for i, category_stat in enumerate(top_categories, 1):
            category_stat['rank'] = i
            category_stat['activity_level'] = (
                "Very High" if category_stat['avg_score'] > 5.0 else
                "High" if category_stat['avg_score'] > 3.0 else
                "Medium" if category_stat['avg_score'] > 1.0 else
                "Low"
            )
        
        return {
            "top_categories": top_categories,
            "analysis_date": str(date.today()),
            "period_analyzed": f"Last {days} days",
            "total_categories": len(top_categories),
            "analysis_timestamp": datetime.now().isoformat(),
            "metrics_explanation": {
                "avg_score": "Average trending score across all phrases",
                "phrase_count": "Total number of trending phrases",
                "total_frequency": "Sum of frequency across all newspapers"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting category activity: {str(e)}")

@router.get("/categories/trends", summary="📊 Category trend comparison over time", tags=["Category Analysis"])
def get_category_trends_comparison(
    days: int = Query(7, description="Number of days to analyze trends (default: 7)"),
    db: Session = Depends(get_db)
):
    """
    Compare trending activity across categories over time with trend analysis
    
    **Trend Analysis Features**:
    - Daily trend scores for each category
    - Trend direction (increasing/decreasing)
    - Trend strength calculation
    - Comparative analysis between categories
    
    **Business Value**:
    - Track news cycle patterns
    - Identify emerging topics
    - Content strategy insights
    """
    try:
        from app.services.category_service import CategoryTrendingService
        
        service = CategoryTrendingService(db)
        
        # Get trend comparison data
        trends = service.get_category_trends_comparison(days=days)
        
        # Calculate overall insights
        total_categories = len(trends)
        increasing_trends = sum(1 for t in trends.values() if t.get('trend_direction') == 'increasing')
        decreasing_trends = total_categories - increasing_trends
        
        # Find most and least active categories
        if trends:
            most_active = max(trends.items(), key=lambda x: x[1].get('second_half_avg', 0))
            least_active = min(trends.items(), key=lambda x: x[1].get('second_half_avg', 0))
        else:
            most_active = least_active = None
        
        return {
            "category_trends": trends,
            "analysis_period": f"Last {days} days",
            "categories_analyzed": total_categories,
            "trend_summary": {
                "increasing_trends": increasing_trends,
                "decreasing_trends": decreasing_trends,
                "most_active_category": most_active[0] if most_active else None,
                "least_active_category": least_active[0] if least_active else None
            },
            "analysis_timestamp": datetime.now().isoformat(),
            "methodology": "Compares first half vs second half of time period"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting category trends: {str(e)}")

@router.get("/categories/distribution", summary="📋 Article distribution by category", tags=["Category Analysis"])
def get_category_distribution(
    days: int = Query(30, description="Number of days to analyze distribution (default: 30)"),
    db: Session = Depends(get_db)
):
    """
    Get distribution of articles across categories with comprehensive statistics
    
    **Distribution Metrics**:
    - Article count per category
    - Percentage distribution
    - Category coverage analysis
    - Source diversity per category
    
    **Analytics Use Cases**:
    - Content audit and analysis
    - Editorial balance assessment
    - Category performance tracking
    """
    try:
        from app.services.category_service import CategoryTrendingService
        
        service = CategoryTrendingService(db)
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get distribution data
        distribution = service.get_category_distribution(
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate percentages and statistics
        total_articles = sum(distribution.values()) if distribution else 0
        distribution_with_percentages = []
        
        for category, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_articles * 100) if total_articles > 0 else 0
            distribution_with_percentages.append({
                "category": category,
                "article_count": count,
                "percentage": round(percentage, 2),
                "rank": len(distribution_with_percentages) + 1
            })
        
        # Calculate diversity metrics
        category_count = len(distribution)
        avg_articles_per_category = total_articles / category_count if category_count > 0 else 0
        
        return {
            "category_distribution": distribution_with_percentages,
            "period": f"Last {days} days",
            "date_range": f"{start_date} to {end_date}",
            "summary_statistics": {
                "total_articles": total_articles,
                "total_categories": category_count,
                "avg_articles_per_category": round(avg_articles_per_category, 2),
                "most_covered_category": distribution_with_percentages[0]['category'] if distribution_with_percentages else None,
                "least_covered_category": distribution_with_percentages[-1]['category'] if distribution_with_percentages else None
            },
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting category distribution: {str(e)}")

@router.post("/categories/analyze", summary="🔍 Analyze articles for category-wise trending phrases", tags=["Category Analysis"])
def analyze_category_phrases(
    request: TrendingPhrasesRequest,
    save_to_db: bool = Query(False, description="Save results to database (default: false)"),
    db: Session = Depends(get_db)
):
    """
    Analyze provided articles to extract category-wise trending phrases
    
    **Analysis Process**:
    1. Categorize each article using enhanced detection
    2. Extract trending phrases by category
    3. Score and rank phrases within categories
    4. Optionally save results to database
    
    **Input**: List of article texts or URLs
    **Output**: Category-wise trending phrase analysis
    
    **Use Cases**:
    - Real-time content analysis
    - Editorial trend identification
    - Category-specific trending insights
    """
    try:
        from app.services.category_service import CategoryTrendingService
        
        service = CategoryTrendingService(db)
        
        # Convert request data to articles list
        articles = []
        for i, text in enumerate(request.texts):
            articles.append({
                'title': f"Article {i+1}",
                'content': text,
                'url': f"https://example.com/article{i+1}",
                'source': 'api_analysis'
            })
        
        # Analyze category phrases
        category_phrases = service.analyze_category_phrases_by_content(
            articles=articles,
            min_phrase_length=3,
            max_phrases_per_category=20
        )
        
        # Calculate analysis statistics
        total_phrases = sum(len(phrases) for phrases in category_phrases.values())
        categories_found = len(category_phrases)
        
        # Save to database if requested
        saved_count = 0
        if save_to_db:
            saved_count = service.save_category_trending_phrases(
                category_phrases,
                date.today(),
                source="api_analysis"
            )
        
        return {
            "category_phrases": category_phrases,
            "analysis_date": str(date.today()),
            "analysis_statistics": {
                "categories_found": categories_found,
                "total_phrases": total_phrases,
                "articles_analyzed": len(articles),
                "avg_phrases_per_category": round(total_phrases / categories_found, 2) if categories_found > 0 else 0
            },
            "database_operation": {
                "saved_to_db": save_to_db,
                "phrases_saved": saved_count if save_to_db else 0
            },
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing category phrases: {str(e)}")

@router.get("/categories/summary", summary="📑 Complete category analysis summary", tags=["Category Analysis"])
def get_category_analysis_summary(
    days: int = Query(7, description="Number of days for comprehensive analysis (default: 7)"),
    db: Session = Depends(get_db)
):
    """
    Get a comprehensive summary of all category-related analytics
    
    **Complete Overview Including**:
    - Top active categories
    - Category distribution
    - Trending phrases by top categories
    - Recent trend directions
    - Overall category performance
    
    **Perfect for**: Dashboards, executive summaries, content strategy meetings
    """
    try:
        from app.services.category_service import CategoryTrendingService
        
        service = CategoryTrendingService(db)
        
        # Get top categories
        top_categories = service.get_top_categories_by_activity(limit=5)
        
        # Get distribution
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        distribution = service.get_category_distribution(start_date=start_date, end_date=end_date)
        
        # Get trends for top categories
        trends = service.get_category_trends_comparison(days=days)
        
        # Get sample trending phrases for top 3 categories
        category_samples = {}
        for cat_stat in top_categories[:3]:
            category = cat_stat['category']
            phrases = service.get_category_trending_phrases(
                category=category,
                start_date=start_date,
                end_date=end_date,
                limit=5
            )
            category_samples[category] = phrases
        
        return {
            "analysis_period": f"Last {days} days",
            "date_range": f"{start_date} to {end_date}",
            "top_active_categories": top_categories,
            "category_distribution": distribution,
            "trending_samples": category_samples,
            "trend_analysis": {
                "total_categories_with_trends": len(trends),
                "increasing_categories": [cat for cat, data in trends.items() if data.get('trend_direction') == 'increasing'],
                "decreasing_categories": [cat for cat, data in trends.items() if data.get('trend_direction') == 'decreasing']
            },
            "summary_statistics": {
                "total_articles": sum(distribution.values()) if distribution else 0,
                "categories_tracked": len(distribution) if distribution else 0,
                "most_active_category": top_categories[0]['category'] if top_categories else None,
                "analysis_coverage": "Complete"
            },
            "generated_at": datetime.now().isoformat(),
            "api_endpoints": {
                "category_detection": "/api/v2/categories/detect",
                "trending_by_category": "/api/v2/categories/trending",
                "category_activity": "/api/v2/categories/activity",
                "trend_comparison": "/api/v2/categories/trends",
                "distribution_analysis": "/api/v2/categories/distribution"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating category summary: {str(e)}")

async def update_category_wise_final_with_reddit(category_wise_trending, target_categories):
    """Helper function to re-run LLM selection with updated category data including Reddit integration"""
    try:
        import os
        from groq import Groq
        import re
        
        # Create category-wise prompt for final selection
        category_prompt_sections = []
        total_input_words = 0
        
        for category, words in category_wise_trending.items():
            if words and len(words) > 0:
                # Take up to 8 words per category (or 16 for আন্তর্জাতিক)
                word_limit = 16 if category == 'আন্তর্জাতিক' else 8
                limited_words = words[:word_limit]
                total_input_words += len(limited_words)
                
                words_text = "\\n".join([f"  {i}. {word}" for i, word in enumerate(limited_words, 1)])
                section = f"{category} ({len(limited_words)}টি):\\n{words_text}"
                category_prompt_sections.append(section)
        
        if not category_prompt_sections:
            return None
            
        categories_text = "\\n\\n".join(category_prompt_sections)
        
        client = Groq(api_key=os.getenv('GROQ_API_KEY_NEWSPAPER'))
        
        final_selection_prompt = f"""তুমি একজন বিশেষজ্ঞ বাংলাদেশি সংবাদ বিশ্লেষক।আপনাকে নিম্নলিখিত ক্যাটেগরি অনুযায়ী ট্রেন্ডিং শব্দগুলো থেকে প্রতিটি ক্যাটেগরি থেকে সবচেয়ে গুরুত্বপূর্ণ 10টি করে শব্দ বেছে নিতে হবে। এমন শব্দ/বাক্যাংশ দাও যেটা শুনলে মানুষ বুঝতে পারবে যে এটা কীসের সাথে সম্পর্কিত। যার একটা অর্থ থাকবে, এমন কিছু দেবে না যেটা অর্থহীন এবং যেটা দেখলে কনটেক্সট বোঝা যাবে না।

ক্যাটেগরি অনুযায়ী ট্রেন্ডিং শব্দ:
{categories_text}

নির্বাচনের নিয়মাবলী:
1. প্রতিটি ক্যাটেগরি থেকে সবচেয়ে প্রাসঙ্গিক ১০টি শব্দ নির্বাচন করুন
2. প্রতিটি শব্দ/বাক্যাংশ ২-৪ শব্দের মধ্যে এবং স্পষ্ট অর্থবোধক হতে হবে
3. এক ক্যাটেগরিতে একই টপিক বা অর্থের কাছাকাছি শব্দ থাকবে না, প্রতিটি শব্দ ইউনিক ও প্রসঙ্গভিত্তিক অর্থবহ হতে হবে
4. response শুধুমাত্র bangla language a deo
5. ব্যক্তিগত নাম এড়িয়ে চলুন, বিষয়বস্তুর উপর ফোকাস করুন
6. সাম্প্রতিক ও জনপ্রিয় বিষয়গুলো অগ্রাধিকার দিন

আউটপুট ফরম্যাট:
প্রতিটি ক্যাটেগরির জন্য নিম্নরূপ ফরম্যাটে দিন:

ক্যাটেগরি নাম:
1. শব্দ১
2. শব্দ২
3. শব্দ৩
4. শব্দ৪
...
10. শব্দ১০

অন্য ক্যাটেগরি নাম:
1. শব্দ১
2. শব্দ২
...
...
10. শব্দ১০

শুধুমাত্র উপরের ফরম্যাটে উত্তর দিন। অতিরিক্ত ব্যাখ্যা বা মন্তব্য যোগ করবেন না।"""
        
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": final_selection_prompt}],
            temperature=0.2,
            max_tokens=1200
        )
        
        llm_response = completion.choices[0].message.content.strip()
        
        # Parse LLM response into category_wise_final
        category_wise_final = {}
        current_category = None
        lines = llm_response.split('\\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a category header
            if line.endswith(':') and not re.match(r'^[১২৩৪৫৬৭৮৯1-8][\\.\)]\s*', line):
                current_category = line.replace(':', '').strip()
                if current_category not in category_wise_final:
                    category_wise_final[current_category] = []
                continue
            
            # Extract numbered items for current category
            if current_category and re.match(r'^[১২৩৪৫৬৭৮৯1-8][\\.\)]\s*', line):
                if len(category_wise_final[current_category]) >= 5:
                    continue
                
                # Remove number prefix and clean up
                word = re.sub(r'^[১২৩৪৫৬৭৮৯1-8][\\.\)]\s*', '', line).strip()
                word = re.sub(r'[।\\.]+$', '', word).strip()
                
                if word and len(word) > 1 and word not in category_wise_final[current_category]:
                    category_wise_final[current_category].append(word)
        
        return category_wise_final
        
    except Exception as e:
        print(f"⚠️ Error in update_category_wise_final_with_reddit: {e}")
        return None

@router.post("/api/generate-candidates", summary="Hybrid analysis with newspaper and Reddit support")
async def hybrid_generate_candidates(
    sources: List[str] = Query(default=["newspaper", "reddit"], description="Sources to analyze: newspaper, reddit"),
    mode: str = Query(default="sequential", description="Processing mode: sequential or parallel"),
    db: Session = Depends(get_db)
):
    """
    Hybrid approach: Analyze newspapers and Reddit separately or together
    - Uses separate API keys for each source
    - Supports parallel and sequential processing
    - Merges results and generates final top 15 trending words
    """
    import asyncio
    import os
    from app.routes.helpers import fetch_news  # Removed generate_trending_word_candidates_realtime_with_save
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "sources_requested": sources,
        "results": {},
        "errors": {},
        "final_trending_words": []
    }
    
    try:
        async def process_newspaper_data():
            """Process newspaper data with dedicated API key (category-wise LLM, 8 words, 50s delay)"""
            import asyncio
            print("📰 Processing newspaper data (category-wise LLM, 8 words, 50s delay)...")
            original_key = os.environ.get("GROQ_API_KEY")
            newspaper_key = os.environ.get("GROQ_API_KEY_NEWSPAPER")
            if newspaper_key:
                os.environ["GROQ_API_KEY"] = newspaper_key

            from app.services.filtered_newspaper_service import FilteredNewspaperScraper
            from app.services.category_llm_analyzer import (
                get_জাতীয়_trending_words, get_অর্থনীতি_trending_words, get_রাজনীতি_trending_words,
                get_বিনোদন_trending_words, get_খেলাধুলা_trending_words,
                get_শিক্ষা_trending_words,
                get_স্বাস্থ্য_trending_words, get_বিজ্ঞান_trending_words,
                get_আন্তর্জাতিক_trending_words, get_প্রযুক্তি_trending_words,
                get_সাহিত্য_সংস্কৃতি_trending_words, get_ক্ষুদ্র_নৃগোষ্ঠী_trending_words
            )
            from groq import Groq
            import re

            TARGET_CATEGORIES = [
                'জাতীয়', 'আন্তর্জাতিক', 'অর্থনীতি', 'রাজনীতি',  'বিনোদন', 
                'খেলাধুলা', 'শিক্ষা', 'স্বাস্থ্য',  'বিজ্ঞান', 'প্রযুক্তি',
                'সাহিত্য-সংস্কৃতি', 'ক্ষুদ্র নৃগোষ্ঠী'
            ]
            print(f"🚀 Starting filtered newspaper scraping for {len(TARGET_CATEGORIES)} categories...")
            scraper = FilteredNewspaperScraper(TARGET_CATEGORIES)
            results = scraper.scrape_all_newspapers()
            print(f"📊 Scraped {results['scraping_info']['total_articles']} articles")

            category_functions = {
                'জাতীয়': get_জাতীয়_trending_words,
                'আন্তর্জাতিক': get_আন্তর্জাতিক_trending_words,
                'অর্থনীতি': get_অর্থনীতি_trending_words,
                'রাজনীতি': get_রাজনীতি_trending_words,
                # 'লাইফস্টাইল': get_লাইফস্টাইল_trending_words,
                'বিনোদন': get_বিনোদন_trending_words,
                'খেলাধুলা': get_খেলাধুলা_trending_words,
                # 'ধর্ম': get_ধর্ম_trending_words,
                # 'চাকরি': get_চাকরি_trending_words,
                'শিক্ষা': get_শিক্ষা_trending_words,
                'স্বাস্থ্য': get_স্বাস্থ্য_trending_words,
                # 'মতামত': get_মতামত_trending_words,
                'বিজ্ঞান': get_বিজ্ঞান_trending_words,
                'প্রযুক্তি': get_প্রযুক্তি_trending_words,
                'সাহিত্য-সংস্কৃতি': get_সাহিত্য_সংস্কৃতি_trending_words,
                'ক্ষুদ্র নৃগোষ্ঠী': get_ক্ষুদ্র_নৃগোষ্ঠী_trending_words
            }

            all_trending_words = []
            category_wise_trending = {}
            category_wise_final = {}
            llm_selection_stats = {}
            client = Groq(api_key=os.getenv('GROQ_API_KEY_NEWSPAPER'))
            total_input_words = 0
            llm_responses = {}

            for idx, category in enumerate(TARGET_CATEGORIES):
                articles = results['category_wise_articles'][category]
                if articles:
                    try:
                        print(f"\n🟢 [{idx+1}/{len(TARGET_CATEGORIES)}] Calling LLM for category: {category} ({len(articles)} articles)...")
                        # Call the category-specific LLM function (these functions are synchronous, no await needed)
                        trending_func = category_functions[category]
                        trending_words = trending_func(articles)  # Remove await and limit parameter
                        # Ensure only 8 words (functions should return 8 but just in case)
                        trending_words = trending_words if trending_words else []
                        category_wise_trending[category] = trending_words
                        all_trending_words.extend(trending_words)
                        llm_responses[category] = trending_words
                        print(f"✅ LLM returned {len(trending_words)} words for {category}")
                    except Exception as e:
                        print(f"⚠️ LLM call failed for {category}: {e}")
                        category_wise_trending[category] = []
                        llm_responses[category] = []
                else:
                    print(f"⚠️ No articles found for {category}, skipping LLM call.")
                    category_wise_trending[category] = []
                    llm_responses[category] = []
                # Wait 50 seconds between LLM calls except after the last category
                if idx < len(TARGET_CATEGORIES) - 1:
                    print(f"⏳ Waiting 50 seconds before next category...")
                    import asyncio
                    await asyncio.sleep(50)

            print("\n🎯 All category-wise LLM calls complete. Running final selection...")
            # Final LLM selection (5 per category, using helper)
            category_wise_final = await update_category_wise_final_with_reddit(category_wise_trending, TARGET_CATEGORIES)
            final_trending_words = []
            if category_wise_final:
                for words in category_wise_final.values():
                    final_trending_words.extend(words)
            llm_selection_stats = {
                "total_input_categories": len(TARGET_CATEGORIES),
                "total_input_words": sum(len(w) for w in category_wise_trending.values()),
                "selected_words": len(final_trending_words),
                "categories_processed": len(category_wise_final) if category_wise_final else 0,
                "selection_method": "Category-wise LLM (8 per category, 50s delay)",
                "llm_response": str(category_wise_final)  # Truncated for brevity
            }
            print(f"✅ Final selection complete. Returning results.")
            return {
                "message": "Category-wise trending words generated successfully using filtered newspaper scraping and LLM analysis!",
                "scraping_info": results['scraping_info'],
                "category_wise_trending_words": category_wise_trending,
                "category_wise_articles": results['category_wise_articles'],  # Include articles for frequency calculation
                "all_trending_words": all_trending_words,
                "category_wise_final": category_wise_final,
                "final_trending_words": final_trending_words,
                "llm_selection": llm_selection_stats,
                "statistics": {
                    "total_articles_scraped": results['scraping_info']['total_articles'],
                    "categories_processed": len([c for c in TARGET_CATEGORIES if category_wise_trending.get(c, [])]),
                    "total_trending_words": len(all_trending_words),
                    "final_selected_words": len(final_trending_words),
                    "scraping_time_seconds": results['scraping_info'].get('scraping_time_seconds', 0)
                }
            }

        async def process_reddit_data():
            """Process Reddit data with dedicated API key"""
            print("🔴 Processing Reddit data...")
            original_key = os.environ.get("GROQ_API_KEY")
            reddit_key = os.environ.get("GROQ_API_KEY_REDDIT")
            if reddit_key:
                os.environ["GROQ_API_KEY"] = reddit_key

            from app.services.reddit_data_scrapping import RedditDataScrapper
            
            try:
                reddit_scraper = RedditDataScrapper()
                result = reddit_scraper.run_comprehensive_analysis(posts_per_subreddit=20)
                
                # Extract trending words from Reddit analysis
                reddit_trending_words = []
                if result and 'comprehensive_response' in result:
                    comp_response = result['comprehensive_response']
                    if comp_response and comp_response.get('status') == 'success':
                        reddit_trending_words = comp_response.get('trending_words', [])
                
                return {
                    "source": "reddit",
                    "trending_words": reddit_trending_words,
                    "raw_result": result,
                    "total_words": len(reddit_trending_words)
                }
            except Exception as e:
                print(f"❌ Reddit processing failed: {e}")
                return {
                    "source": "reddit", 
                    "trending_words": [],
                    "error": str(e),
                    "total_words": 0
                }
            finally:
                # Restore original API key
                if original_key:
                    os.environ["GROQ_API_KEY"] = original_key

        # Process sources based on mode
        if mode == "parallel" and len(sources) > 1:
            # Run newspaper and Reddit processing in parallel
            tasks = []
            if "newspaper" in sources:
                tasks.append(process_newspaper_data())
            if "reddit" in sources:
                tasks.append(process_reddit_data())
            
            source_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in source_results:
                if isinstance(result, Exception):
                    results["errors"]["processing"] = str(result)
                elif isinstance(result, dict):
                    source = result.get("source", "unknown")
                    results["results"][source] = result
        else:
            # Sequential processing
            if "newspaper" in sources:
                try:
                    newspaper_result = await process_newspaper_data()
                    results["results"]["newspaper"] = newspaper_result
                except Exception as e:
                    results["errors"]["newspaper"] = str(e)
            
            if "reddit" in sources:
                try:
                    reddit_result = await process_reddit_data()
                    results["results"]["reddit"] = reddit_result
                except Exception as e:
                    results["errors"]["reddit"] = str(e)

        # Merge final trending words from all sources
        final_words = []
        for source_name, source_result in results["results"].items():
            if source_name == "newspaper":
                # Get words from newspaper analysis
                if "final_trending_words" in source_result:
                    final_words.extend(source_result["final_trending_words"])
                elif "category_wise_final" in source_result:
                    # Flatten category-wise words
                    for category_words in source_result["category_wise_final"].values():
                        final_words.extend(category_words)
            elif source_name == "reddit":
                # Get words from Reddit analysis
                final_words.extend(source_result.get("trending_words", []))

        # Remove duplicates while preserving order
        seen = set()
        unique_final_words = []
        for word in final_words:
            if word not in seen:
                unique_final_words.append(word)
                seen.add(word)

        # Limit to top 15 words
        results["final_trending_words"] = unique_final_words[:15]

        # FINAL LLM INTEGRATION: Create category-wise final selection from category-word pairs
        print(f"\n🤖 Starting FINAL LLM integration using category-wise data...")
        
        # Get category-wise data from newspaper results (already organized by categories)
        newspaper_category_data = {}
        reddit_words = []
        
        # Extract category-wise data from newspaper results
        if "newspaper" in results["results"]:
            newspaper_result = results["results"]["newspaper"]
            if "category_wise_trending_words" in newspaper_result:
                newspaper_category_data = newspaper_result["category_wise_trending_words"]
                print(f"📰 Found newspaper data with {len(newspaper_category_data)} categories")
        
        # Extract Reddit words (will be added to 'আন্তর্জাতিক' category)
        if "reddit" in results["results"]:
            reddit_result = results["results"]["reddit"]
            reddit_words = reddit_result.get("trending_words", [])
            print(f"📡 Found {len(reddit_words)} Reddit words to add to আন্তর্জাতিক category")
        
        # Merge Reddit words into 'আন্তর্জাতিক' category
        if reddit_words and 'আন্তর্জাতিক' in newspaper_category_data:
            existing_intl_words = newspaper_category_data['আন্তর্জাতিক']
            combined_intl_words = existing_intl_words + reddit_words
            # Remove duplicates while preserving order
            seen = set()
            unique_intl_words = []
            for word in combined_intl_words:
                if word not in seen:
                    unique_intl_words.append(word)
                    seen.add(word)
            newspaper_category_data['আন্তর্জাতিক'] = unique_intl_words
            print(f"🌍 Enhanced আন্তর্জাতিক category: {len(unique_intl_words)} total words")
        
        if newspaper_category_data:
            try:
                from groq import Groq
                
                # Use newspaper API key for final integration
                client = Groq(api_key=os.getenv('GROQ_API_KEY_NEWSPAPER'))
                
                # Create category-wise formatted prompt
                category_sections = []
                for category, words in newspaper_category_data.items():
                    if words:
                        # Take 8 words per category (16 for আন্তর্জাতিক)
                        word_limit = 16 if category == 'আন্তর্জাতিক' else 8
                        limited_words = words[:word_limit]
                        
                        words_text = "\n".join([f"  - {word}" for word in limited_words])
                        section = f"**{category}** ({len(limited_words)} words):\n{words_text}"
                        category_sections.append(section)
                
                category_data_text = "\n\n".join(category_sections)
                
                final_integration_prompt = f"""তুমি একজন বিশেষজ্ঞ বাংলাদেশি সংবাদ বিশ্লেষক।আপনাকে নিম্নলিখিত ক্যাটেগরি অনুযায়ী ট্রেন্ডিং শব্দগুলো থেকে প্রতিটি ক্যাটেগরি থেকে সবচেয়ে গুরুত্বপূর্ণ 10টি করে শব্দ বেছে নিতে হবে। এমন শব্দ/বাক্যাংশ দাও যেটা শুনলে মানুষ বুঝতে পারবে যে এটা কীসের সাথে সম্পর্কিত। যার একটা অর্থ থাকবে, এমন কিছু দেবে না যেটা অর্থহীন এবং যেটা দেখলে কনটেক্সট বোঝা যাবে না।

ক্যাটেগরি-ভিত্তিক ট্রেন্ডিং শব্দ:
{category_data_text}

নির্বাচনের নিয়মাবলী:
1. প্রতিটি ক্যাটেগরি থেকে সবচেয়ে প্রাসঙ্গিক ১০টি শব্দ নির্বাচন করুন
2. প্রতিটি শব্দ/বাক্যাংশ ২-৪ শব্দের মধ্যে এবং স্পষ্ট অর্থবোধক হতে হবে
3. এক ক্যাটেগরিতে একই টপিক বা অর্থের কাছাকাছি শব্দ থাকবে না, প্রতিটি শব্দ ইউনিক ও প্রসঙ্গভিত্তিক অর্থবহ হতে হবে
4. response শুধুমাত্র bangla language a deo
5. ব্যক্তিগত নাম এড়িয়ে চলুন, বিষয়বস্তুর উপর ফোকাস করুন
6. সাম্প্রতিক ও জনপ্রিয় বিষয়গুলো অগ্রাধিকার দিন

আউটপুট ফরম্যাট:
প্রতিটি ক্যাটেগরির জন্য নিম্নরূপ ফরম্যাটে দিন:

ক্যাটেগরি নাম:
1. শব্দ১
2. শব্দ২
3. শব্দ৩
4. শব্দ৪
...
10. শব্দ১০

অন্য ক্যাটেগরি নাম:
1. শব্দ১
2. শব্দ২
...
...
10. শব্দ১০

শুধুমাত্র উপরের ফরম্যাটে উত্তর দিন। অতিরিক্ত ব্যাখ্যা বা মন্তব্য যোগ করবেন না।"""
                
                print("🤖 Calling final integration LLM with category-wise data...")
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": final_integration_prompt}],
                    temperature=0.3,
                    max_tokens=5000
                )
                
                llm_response = completion.choices[0].message.content.strip()
                print(f"🔍 Final Integration LLM Response:\n{llm_response}")
                
                # Parse TEXT format response (not JSON)
                category_wise_final = {}
                current_category = None
                lines = llm_response.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check if this is a category header (ends with colon and doesn't start with number)
                    if line.endswith(':') and not re.match(r'^[১২৩৪৫৬৭৮৯১০1-9][\.\)]\s*', line):
                        current_category = line.replace(':', '').strip()
                        if current_category not in category_wise_final:
                            category_wise_final[current_category] = []
                        print(f"✅ Found category: '{current_category}'")
                        continue
                    
                    # Extract numbered items for current category (support both English and Bengali numbers)
                    if current_category and re.match(r'^[১২৩৪৫৬৭৮৯১০][\.\)]\s*|^1[0][\.\)]\s*|^[1-9][\.\)]\s*', line):
                        # Remove number prefix and clean up
                        word = re.sub(r'^[১২৩৪৫৬৭৮৯১০][\.\)]\s*|^1[0][\.\)]\s*|^[1-9][\.\)]\s*', '', line).strip()
                        # Remove any trailing punctuation or extra spaces
                        word = re.sub(r'[।\.]+$', '', word).strip()
                        
                        if word and len(word) > 1:
                            category_wise_final[current_category].append(word)
                            print(f"✅ Added word to {current_category}: '{word}' ({len(category_wise_final[current_category])}/total)")
                
                print(f"✅ Successfully parsed text response with {len(category_wise_final)} categories")
                
                # 🔍 FREQUENCY CALCULATION: Calculate frequency for all selected phrases
                print(f"\n🔍 FREQUENCY CALCULATION: Calculating frequency for category-wise phrases...")
                print(f"🔍 DEBUG: Total categories to process: {len(category_wise_final)}")
                
                # Convert words to dictionary format with frequency
                from app.services.category_llm_analyzer import calculate_phrase_frequency_in_articles
                
                category_wise_final_with_freq = {}
                total_phrases_calculated = 0
                
                # Get all articles from newspaper result for frequency calculation
                all_articles = []
                if "newspaper" in results["results"] and "category_wise_articles" in results["results"]["newspaper"]:
                    print(f"🔍 DEBUG: Found newspaper category_wise_articles")
                    newspaper_articles = results["results"]["newspaper"]["category_wise_articles"]
                    # Collect all articles from all categories
                    for cat_name, cat_articles in newspaper_articles.items():
                        all_articles.extend(cat_articles)
                    print(f"🔍 DEBUG: Total articles collected for frequency calculation: {len(all_articles)}")
                else:
                    print(f"🔍 DEBUG: No newspaper articles found for frequency calculation")
                
                for category, words in category_wise_final.items():
                    print(f"🔍 Processing category '{category}' with {len(words)} words...")
                    
                    # Get category-specific articles if available, else use all articles
                    category_articles = []
                    if "newspaper" in results["results"] and "category_wise_articles" in results["results"]["newspaper"]:
                        category_articles = results["results"]["newspaper"]["category_wise_articles"].get(category, [])
                        print(f"🔍 DEBUG: Found {len(category_articles)} category-specific articles for '{category}'")
                    
                    # If no category-specific articles, use all articles as fallback
                    if not category_articles and all_articles:
                        category_articles = all_articles
                        print(f"🔍 DEBUG: Using all {len(all_articles)} articles as fallback for '{category}'")
                    
                    category_wise_final_with_freq[category] = []
                    
                    for word_text in words:
                        if isinstance(word_text, str) and word_text.strip():
                            actual_frequency = 1  # Default frequency
                            
                            # Calculate actual frequency if articles are available
                            if category_articles:
                                try:
                                    freq_stats = calculate_phrase_frequency_in_articles(word_text, category_articles)
                                    actual_frequency = freq_stats.get('frequency', 1)
                                    print(f"🔍 [{total_phrases_calculated+1}] '{word_text}' → calculated frequency: {actual_frequency}")
                                except Exception as e:
                                    print(f"🔍 [{total_phrases_calculated+1}] '{word_text}' → frequency calculation failed: {e}, using default: 1")
                            else:
                                print(f"🔍 [{total_phrases_calculated+1}] '{word_text}' → no articles available, using default frequency: 1")
                            
                            # Create word info dictionary
                            word_info = {
                                'word': word_text,
                                'frequency': actual_frequency,
                                'category': category,
                                'source': 'hybrid_llm_selection'
                            }
                            
                            category_wise_final_with_freq[category].append(word_info)
                            total_phrases_calculated += 1
                
                # Replace the original category_wise_final with frequency-enhanced version
                category_wise_final = category_wise_final_with_freq
                print(f"✅ FREQUENCY CALCULATION COMPLETE: {total_phrases_calculated} phrases processed")
                
                print(f"\n🎯 Final Integration Complete!")
                print(f"📊 Categories created: {len(category_wise_final)}")
                for category, words in category_wise_final.items():
                    # Extract word text for display since words are now dictionaries
                    word_texts = []
                    for word_info in words[:3]:
                        if isinstance(word_info, dict) and 'word' in word_info:
                            word_texts.append(word_info['word'])
                        else:
                            word_texts.append(str(word_info))
                    print(f"   {category}: {len(words)} words - {', '.join(word_texts)}...")
                
                # Add category_wise_final to results for frontend consumption
                results["category_wise_final"] = category_wise_final
                results["llm_response"] = llm_response  # Add for debugging
                
            except Exception as e:
                print(f"⚠️ Final LLM integration failed: {e}")
                # Fallback: Create simple categories from newspaper data
                if newspaper_category_data:
                    fallback_categories = {}
                    for category, words in newspaper_category_data.items():
                        fallback_categories[category] = words[:10]  # Take first 10 words
                    results["category_wise_final"] = fallback_categories
                else:
                    results["category_wise_final"] = {
                        "সাধারণ": unique_final_words[:10],
                        "ট্রেন্ডিং": unique_final_words[10:20] if len(unique_final_words) > 10 else []
                    }
        else:
            print("⚠️ No category-wise data available for final integration")
            results["category_wise_final"] = {}
        
        print(f"\n✅ HYBRID ANALYSIS COMPLETE!")
        print(f"📊 Total sources processed: {len(results['results'])}")
        print(f"🎯 Final trending words: {len(results['final_trending_words'])}")
        print(f"📂 Categories created: {len(results.get('category_wise_final', {}))}")

        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in hybrid candidate generation: {str(e)}")

@router.post("/set_word_of_the_day", summary="Set today's word of the day")
def set_word_of_the_day(word: str, db: Session = Depends(get_db)):
    """Set the word of the day for today"""
    today = date.today()
    
    # Check if word already exists for today
    existing_word = db.query(Word).filter(Word.date == today).first()
    
    if existing_word:
        existing_word.word = word
    else:
        new_word = Word(date=today, word=word)
        db.add(new_word)
    
    db.commit()
    
    return {
        "message": f"Word of the day set successfully!",
        "date": str(today),
        "word": word
    }

@router.post("/set_category_words", summary="Set today's words with category information")
def set_category_words(
    request: dict, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Set words of the day with category information - supports multiple words per category (Admin only)"""
    from app.models.word import CategoryTrendingPhrase, TrendingPhrase
    
    today = date.today()
    selected_words = request.get('words', [])
    
    if not selected_words:
        raise HTTPException(status_code=400, detail="No words provided")
    
    try:
        # Clear existing data for today
        db.query(CategoryTrendingPhrase).filter(CategoryTrendingPhrase.date == today).delete()
        db.query(TrendingPhrase).filter(TrendingPhrase.date == today).delete()
        
        # Save category-wise selected words
        saved_count = 0
        all_words = []
        
        for word_info in selected_words:
            word = word_info.get('word', '').strip()
            category = word_info.get('category', 'অজানা').strip()
            
            if word and category:
                # Save to CategoryTrendingPhrase table
                category_phrase = CategoryTrendingPhrase(
                    date=today,
                    category=category,
                    phrase=word,
                    score=100.0,  # High score for selected words
                    frequency=1,
                    phrase_type='selected',
                    source='user_selection'
                )
                db.add(category_phrase)
                
                # Save to TrendingPhrase table for trending analysis using smart frequency handling
                from app.routes.helpers import add_or_update_trending_phrase
                add_or_update_trending_phrase(
                    db=db,
                    date=today,
                    phrase=word,
                    score=100.0,
                    frequency=1,
                    phrase_type='selected',
                    source='user_selection'
                )
                
                saved_count += 1
                all_words.append(word)
        
        # Save all selected words as today's words in words table
        if selected_words:
            main_word = selected_words[0].get('word', '')
            
            # Prepare selected words data for JSON storage
            words_data = []
            for word_info in selected_words:
                words_data.append({
                    'word': word_info.get('word', ''),
                    'category': word_info.get('category', ''),
                    'originalText': word_info.get('originalText', '')
                })
            
            existing_word = db.query(Word).filter(Word.date == today).first()
            
            if existing_word:
                existing_word.word = main_word
                existing_word.selected_words = words_data
            else:
                new_word = Word(
                    date=today, 
                    word=main_word,
                    selected_words=words_data
                )
                db.add(new_word)
        
        db.commit()
        
        return {
            "message": f"Successfully saved {saved_count} category words for today!",
            "date": str(today),
            "saved_words": saved_count,
            "words": selected_words,
            "all_selected_words": all_words,
            "main_word_of_day": selected_words[0].get('word', '') if selected_words else None
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving category words: {str(e)}")

@router.get("/phrase-frequency", summary="Get phrase frequency data over time")
def get_phrase_frequency_data(
    phrase: str = Query(..., description="The phrase to get frequency data for"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get phrase frequency data over time"""
    try:
        # Parse dates
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start_date = date.today() - timedelta(days=90)  # Default to 90 days ago to show more data
            
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end_date = date.today()
        
        # Get phrase frequency data
        phrase_data = db.query(TrendingPhrase).filter(
            TrendingPhrase.phrase == phrase,
            TrendingPhrase.date >= start_date,
            TrendingPhrase.date <= end_date
        ).order_by(TrendingPhrase.date.asc()).all()
        
        # Format data for chart
        chart_data = []
        for item in phrase_data:
            chart_data.append({
                'date': item.date.strftime('%Y-%m-%d'),
                'frequency': item.frequency,
                'score': round(item.score, 2),
                'phrase_type': item.phrase_type,
                'source': item.source
            })
        
        return {
            "phrase": phrase,
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "total_records": len(chart_data),
            "data": chart_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching phrase frequency data: {str(e)}")
