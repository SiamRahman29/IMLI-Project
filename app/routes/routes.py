from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import date, datetime, timedelta
from typing import Optional, List

from app.db.database import SessionLocal
from app.models.word import Word, TrendingPhrase
from app.routes.helpers import get_trending_words, generate_trending_word_candidates_realtime_with_save
from app.dto.dtos import TrendingWordsResponse, TrendingPhraseResponse, DailyTrendingResponse, TrendingPhrasesRequest

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
        raise HTTPException(status_code=404, detail="Today's word is not yet set")

@router.post("/generate_candidates", summary="Generate a list of candidates for trending words")
def generate_candidates(db: Session = Depends(get_db)):
    """Generate trending word candidates using AI and NLP analysis"""
    try:
        # Run full trending analysis
        get_trending_words(db)
        
        # Also generate AI candidates with database save
        ai_candidates = generate_trending_word_candidates_realtime_with_save(db, limit=15)
        
        return {
            "message": "Trending analysis completed!",
            "ai_candidates": ai_candidates,
            "note": "Check /trending-phrases endpoint for detailed analysis"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating candidates: {str(e)}")

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

@router.get("/trending-phrases", summary="Get trending phrases with filtering options")
def get_trending_phrases(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    phrase_type: Optional[str] = Query(None, description="unigram, bigram, or trigram"),
    source: Optional[str] = Query(None, description="news or social_media"),
    limit: int = Query(10, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """Get trending phrases with optional filtering"""
    
    # Build query
    query = db.query(TrendingPhrase)
    
    # Apply filters
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(TrendingPhrase.date >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(TrendingPhrase.date <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
    
    if phrase_type:
        if phrase_type not in ['unigram', 'bigram', 'trigram']:
            raise HTTPException(status_code=400, detail="phrase_type must be unigram, bigram, or trigram")
        query = query.filter(TrendingPhrase.phrase_type == phrase_type)
    
    if source:
        if source not in ['news', 'social_media']:
            raise HTTPException(status_code=400, detail="source must be news or social_media")
        query = query.filter(TrendingPhrase.source == source)
    
    # Order by score and limit
    trending_phrases = query.order_by(desc(TrendingPhrase.score)).limit(limit).all()
    
    if not trending_phrases:
        raise HTTPException(status_code=404, detail="No trending phrases found")
    
    # Convert to response format
    phrase_responses = []
    for phrase in trending_phrases:
        phrase_responses.append(TrendingPhraseResponse(
            phrase=phrase.phrase,
            score=phrase.score,
            frequency=phrase.frequency,
            phrase_type=phrase.phrase_type,
            source=phrase.source
        ))
    
    return {
        "trending_phrases": phrase_responses,
        "total_count": len(phrase_responses),
        "filters_applied": {
            "start_date": start_date,
            "end_date": end_date,
            "phrase_type": phrase_type,
            "source": source,
            "limit": limit
        }
    }

@router.get("/daily-trending/{target_date}", summary="Get trending phrases for a specific date")
def get_daily_trending(target_date: str, db: Session = Depends(get_db)):
    """Get all trending phrases for a specific date"""
    try:
        target_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get trending phrases for the date
    trending_phrases = db.query(TrendingPhrase).filter(
        TrendingPhrase.date == target_dt
    ).order_by(desc(TrendingPhrase.score)).all()
    
    if not trending_phrases:
        raise HTTPException(status_code=404, detail=f"No trending phrases found for {target_date}")
    
    # Group by phrase type
    phrases_by_type = {
        'unigrams': [],
        'bigrams': [],
        'trigrams': []
    }
    
    for phrase in trending_phrases:
        phrase_response = TrendingPhraseResponse(
            phrase=phrase.phrase,
            score=phrase.score,
            frequency=phrase.frequency,
            phrase_type=phrase.phrase_type,
            source=phrase.source
        )
        
        if phrase.phrase_type == 'unigram':
            phrases_by_type['unigrams'].append(phrase_response)
        elif phrase.phrase_type == 'bigram':
            phrases_by_type['bigrams'].append(phrase_response)
        elif phrase.phrase_type == 'trigram':
            phrases_by_type['trigrams'].append(phrase_response)
    
    return DailyTrendingResponse(
        date=target_date,
        trending_phrases=trending_phrases
    )

@router.get("/top-phrases", summary="Get top trending phrases across all time")
def get_top_phrases(
    days: int = Query(7, description="Number of recent days to consider"),
    phrase_type: Optional[str] = Query(None, description="unigram, bigram, or trigram"),
    limit: int = Query(20, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """Get top trending phrases from recent days"""
    
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # Build query
    query = db.query(TrendingPhrase).filter(
        and_(
            TrendingPhrase.date >= start_date,
            TrendingPhrase.date <= end_date
        )
    )
    
    if phrase_type:
        if phrase_type not in ['unigram', 'bigram', 'trigram']:
            raise HTTPException(status_code=400, detail="phrase_type must be unigram, bigram, or trigram")
        query = query.filter(TrendingPhrase.phrase_type == phrase_type)
    
    # Get top phrases
    top_phrases = query.order_by(desc(TrendingPhrase.score)).limit(limit).all()
    
    if not top_phrases:
        raise HTTPException(status_code=404, detail="No trending phrases found")
    
    # Convert to response format
    phrase_responses = []
    for phrase in top_phrases:
        phrase_responses.append(TrendingPhraseResponse(
            phrase=phrase.phrase,
            score=phrase.score,
            frequency=phrase.frequency,
            phrase_type=phrase.phrase_type,
            source=phrase.source
        ))
    
    return {
        "top_phrases": phrase_responses,
        "period": f"Last {days} days",
        "date_range": f"{start_date} to {end_date}",
        "total_count": len(phrase_responses)
    }

# Category-based trending analysis endpoints
@router.get("/categories/trending", summary="Get trending phrases by category")
def get_category_trending_phrases(
    category: str = Query(..., description="Category name in Bengali (e.g., রাজনীতি, খেলাধুলা)"),
    days: int = Query(7, description="Number of days to analyze"),
    limit: int = Query(20, description="Maximum number of phrases to return"),
    db: Session = Depends(get_db)
):
    """Get trending phrases for a specific category"""
    try:
        from app.services.category_service import CategoryTrendingService
        from app.models.word import CategoryTrendingPhrase
        
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
        
        return {
            "category": category,
            "phrases": phrases,
            "period": f"Last {days} days",
            "date_range": f"{start_date} to {end_date}",
            "total_count": len(phrases)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting category phrases: {str(e)}")

@router.get("/categories/activity", summary="Get top categories by trending activity")
def get_top_categories_activity(
    days: int = Query(7, description="Number of days to analyze"),
    limit: int = Query(10, description="Number of top categories to return"),
    db: Session = Depends(get_db)
):
    """Get top categories ranked by trending phrase activity"""
    try:
        from app.services.category_service import CategoryTrendingService
        
        service = CategoryTrendingService(db)
        
        # Get today's activity (or specify date range)
        top_categories = service.get_top_categories_by_activity(
            analysis_date=date.today(),
            limit=limit
        )
        
        return {
            "top_categories": top_categories,
            "analysis_date": str(date.today()),
            "total_categories": len(top_categories)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting category activity: {str(e)}")

@router.get("/categories/trends", summary="Get category trend comparison")
def get_category_trends_comparison(
    days: int = Query(7, description="Number of days to analyze trends"),
    db: Session = Depends(get_db)
):
    """Compare trending activity across categories over time"""
    try:
        from app.services.category_service import CategoryTrendingService
        
        service = CategoryTrendingService(db)
        
        # Get trend comparison
        trends = service.get_category_trends_comparison(days=days)
        
        return {
            "category_trends": trends,
            "analysis_period": f"Last {days} days",
            "categories_analyzed": len(trends)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting category trends: {str(e)}")

@router.get("/categories/distribution", summary="Get article distribution by category")
def get_category_distribution(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get distribution of articles across categories"""
    try:
        from app.services.category_service import CategoryTrendingService
        
        service = CategoryTrendingService(db)
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get distribution
        distribution = service.get_category_distribution(
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "category_distribution": distribution,
            "period": f"Last {days} days",
            "date_range": f"{start_date} to {end_date}",
            "total_articles": sum(distribution.values()) if distribution else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting category distribution: {str(e)}")

@router.post("/categories/analyze", summary="Analyze articles and extract category-wise trending phrases")
def analyze_category_phrases(
    request: TrendingPhrasesRequest,
    db: Session = Depends(get_db)
):
    """Analyze provided articles to extract category-wise trending phrases"""
    try:
        from app.services.category_service import CategoryTrendingService
        from app.routes.helpers import detect_category_from_url
        
        service = CategoryTrendingService(db)
        
        # Convert request data to articles list
        articles = []
        for i, text in enumerate(request.texts):
            articles.append({
                'title': f"Article {i+1}",
                'content': text,
                'url': f"https://example.com/article{i+1}"
            })
        
        # Analyze category phrases
        category_phrases = service.analyze_category_phrases_by_content(
            articles=articles,
            min_phrase_length=3,
            max_phrases_per_category=20
        )
        
        # Save to database if requested
        if hasattr(request, 'save_to_db') and request.save_to_db:
            saved_count = service.save_category_trending_phrases(
                category_phrases,
                date.today(),
                source="api_analysis"
            )
            
            return {
                "category_phrases": category_phrases,
                "analysis_date": str(date.today()),
                "categories_found": len(category_phrases),
                "total_phrases": sum(len(phrases) for phrases in category_phrases.values()),
                "saved_to_db": saved_count
            }
        else:
            return {
                "category_phrases": category_phrases,
                "analysis_date": str(date.today()),
                "categories_found": len(category_phrases),
                "total_phrases": sum(len(phrases) for phrases in category_phrases.values())
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing category phrases: {str(e)}")

@router.get("/categories/detect", summary="Test category detection for a URL")
def test_category_detection(
    url: str = Query(..., description="URL to analyze"),
    title: str = Query("", description="Article title (optional)"),
    content: str = Query("", description="Article content (optional)"),
):
    """Test the enhanced category detection system"""
    try:
        from app.routes.helpers import detect_category_from_url
        
        # Detect category
        detected_category = detect_category_from_url(url, title, content)
        
        return {
            "url": url,
            "title": title[:100] + "..." if len(title) > 100 else title,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "detected_category": detected_category,
            "detection_method": "URL pattern + Content analysis",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting category: {str(e)}")
