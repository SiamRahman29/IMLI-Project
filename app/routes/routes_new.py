from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import date, datetime, timedelta
from typing import Optional, List
import json
import time
import io
import sys
import random
import traceback
import builtins
import os
import asyncio
import io
import sys
import random

from app.db.database import SessionLocal
from app.models.word import Word, TrendingPhrase
from app.routes.helpers import get_trending_words
from app.dto.dtos import TrendingWordsResponse, TrendingPhraseResponse, DailyTrendingResponse, TrendingPhrasesRequest
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
    """Get the word of the day for today"""
    today = date.today()
    word_entry = db.query(Word).filter(Word.date == today).first()
    
    if word_entry:
        return TrendingWordsResponse(
            date=str(word_entry.date),
            words=word_entry.word
        )
    else:
        # Instead of raising 404, return a default response
        return {
            "date": str(today),
            "words": None,
            "message": "Today's word is not yet set"
        }

@router.post("/generate_candidates", summary="Generate category-wise trending words from newspapers using LLM")
def generate_candidates(db: Session = Depends(get_db)):
    """Generate trending word candidates using filtered newspaper scraping and category-wise LLM analysis"""
    from app.services.filtered_newspaper_service import FilteredNewspaperScraper
    from app.services.category_llm_analyzer import (
        get_জাতীয়_trending_words, get_অর্থনীতি_trending_words, get_রাজনীতি_trending_words,
        get_লাইফস্টাইল_trending_words, get_বিনোদন_trending_words, get_খেলাধুলা_trending_words,
        get_ধর্ম_trending_words, get_চাকরি_trending_words, get_শিক্ষা_trending_words,
        get_স্বাস্থ্য_trending_words, get_মতামত_trending_words, get_বিজ্ঞান_trending_words,
        get_আন্তর্জাতিক_trending_words, get_প্রযুক্তি_trending_words
    )
    
    try:
        # Target categories as requested
        TARGET_CATEGORIES = [
            'জাতীয়', 'আন্তর্জাতিক', 'অর্থনীতি', 'রাজনীতি', 'লাইফস্টাইল', 'বিনোদন', 
            'খেলাধুলা', 'ধর্ম', 'চাকরি', 'শিক্ষা', 'স্বাস্থ্য', 'মতামত', 'বিজ্ঞান', 'প্রযুক্তি'
        ]
        
        print(f"🚀 Starting filtered newspaper scraping for {len(TARGET_CATEGORIES)} categories...")
        
        # Initialize filtered newspaper scraper
        scraper = FilteredNewspaperScraper(TARGET_CATEGORIES)
        
        # Scrape all newspapers with category filtering
        results = scraper.scrape_all_newspapers()
        
        print(f"📊 Scraped {results['scraping_info']['total_articles']} articles")
        print(f"📂 Category-wise breakdown:")
        for category in TARGET_CATEGORIES:
            count = scraper.statistics['category_counts'][category]
            print(f"   {category}: {count} articles")
        
        # Category-wise LLM trending word extraction
        category_functions = {
            'জাতীয়': get_জাতীয়_trending_words,
            'আন্তর্জাতিক': get_আন্তর্জাতিক_trending_words,
            'অর্থনীতি': get_অর্থনীতি_trending_words,
            'রাজনীতি': get_রাজনীতি_trending_words,
            'লাইফস্টাইল': get_লাইফস্টাইল_trending_words,
            'বিনোদন': get_বিনোদন_trending_words,
            'খেলাধুলা': get_খেলাধুলা_trending_words,
            'ধর্ম': get_ধর্ম_trending_words,
            'চাকরি': get_চাকরি_trending_words,
            'শিক্ষা': get_শিক্ষা_trending_words,
            'স্বাস্থ্য': get_স্বাস্থ্য_trending_words,
            'মতামত': get_মতামত_trending_words,
            'বিজ্ঞান': get_বিজ্ঞান_trending_words,
            'প্রযুক্তি': get_প্রযুক্তি_trending_words
        }
        
        # Extract trending words for each category
        all_trending_words = []
        category_wise_trending = {}
        for category in TARGET_CATEGORIES:
            articles = results['category_wise_articles'][category]
            if articles:
                print(f"🤖 Processing {category} category with {len(articles)} articles...")
                trending_words = category_functions[category](articles)
                category_wise_trending[category] = trending_words
                all_trending_words.extend(trending_words)
                print(f"✅ {category}: {len(trending_words)} trending words extracted")
            else:
                print(f"⚠️ {category}: No articles found")
                category_wise_trending[category] = []

        # --- Integrate Reddit LLM trending words for 'আন্তর্জাতিক' ---
        try:
            from app.services.reddit_data_scrapping import RedditDataScrapper
            reddit_scraper = RedditDataScrapper()
            reddit_results = reddit_scraper.run_comprehensive_analysis(posts_per_subreddit=20)
            reddit_emerging_words = reddit_results.get('emerging_words', [])
            reddit_trending_words = [item['emerging_word'] for item in reddit_emerging_words if item.get('emerging_word')]
            if reddit_trending_words:
                # Merge Reddit trending words with newspaper 'আন্তর্জাতিক' trending words
                category_wise_trending = scraper.combine_reddit_trending_with_international(
                    category_wise_trending, reddit_trending_words
                )
                # Also update all_trending_words for completeness
                all_trending_words.extend([w for w in reddit_trending_words if w not in all_trending_words])
        except Exception as e:
            print(f"⚠️ Could not integrate Reddit LLM trending words: {e}")

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
                    # Take up to 8 words per category (or 16 for আন্তর্জাতিক)
                    word_limit = 16 if category == 'আন্তর্জাতিক' else 8
                    limited_words = words[:word_limit]
                    total_input_words += len(limited_words)
                    
                    words_text = "\n".join([f"  {i}. {word}" for i, word in enumerate(limited_words, 1)])
                    section = f"{category} ({len(limited_words)}টি):\n{words_text}"
                    category_prompt_sections.append(section)
            
            if category_prompt_sections:
                categories_text = "\n\n".join(category_prompt_sections)
                
                from groq import Groq
                client = Groq(api_key=os.getenv('GROQ_API_KEY_NEWSPAPER'))
                
                final_selection_prompt = f"""
তুমি একজন বিশেষজ্ঞ বাংলা ভাষা বিশ্লেষক। নিচে বিভিন্ন ক্যাটেগরি থেকে সংগৃহীত ট্রেন্ডিং শব্দ/বাক্যাংশের তালিকা দেওয়া হল। প্রতিটি ক্যাটেগরি থেকে সবচেয়ে গুরুত্বপূর্ণ ও ট্রেন্ডিং ৫টি শব্দ/বাক্যাংশ নির্বাচন করো।

নির্বাচনের মানদণ্ড:
1. সর্বোচ্চ ট্রেন্ডিং ও আলোচিত বিষয়
2. বর্তমান সময়ের সবচেয়ে প্রাসঙ্গিক
3. ২-৪ শব্দের মধ্যে সংক্ষিপ্ত ও স্পষ্ট বাংলা শব্দ/বাক্যাংশ
4. এক ক্যাটেগরিতে একই টপিক বা অর্থের কাছাকাছি শব্দ থাকবে না, প্রতিটি শব্দ ইউনিক ও প্রসঙ্গভিত্তিক অর্থবহ হতে হবে
5. প্রতি ক্যাটেগরিতে ঠিক ৫টি করে

ক্যাটেগরি-ভিত্তিক ট্রেন্ডিং শব্দ:

{categories_text}

আউটপুট ফরম্যাট (প্রতি ক্যাটেগরিতে ৫টি করে):

[ক্যাটেগরির নাম]:
১. [শব্দ/বাক্যাংশ]
২. [শব্দ/বাক্যাংশ]
৩. [শব্দ/বাক্যাংশ]
৪. [শব্দ/বাক্যাংশ]
৫. [শব্দ/বাক্যাংশ]

**গুরুত্বপূর্ণ:** শুধুমাত্র উপরের ফরম্যাটে উত্তর দাও। অতিরিক্ত ব্যাখ্যা যোগ করো না।
"""
                
                print(f"🤖 Generating final category-wise selection from {len(category_prompt_sections)} categories using LLM...")
                
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
                
                # Parse category-wise response
                current_category = None
                lines = llm_response.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check if this is a category header (ends with colon)
                    if line.endswith(':') and not line.startswith(('1.', '2.', '3.', '4.', '5.', '১.', '২.', '৩.', '৪.', '৫.')):
                        current_category = line.replace(':', '').strip()
                        category_wise_final[current_category] = []
                        continue
                    
                    # Extract numbered items for current category
                    if current_category and (line.startswith(('1.', '2.', '3.', '4.', '5.', '১.', '২.', '৩.', '৪.', '৫.'))):
                        import re
                        word = re.sub(r'^[১২ৃ৪৫1-5][\.\)]\s*', '', line).strip()
                        if word and len(word) > 1:
                            category_wise_final[current_category].append(word)
                            final_trending_words.append(word)
                
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
            # Fallback: Use top words from each category
            for category, words in category_wise_trending.items():
                if words:
                    category_wise_final[category] = words[:5]  # Take top 5 from each
                    final_trending_words.extend(words[:5])
            
            llm_selection_stats = {
                "selection_method": "Fallback: Top 5 per category without LLM",
                "selected_words": len(final_trending_words),
                "categories_processed": len(category_wise_final)
            }

        print(f"🎉 Total trending words extracted: {len(all_trending_words)}")
        print(f"🎯 Final selected words: {len(final_trending_words)}")
        
        return {
            "message": "Category-wise trending words generated successfully using filtered newspaper scraping and LLM analysis!",
            "scraping_info": results['scraping_info'],
            "category_wise_trending_words": category_wise_trending,
            "all_trending_words": all_trending_words,
            "category_wise_final": category_wise_final,
            "final_trending_words": final_trending_words,
            "llm_selection": llm_selection_stats,
            "statistics": {
                "total_articles_scraped": results['scraping_info']['total_articles'],
                "categories_processed": len([c for c in TARGET_CATEGORIES if category_wise_trending[c]]),
                "total_trending_words": len(all_trending_words),
                "final_selected_words": len(final_trending_words),
                "scraping_time_seconds": results['scraping_info']['scraping_time_seconds']
            }
        }
        
    except Exception as e:
        detail = f"Error generating category-wise candidates: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=detail)

