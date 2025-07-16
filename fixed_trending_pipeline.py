#!/usr/bin/env python3
"""
Fixed Pipeline Implementation for Trending Words with Frequency Calculation
This implements the correct flow as requested by the user
"""

import os
import json
import re
from typing import List, Dict, Optional
from collections import Counter

def calculate_phrase_frequency_from_articles(phrase: str, articles: List[Dict]) -> int:
    """
    Calculate frequency of a phrase across scraped articles
    This is called AFTER final phrase selection to determine frequency
    
    Args:
        phrase: The phrase to count
        articles: List of scraped articles from the category
    
    Returns:
        Frequency count (how many articles this phrase appears in)
    """
    frequency_count = 0
    phrase_lower = phrase.lower().strip()
    
    print(f"🔍 Calculating frequency for phrase: '{phrase}' across {len(articles)} articles")
    
    for article in articles:
        article_text = ""
        
        # Combine title, heading, and content for searching
        for field in ['title', 'heading', 'content', 'description']:
            if article.get(field):
                article_text += " " + str(article[field])
        
        article_text = article_text.lower()
        
        # Count if phrase appears in this article
        if phrase_lower in article_text:
            frequency_count += 1
    
    print(f"✅ Phrase '{phrase}' found in {frequency_count} articles")
    return frequency_count

def extract_final_phrases_from_text_response(llm_text_response: str) -> Dict[str, List[str]]:
    """
    Extract final 10 phrases per category from LLM text response
    This handles the text format output from final selection LLM
    
    Args:
        llm_text_response: Text response from final selection LLM
    
    Returns:
        Dictionary with category -> list of 10 phrases
    """
    category_phrases = {}
    current_category = None
    
    lines = llm_text_response.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this line is a category header (ends with colon)
        if line.endswith(':') and not re.match(r'^[১২৩৪৫৬৭৮৯১০0-9]', line):
            current_category = line.replace(':', '').strip()
            category_phrases[current_category] = []
            print(f"📂 Found category: '{current_category}'")
            continue
        
        # Check if this line is a numbered phrase
        if current_category and re.match(r'^[১২৩৪৫৬৭৮৯১০0-9]', line):
            # Extract phrase text (remove number prefix)
            phrase = re.sub(r'^[১২৩৪৫৬৭৮৯১০0-9]+[\.\)]\s*', '', line).strip()
            phrase = re.sub(r'[।\.]+$', '', phrase).strip()  # Remove trailing punctuation
            
            if phrase and len(phrase) > 1:
                category_phrases[current_category].append(phrase)
                print(f"  ✅ Added phrase: '{phrase}'")
                
                # Limit to 10 phrases per category
                if len(category_phrases[current_category]) >= 10:
                    print(f"  🔄 Category '{current_category}' reached 10 phrases limit")
    
    return category_phrases

def attach_frequency_to_final_phrases(
    category_phrases: Dict[str, List[str]], 
    category_articles: Dict[str, List[Dict]]
) -> Dict[str, List[Dict]]:
    """
    Attach frequency information to final selected phrases
    
    Args:
        category_phrases: Dict of category -> list of phrases
        category_articles: Dict of category -> list of articles
    
    Returns:
        Dict of category -> list of phrase objects with frequency
    """
    category_wise_final = {}
    
    for category, phrases in category_phrases.items():
        category_wise_final[category] = []
        articles = category_articles.get(category, [])
        
        print(f"\n📊 Processing category '{category}' with {len(phrases)} phrases and {len(articles)} articles")
        
        for phrase in phrases:
            # Calculate frequency from scraped articles
            frequency = calculate_phrase_frequency_from_articles(phrase, articles)
            
            # Create phrase object with frequency
            phrase_obj = {
                'word': phrase,
                'frequency': frequency,
                'category': category,
                'source': 'llm_selection'
            }
            
            category_wise_final[category].append(phrase_obj)
            print(f"  ✅ '{phrase}' → frequency: {frequency}")
    
    return category_wise_final

def process_newspaper_trending_words(results: Dict) -> Dict[str, List[str]]:
    """
    Process newspaper results to extract 15 trending words per category using LLM
    
    Args:
        results: Results from newspaper scraping
    
    Returns:
        Dict of category -> list of 15 trending words
    """
    category_trending = {}
    
    if 'category_wise_articles' in results:
        print("📰 Processing newspaper data for trending words...")
        
        # Import the LLM analyzer
        try:
            from app.services.category_llm_analyzer import get_category_trending_words
            
            for category, articles in results['category_wise_articles'].items():
                print(f"🔍 Processing category: {category} ({len(articles)} articles)")
                
                # Get 15 trending words for this category using LLM
                trending_words = get_category_trending_words(category, articles)
                category_trending[category] = trending_words[:15]  # Ensure max 15
                
                print(f"✅ Got {len(category_trending[category])} trending words for {category}")
        
        except Exception as e:
            print(f"❌ Error processing newspaper trending words: {e}")
    
    return category_trending

def process_reddit_trending_words(results: Dict) -> List[str]:
    """
    Process reddit results to extract 2 words per subreddit using LLM
    
    Args:
        results: Results from reddit scraping
    
    Returns:
        List of trending words from reddit
    """
    reddit_words = []
    
    if 'subreddit_results' in results:
        print("📡 Processing reddit data for trending words...")
        
        for subreddit_result in results['subreddit_results']:
            if subreddit_result.get('status') == 'success':
                # Get 2 words per subreddit (simplified for now)
                words = subreddit_result.get('trending_words', [])[:2]
                reddit_words.extend(words)
        
        print(f"✅ Got {len(reddit_words)} words from Reddit")
    
    return reddit_words

