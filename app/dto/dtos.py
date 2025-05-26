from pydantic import BaseModel

class TrendingWordsResponse(BaseModel):
    date: str
    words: list[str]