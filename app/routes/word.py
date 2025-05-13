from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.db.database import SessionLocal
from app.models.word import Word

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
        raise HTTPException(status_code=404, detail="No word found for today")

    return {"date": today.isoformat(), "word": word_obj.word}


@router.post("/word", summary="Add a word of the day for today")
def set_word_of_the_day(db: Session = Depends(get_db)):
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
    return {"message": "Not ready yet, senor"}
