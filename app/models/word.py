from sqlalchemy import Column, String, Date, Float, Integer, Text, DateTime, JSON
from app.db.database import Base
from sqlalchemy import Sequence
from datetime import datetime

class Word(Base):
    __tablename__ = "words"

    date = Column(Date, primary_key=True, index=True)
    word = Column(String, nullable=False)  # Main/primary word
    selected_words = Column(JSON, nullable=True)  # Array of all selected words with categories

class TrendingPhrase(Base):
    __tablename__ = "trending_phrases"
    
    id = Column(Integer, Sequence('phrase_id_seq'), primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    phrase = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    frequency = Column(Integer, nullable=False)
    phrase_type = Column(String, nullable=False)  # 'unigram', 'bigram', 'trigram'
    source = Column(String, nullable=False)  # 'news', 'social_media'

class WeeklyTrendingPhrase(Base):
    __tablename__ = "weekly_trending_phrases"
    
    id = Column(Integer, Sequence('weekly_phrase_id_seq'), primary_key=True, index=True)
    week_start = Column(Date, nullable=False, index=True)
    week_end = Column(Date, nullable=False)
    phrase = Column(String, nullable=False)
    total_score = Column(Float, nullable=False)
    average_score = Column(Float, nullable=False)
    total_frequency = Column(Integer, nullable=False)
    appearance_days = Column(Integer, nullable=False)  # How many days this week the phrase appeared
    phrase_type = Column(String, nullable=False)
    dominant_source = Column(String, nullable=False)  # Most common source for this phrase
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class CategoryTrendingPhrase(Base):
    __tablename__ = "category_trending_phrases"
    
    id = Column(Integer, Sequence('category_phrase_id_seq'), primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)  # রাজনীতি, অর্থনীতি, খেলাধুলা etc.
    phrase = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    frequency = Column(Integer, nullable=False)
    phrase_type = Column(String, nullable=False)  # 'unigram', 'bigram', 'trigram'
    source = Column(String, nullable=False)  # 'news', 'social_media'
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, Sequence('article_id_seq'), primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    url = Column(String, nullable=True)
    published_date = Column(Date, nullable=True)
    source = Column(String, nullable=False)
    category = Column(String, nullable=True)  # Add category field
    