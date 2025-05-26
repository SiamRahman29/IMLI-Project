from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.db.database import SessionLocal
from app.models.word import Word
from app.routes.helpers import get_trending_words
from app.dto.dtos import TrendingWordsResponse

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
    today = date.today()
    word_obj = db.query(Word).filter(Word.date == today).first()

    if word_obj is None:
        return {"message": "Today's word not set yet, check back later", "date": today.isoformat()}

    return {"date": today.isoformat(), "word": word_obj.word}


@router.post("/generate_candidates", summary="Generate a list of candidates for trending words")
def generate_candidates(db_session: Session = Depends(get_db)):
    
    """
    today = date.today()
    existing = db.query(Word).filter(Word.date == today).first()

    if existing:
        existing.word = word
    else:
        new_word = Word(date=today, word=word)
        db.add(new_word)

    db.commit()
    return {"message": "Word of the day saved", "date": today.isoformat(), "word": word}
    """
    try:
        words = get_trending_words(db_session)
        if not words:
            raise HTTPException(status_code=404, detail="No trending words found")
        return TrendingWordsResponse(
            date=date.today().isoformat(),
            words=words
        )
    except Exception as e:
        if e.status_code == 429:
            raise HTTPException(status_code=429, detail="Rate limit reached. Please try again later.")
        raise HTTPException(status_code=500, detail="An error occurred while generating candidates for trending words.")
        
    
# TODO: Rename endpoints to be better
# TODO: Turn this into a trending_words endpoint and allow user to reject words from the list instead of choosing one
@router.post("/set_word_of_the_day", summary="Set today's word of the day")
def set_word_of_the_day(new_word: str, db: Session = Depends(get_db)):
    """
    Sets the word of the day for today.
    """
    if not new_word:
        raise HTTPException(status_code=400, detail="Missing parameter: word cannot be empty")
    # TODO: Figure out what to do if a word is already set for today
    today = date.today()
    existing_word = db.query(Word).filter(Word.date == today).first()

    if existing_word:
        existing_word.word = new_word
    else:
        new_word = Word(date=today, word=new_word)
        db.add(new_word)

    db.commit()
    return {"message": "Word of the day saved", "date": today.isoformat(), "word": new_word}


