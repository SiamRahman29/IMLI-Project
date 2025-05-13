from fastapi import APIRouter, HTTPException
from datetime import date

router = APIRouter()

# Simulate in-memory "database" for now
fake_db = {}

@router.get("/", summary="Get today's word of the day")
def get_word_of_the_day():
    today = date.today().isoformat()
    word = fake_db.get(today)

    if word is None:
        raise HTTPException(status_code=404, detail="No word found for today")
    
    return {"date": today, "word": word}


@router.post("/word", summary="Add a word of the day for today")
def set_word_of_the_day(word: str):
    today = date.today().isoformat()
    fake_db[today] = word
    return {"message": "Word of the day set successfully", "date": today, "word": word}