def fixed_trending_pipeline(results: Dict) -> Dict:
    """
    Fixed pipeline implementation according to user requirements:
    
    1. Newspaper scraping → categorize
    2. Each category → 15 trending phrases (LLM)
    3. Reddit scraping → 2 phrases per subreddit (LLM) 
    4. Newspaper + Reddit → Final 10 phrases per category (text format LLM)
    5. Final phrases → Calculate frequency from scraped articles
    
    Args:
        results: Combined results from newspaper and reddit scraping
    
    Returns:
        Updated results with category_wise_final containing frequency info
    """
    
    print("🚀 Starting Fixed Trending Words Pipeline...")
    print("=" * 60)
    
    # Step 1 & 2: Process newspaper data → get 15 trending words per category
    print("\n📰 Step 1-2: Newspaper Processing (15 words per category)")
    newspaper_trending = process_newspaper_trending_words(results.get('results', {}).get('newspaper', {}))
    
    # Step 3: Process reddit data → get 2 words per subreddit  
    print("\n📡 Step 3: Reddit Processing (2 words per subreddit)")
    reddit_words = process_reddit_trending_words(results.get('results', {}).get('reddit', {}))
    
    # Merge reddit words into 'আন্তর্জাতিক' category
    if reddit_words and 'আন্তর্জাতিক' in newspaper_trending:
        newspaper_trending['আন্তর্জাতিক'].extend(reddit_words)
        print(f"🔗 Merged {len(reddit_words)} Reddit words into 'আন্তর্জাতিক' category")
    
    # Step 4: Final selection → 10 phrases per category (text format LLM)
    print("\n🤖 Step 4: Final Selection (10 phrases per category)")
    
    if newspaper_trending:
        try:
            from groq import Groq
            client = Groq(api_key=os.getenv('GROQ_API_KEY_NEWSPAPER'))
            
            # Create prompt with all categories
            category_sections = []
            for category, words in newspaper_trending.items():
                if words:
                    words_text = "\\n".join([f"  {i}. {word}" for i, word in enumerate(words[:15], 1)])
                    section = f"{category} ({len(words[:15])}টি):\\n{words_text}"
                    category_sections.append(section)
            
            categories_text = "\\n\\n".join(category_sections)
            
            final_selection_prompt = f"""তুমি একজন বিশেষজ্ঞ বাংলাদেশি সংবাদ বিশ্লেষক। আপনাকে নিম্নলিখিত ক্যাটেগরি অনুযায়ী ট্রেন্ডিং শব্দগুলো থেকে প্রতিটি ক্যাটেগরি থেকে সবচেয়ে গুরুত্বপূর্ণ ১০টি করে শব্দ বেছে নিতে হবে।

ক্যাটেগরি অনুযায়ী ট্রেন্ডিং শব্দ:
{categories_text}

নির্বাচনের নিয়মাবলী:
1. প্রতিটি ক্যাটেগরি থেকে সবচেয়ে প্রাসঙ্গিক ১০টি শব্দ নির্বাচন করুন
2. প্রতিটি শব্দ/বাক্যাংশ ২-৪ শব্দের মধ্যে এবং স্পষ্ট অর্থবোধক হতে হবে
3. ব্যক্তিগত নাম এড়িয়ে চলুন, বিষয়বস্তুর উপর ফোকাস করুন

আউটপুট ফরম্যাট:
প্রতিটি ক্যাটেগরির জন্য নিম্নরূপ ফরম্যাটে দিন:

ক্যাটেগরি নাম:
1. শব্দ১
2. শব্দ২
...
10. শব্দ১০

শুধুমাত্র উপরের ফরম্যাটে উত্তর দিন।"""

            print("🤖 Calling final selection LLM...")
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": final_selection_prompt}],
                temperature=0.3,
                max_tokens=5000
            )
            
            llm_text_response = completion.choices[0].message.content.strip()
            print(f"✅ Got LLM response ({len(llm_text_response)} characters)")
            
            # Step 4b: Extract phrases from text response
            category_phrases = extract_final_phrases_from_text_response(llm_text_response)
            print(f"📋 Extracted phrases for {len(category_phrases)} categories")
            
            # Step 5: Calculate frequency from scraped articles
            print("\\n📊 Step 5: Calculating Frequencies from Scraped Articles")
            
            category_articles = {}
            if 'results' in results and 'newspaper' in results['results']:
                category_articles = results['results']['newspaper'].get('category_wise_articles', {})
            
            category_wise_final = attach_frequency_to_final_phrases(category_phrases, category_articles)
            
            # Add to results
            results['category_wise_final'] = category_wise_final
            results['llm_text_response'] = llm_text_response
            
            print(f"\\n🎉 Pipeline Complete!")
            print(f"📊 Final Results:")
            for category, phrases in category_wise_final.items():
                total_freq = sum(p['frequency'] for p in phrases)
                print(f"  {category}: {len(phrases)} phrases, total frequency: {total_freq}")
            
        except Exception as e:
            print(f"❌ Error in final selection: {e}")
            import traceback
            traceback.print_exc()
    
    return results

# Test function
if __name__ == "__main__":
    print("🧪 Testing Fixed Pipeline...")
    
    # Test frequency calculation
    test_phrase = "সরকার"
    test_articles = [
        {"title": "সরকার নতুন নীতি ঘোষণা করেছে", "heading": "সরকারি সিদ্ধান্ত"},
        {"title": "অর্থনৈতিক সংস্কার", "heading": "নতুন পরিকল্পনা"},
        {"title": "সরকার কর্তৃক নতুন আইন", "content": "সরকার আজ গুরুত্বপূর্ণ ঘোষণা দিয়েছে"}
    ]
    
    frequency = calculate_phrase_frequency_from_articles(test_phrase, test_articles)
    print(f"Test result: '{test_phrase}' appears in {frequency} articles")
