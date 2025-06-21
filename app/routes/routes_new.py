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
import traceback
import json
import time
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

@router.post("/generate_candidates", summary="Generate a list of candidates for trending words")
def generate_candidates(db: Session = Depends(get_db)):
    """Generate trending word candidates using real-time AI and NLP analysis, save top 15 to database"""
    from app.routes.helpers import generate_trending_word_candidates_realtime_with_save
    
    try:
        # Real-time analysis with database storage for top 15 LLM words
        ai_candidates = generate_trending_word_candidates_realtime_with_save(db, limit=15)
        
        return {
            "message": "Real-time trending word candidates generated and top 15 saved to database!",
            "ai_candidates": ai_candidates,
            "note": "Top 15 LLM trending words saved to database for trending analysis section."
        }
    except Exception as e:
        detail = f"Error generating candidates: {str(e)}\n{traceback.format_exc()}"
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