@router.get("/trending-phrases", summary="Get trending phrases for a specific date range")
def get_trending_phrases(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    limit: int = Query(50, description="Maximum number of phrases to return"),
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
    
    # Order by score descending and limit
    phrases = query.order_by(desc(TrendingPhrase.score)).limit(limit).all()
    
    # Convert to response format
    trending_phrases = []
    for phrase in phrases:
        trending_phrases.append(TrendingPhraseResponse(
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
        "total_count": len(trending_phrases),
        "phrases": trending_phrases
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
            
            # Step 3: Store articles in database  
            yield f"data: {json.dumps({'step': 3, 'message': 'সংগৃহীত কন্টেন্ট ডেটাবেসে সংরক্ষণ করা হচ্ছে...', 'progress': 25, 'details': {'storing': 'articles', 'articles_collected': len(news_articles)}})}\n\n"
            print("=== Storing articles in database ===")
            
            from app.routes.helpers import store_news
            store_news(db, news_articles)
            
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
    """Get trending phrases summary for a specific week"""
    
    if not target_week:
        # Current week start (Monday)
        today = date.today()
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
    else:
        try:
            week_start = datetime.strptime(target_week, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    week_end = week_start + timedelta(days=6)
    
    # Get phrases for the target week
    phrases = db.query(TrendingPhrase).filter(
        and_(
            TrendingPhrase.date >= week_start,
            TrendingPhrase.date <= week_end
        )
    ).order_by(desc(TrendingPhrase.score)).all()
    
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

# ==========================================
# CATEGORY-BASED TRENDING ANALYSIS ENDPOINTS
# ==========================================

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

# ==========================================
# END OF CATEGORY-BASED ANALYSIS ENDPOINTS
# ==========================================

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
            """Process newspaper data with dedicated API key"""
            print("📰 Processing newspaper data...")
            
            # Temporarily set newspaper API key
            original_key = os.environ.get("GROQ_API_KEY")
            newspaper_key = os.environ.get("GROQ_API_KEY_NEWSPAPER")
            if newspaper_key:
                os.environ["GROQ_API_KEY"] = newspaper_key
            
            # Use category-wise newspaper analysis as per user requirements
            from app.services.filtered_newspaper_service import FilteredNewspaperScraper
            from app.services.category_llm_analyzer import (
                get_জাতীয়_trending_words, get_অর্থনীতি_trending_words, get_রাজনীতি_trending_words,
                get_লাইফস্টাইল_trending_words, get_বিনোদন_trending_words, get_খেলাধুলা_trending_words,
                get_ধর্ম_trending_words, get_চাকরি_trending_words, get_শিক্ষা_trending_words,
                get_স্বাস্থ্য_trending_words, get_মতামত_trending_words, get_বিজ্ঞান_trending_words,
                get_আন্তর্জাতিক_trending_words, get_প্রযুক্তি_trending_words
            )
            
            # Target categories
            TARGET_CATEGORIES = [
                'জাতীয়', 'আন্তর্জাতিক', 'অর্থনীতি', 'রাজনীতি', 'লাইফস্টাইল', 'বিনোদন', 
                'খেলাধুলা', 'ধর্ম', 'চাকরি', 'শিক্ষা', 'স্বাস্থ্য', 'মতামত', 'বিজ্ঞান', 'প্রযুক্তি'
            ]
            
            print(f"🚀 Starting filtered newspaper scraping for {len(TARGET_CATEGORIES)} categories...")
            
            # Initialize filtered newspaper scraper
            scraper = FilteredNewspaperScraper(TARGET_CATEGORIES)
            
            # Scrape all newspapers with category filtering
            results = scraper.scrape_all_newspapers()
            
            print(f"📊 Scraped {results['scraping_info']['total_articles']} articles")
            
            # Category-wise LLM trending word extraction
            category_functions = {
                'জাতীয়': get_জাতীয়_trending_words,
                'আন্তর্জাতিক': get_আন্তর্জাতিক_trending_words,
                'অর্থনীতি': get_অর্থনীতি_trending_words,
                'রাজনীতি': get_রাজনীতি_trending_words,
                'লাইফস্টাইল': get_লাইফস্টাইল_trending_words,
                'বিনোদন': get_বিনোদন_trending_words,
                'খেলাধুলা': get_খেলাধুলা_trending_words,
                'ধর্ম': get_ধর্ম_trending_words,
                'চাকরি': get_চাকরি_trending_words,
                'শিক্ষা': get_শিক্ষা_trending_words,
                'স্বাস্থ্য': get_স্বাস্থ্য_trending_words,
                'মতামত': get_মতামত_trending_words,
                'বিজ্ঞান': get_বিজ্ঞান_trending_words,
                'প্রযুক্তি': get_প্রযুক্তি_trending_words
            }
            
            # Extract trending words for each category
            all_trending_words = []
            category_wise_trending = {}
            for category in TARGET_CATEGORIES:
                articles = results['category_wise_articles'][category]
                if articles:
                    print(f"🤖 Processing {category} category with {len(articles)} articles...")
                    trending_words = category_functions[category](articles)
                    category_wise_trending[category] = trending_words
                    all_trending_words.extend(trending_words)
                    print(f"✅ {category}: {len(trending_words)} trending words extracted")
                else:
                    print(f"⚠️ {category}: No articles found")
                    category_wise_trending[category] = []

            # --- Integrate Reddit LLM trending words for 'আন্তর্জাতিক' ---
            try:
                from app.services.reddit_data_scrapping import RedditDataScrapper
                reddit_scraper = RedditDataScrapper()
                reddit_results = reddit_scraper.run_comprehensive_analysis(posts_per_subreddit=20)
                reddit_emerging_words = reddit_results.get('emerging_words', [])
                reddit_trending_words = [item['emerging_word'] for item in reddit_emerging_words if item.get('emerging_word')]
                if reddit_trending_words:
                    print(f"📱 Found {len(reddit_trending_words)} Reddit trending words")
                    # Combine Reddit trending words with newspaper 'আন্তর্জাতিক' trending words (8 + 8 = 16)
                    international_newspaper_words = category_wise_trending.get('আন্তর্জাতিক', [])[:8]  # Take only 8 from newspaper
                    reddit_words_limited = reddit_trending_words[:8]  # Take only 8 from Reddit
                    
                    # Combine for আন্তর্জাতিক category
                    category_wise_trending['আন্তর্জাতিক'] = international_newspaper_words + reddit_words_limited
                    print(f"🔗 Combined আন্তর্জাতিক: {len(international_newspaper_words)} newspaper + {len(reddit_words_limited)} Reddit = {len(category_wise_trending['আন্তর্জাতিক'])} total")
                    
                    # Also update all_trending_words for completeness
                    all_trending_words.extend([w for w in reddit_words_limited if w not in all_trending_words])
            except Exception as e:
                print(f"⚠️ Could not integrate Reddit LLM trending words: {e}")

            # Limit each category to exactly 8 words (except আন্তর্জাতিক which can have 16)
            for category in category_wise_trending:
                if category != 'আন্তর্জাতিক':
                    category_wise_trending[category] = category_wise_trending[category][:8]

            print(f"🎉 Total trending words extracted: {len(all_trending_words)}")
            return {
                "message": "Category-wise trending words generated successfully using filtered newspaper scraping and LLM analysis!",
                "scraping_info": results['scraping_info'],
                "category_wise_trending_words": category_wise_trending,
                "all_trending_words": all_trending_words,
                "statistics": {
                    "total_articles_scraped": results['scraping_info']['total_articles'],
                    "categories_processed": len([c for c in TARGET_CATEGORIES if category_wise_trending[c]]),
                    "total_trending_words": len(all_trending_words),
                    "scraping_time_seconds": results['scraping_info']['scraping_time_seconds']
                }
            }
        
        async def process_reddit_data():
            """Process Reddit data with dedicated API key"""
            try:
                print("📱 Processing Reddit data...")
                
                # Temporarily set Reddit API key
                original_key = os.environ.get("GROQ_API_KEY")
                reddit_key = os.environ.get("GROQ_API_KEY_REDDIT")
                if reddit_key:
                    os.environ["GROQ_API_KEY"] = reddit_key
                
                # Initialize Reddit data scrapper
                from app.services.reddit_data_scrapping import RedditDataScrapper
                reddit_scraper = RedditDataScrapper()
                
                # Run comprehensive analysis on Reddit data
                reddit_results = reddit_scraper.run_comprehensive_analysis(posts_per_subreddit=20)
                
                return reddit_results.get('emerging_words', [])
            
            except Exception as e:
                results["errors"]["reddit"] = str(e)
                return []
        
        # Main processing logic
        if mode == "sequential":
            print("🔄 Starting sequential processing: Newspapers first, then Reddit...")
            
            # Sequential processing: Newspapers first, then Reddit
            newspaper_results = await process_newspaper_data()
            results["results"]["newspaper"] = newspaper_results
            
            # Add newspaper trending words to final list
            if newspaper_results and "all_trending_words" in newspaper_results:
                newspaper_words = newspaper_results["all_trending_words"]
                results["final_trending_words"].extend(newspaper_words)
                print(f"📰 Added {len(newspaper_words)} newspaper trending words to final list")
                print(f"📰 Sample newspaper words: {', '.join(newspaper_words[:5])}..." if newspaper_words else "❌ No newspaper words")
            
            # Now process Reddit data
            print("📱 Starting Reddit data processing...")
            reddit_emerging_words = await process_reddit_data()
            
            # Merge results if Reddit data is available
            if reddit_emerging_words:
                results["results"]["reddit"] = reddit_emerging_words
                reddit_words = []
                # Combine Reddit trending words with existing newspaper trends
                for item in reddit_emerging_words:
                    word = item.get('emerging_word')
                    if word and word not in results["final_trending_words"]:
                        results["final_trending_words"].append(word)
                        reddit_words.append(word)
                
                print(f"📱 Added {len(reddit_words)} unique Reddit trending words to final list")
                print(f"📱 Sample Reddit words: {', '.join(reddit_words[:3])}..." if reddit_words else "❌ No Reddit words")
            else:
                print("⚠️ No Reddit data obtained")
        
        else:
            print("🔄 Starting parallel processing: Newspapers and Reddit simultaneously...")
            
            # Parallel processing: Newspapers and Reddit at the same time
            newspaper_task = asyncio.create_task(process_newspaper_data())
            reddit_task = asyncio.create_task(process_reddit_data())
            
            # Wait for both tasks to complete
            newspaper_results, reddit_emerging_words = await asyncio.gather(newspaper_task, reddit_task)
            
            # Store newspaper results
            results["results"]["newspaper"] = newspaper_results
            if newspaper_results and "all_trending_words" in newspaper_results:
                newspaper_words = newspaper_results["all_trending_words"]
                results["final_trending_words"].extend(newspaper_words)
                print(f"📰 Added {len(newspaper_words)} newspaper trending words to final list")
                print(f"📰 Sample newspaper words: {', '.join(newspaper_words[:5])}..." if newspaper_words else "❌ No newspaper words")
            
            # Merge Reddit results into final trending words
            if reddit_emerging_words:
                results["results"]["reddit"] = reddit_emerging_words
                reddit_words = []
                for item in reddit_emerging_words:
                    word = item.get('emerging_word')
                    if word and word not in results["final_trending_words"]:
                        results["final_trending_words"].append(word)
                        reddit_words.append(word)
                
                print(f"📱 Added {len(reddit_words)} unique Reddit trending words to final list")
                print(f"📱 Sample Reddit words: {', '.join(reddit_words[:3])}..." if reddit_words else "❌ No Reddit words")
            else:
                print("⚠️ No Reddit data obtained")
        
        print(f"🔗 Total combined trending words before LLM selection: {len(results['final_trending_words'])}")
        print(f"🔗 Combined sample: {', '.join(results['final_trending_words'][:8])}..." if results['final_trending_words'] else "❌ No combined words")
        
        # Final response construction
        results["message"] = "Trending words generated from selected sources"
        results["total_sources"] = len(sources)
        
        # Prepare detailed source information for better LLM analysis
        source_breakdown = {}
        category_wise_breakdown = {}
        
        if results["results"].get("newspaper"):
            newspaper_results = results["results"]["newspaper"]
            newspaper_words = newspaper_results.get("all_trending_words", [])
            category_wise_words = newspaper_results.get("category_wise_trending_words", {})
            
            source_breakdown["newspaper"] = {
                "count": len(newspaper_words),
                "words": newspaper_words,
                "categories": category_wise_words
            }
            
            # Build category-wise breakdown for LLM prompt
            for category, words in category_wise_words.items():
                if words:
                    category_wise_breakdown[category] = words
        
        if results["results"].get("reddit"):
            reddit_words = [item.get('emerging_word') for item in results["results"]["reddit"] if item.get('emerging_word')]
            source_breakdown["reddit"] = {
                "count": len(reddit_words),
                "words": reddit_words
            }
        
        # Use LLM to get final category-wise selection (5 words per category)
        if category_wise_breakdown:
            try:
                print(f"🤖 Generating category-wise final selection from {len(category_wise_breakdown)} categories using LLM...")
                
                # Create category-wise prompt format
                category_prompt_sections = []
                for category, words in category_wise_breakdown.items():
                    if words:
                        words_text = "\n".join([f"  {i}. {word}" for i, word in enumerate(words, 1)])
                        section = f"{category}:\n{words_text}"
                        category_prompt_sections.append(section)
                
                categories_text = "\n\n".join(category_prompt_sections)
                
                from groq import Groq
                client = Groq()

                final_selection_prompt = f"""আপনাকে নিম্নলিখিত ক্যাটেগরি অনুযায়ী ট্রেন্ডিং শব্দগুলো থেকে প্রতিটি ক্যাটেগরি থেকে সবচেয়ে গুরুত্বপূর্ণ ৫টি করে শব্দ বেছে নিতে হবে। এমন শব্দ/বাক্যাংশ দাও যেটা শুনলে মানুষ বুঝতে পারবে যে এটা কীসের সাথে সম্পর্কিত। যার একটা অর্থ থাকবে, এমন কিছু দেবে না যেটা অর্থহীন এবং যেটা দেখলে কনটেক্সট বোঝা যাবে না।
ক্যাটেগরি অনুযায়ী ট্রেন্ডিং শব্দ:
{categories_text}
নির্বাচনের নিয়মাবলী:
1. প্রতিটি ক্যাটেগরি থেকে সবচেয়ে প্রাসঙ্গিক ৫টি শব্দ নির্বাচন করুন
2. প্রতিটি শব্দ/বাক্যাংশ ২-৪ শব্দের মধ্যে এবং স্পষ্ট অর্থবোধক হতে হবে
3. এক ক্যাটেগরিতে একই টপিক বা অর্থের কাছাকাছি শব্দ থাকবে না, প্রতিটি শব্দ ইউনিক ও প্রসঙ্গভিত্তিক অর্থবহ হতে হবে
4. response শুধুমাত্র bangla language a deo
5. ব্যক্তিগত নাম এড়িয়ে চলুন, বিষয়বস্তুর উপর ফোকাস করুন
6. সাম্প্রতিক ও জনপ্রিয় বিষয়গুলো অগ্রাধিকার দিন
7. শব্দগুলোর মধ্যে সম্পর্ক ও প্রাসঙ্গিকতা বিবেচনা করুন

আউটপুট ফরম্যাট:
প্রতিটি ক্যাটেগরির জন্য নিম্নরূপ ফরম্যাটে দিন:

ক্যাটেগরি নাম:
1. শব্দ১
2. শব্দ২
3. শব্দ৩
4. শব্দ৪
5. শব্দ৫

অন্য ক্যাটেগরি নাম:
1. শব্দ১
2. শব্দ২
...
...
5. শব্দ৫

শুধুমাত্র উপরের ফরম্যাটে উত্তর দিন। অতিরিক্ত ব্যাখ্যা বা মন্তব্য যোগ করবেন না।"""
                
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "আপনি একজন বিশেষজ্ঞ বাংলা ভাষা বিশ্লেষক যিনি ক্যাটেগরি অনুযায়ী ট্রেন্ডিং বিষয় নির্বাচন করতে পারেন।"},
                        {"role": "user", "content": final_selection_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=800
                )
                
                llm_response = completion.choices[0].message.content.strip()
                
                # Parse category-wise response
                category_wise_final = {}
                all_final_words = []
                
                current_category = None
                lines = llm_response.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check if this is a category header (ends with colon)
                    if line.endswith(':') and not line.startswith(('1.', '2.', '3.', '4.', '5.', '১.', '২.', '৩.', '৪.', '৫.')):
                        current_category = line.replace(':', '').strip()
                        category_wise_final[current_category] = []
                    
                    # Check if this is a numbered item
                    elif current_category and (line.startswith(('1.', '2.', '3.', '4.', '5.')) or line.startswith(('১.', '২.', '৩.', '৪.', '৫.'))):
                        # Extract word after number
                        import re
                        word = re.sub(r'^[১২৩৪৫1-5][\.\)]\s*', '', line).strip()
                        if word and len(word) > 1:
                            category_wise_final[current_category].append(word)
                            all_final_words.append(word)
                
                # Store results
                results["llm_response"] = llm_response
                results["final_trending_words"] = all_final_words
                results["category_wise_final"] = category_wise_final
                results["llm_selection"] = {
                    "total_input_categories": len(category_wise_breakdown),
                    "total_input_words": sum(len(words) for words in category_wise_breakdown.values()),
                    "selected_words": len(all_final_words),
                    "categories_processed": len(category_wise_final),
                    "selection_method": "Enhanced category-wise LLM selection",
                    "source_breakdown": source_breakdown
                }
                
                print(f"✅ LLM selected {len(all_final_words)} words across {len(category_wise_final)} categories")
                
                # Print category breakdown
                for category, words in category_wise_final.items():
                    print(f"📊 {category}: {len(words)} words - {', '.join(words[:3])}..." if words else f"📊 {category}: No words")
                
            except Exception as e:
                print(f"⚠️ Could not use LLM for category-wise selection, using combined approach: {e}")
                # Fallback to previous method but organized by category
                if results["final_trending_words"]:
                    combined_words = list(set(results["final_trending_words"]))[:70]  # Take reasonable amount
                    results["final_trending_words"] = combined_words[:70]
                    
                    # Organize by category as fallback
                    category_wise_final = {}
                    words_per_category = 5
                    word_index = 0
                    
                    for category in category_wise_breakdown.keys():
                        category_words = []
                        for _ in range(words_per_category):
                            if word_index < len(combined_words):
                                category_words.append(combined_words[word_index])
                                word_index += 1
                        category_wise_final[category] = category_words
                    
                    results["category_wise_final"] = category_wise_final
                    results["llm_selection"] = {
                        "total_input_words": len(combined_words),
                        "selected_words": len(results["final_trending_words"]),
                        "selection_method": "Fallback: Category distribution (LLM failed)"
                    }
        else:
            results["final_trending_words"] = []
            results["category_wise_final"] = {}
            print("⚠️ No category-wise words found from any source")
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in hybrid candidate generation: {str(e)}")
