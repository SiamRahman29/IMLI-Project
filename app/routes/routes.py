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
