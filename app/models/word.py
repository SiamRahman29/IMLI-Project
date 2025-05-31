from sqlalchemy import Column, String, Date, Float, Integer, Text
from app.db.database import Base
from sqlalchemy import Sequence

class Word(Base):
    __tablename__ = "words"

    date = Column(Date, primary_key=True, index=True)
    word = Column(String, nullable=False)

class TrendingPhrase(Base):
    __tablename__ = "trending_phrases"
    
    id = Column(Integer, Sequence('phrase_id_seq'), primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    phrase = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    frequency = Column(Integer, nullable=False)
    phrase_type = Column(String, nullable=False)  # 'unigram', 'bigram', 'trigram'
    source = Column(String, nullable=False)  # 'news', 'social_media'

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, Sequence('article_id_seq'), primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    url = Column(String, nullable=True)
    published_date = Column(Date, nullable=True)
    source = Column(String, nullable=False)
    