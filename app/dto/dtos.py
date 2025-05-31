from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date

class TrendingWordsResponse(BaseModel):
    date: str
    words: str

class TrendingPhraseResponse(BaseModel):
    date: str
    phrase: str
    score: float
    frequency: int
    phrase_type: str
    source: str

class DailyTrendingResponse(BaseModel):
    date: str
    total_phrases: int
    by_source: Dict[str, List[Dict[str, Any]]]
    by_phrase_type: Dict[str, List[Dict[str, Any]]]
    top_phrases: List[Dict[str, Any]]

class TrendingPhrasesRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    phrase_type: Optional[str] = None  # 'unigram', 'bigram', 'trigram'
    source: Optional[str] = None  # 'news', 'social_media'
    limit: Optional[int] = 10