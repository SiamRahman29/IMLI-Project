from sqlalchemy import Column, String, Date
from app.db.database import Base
from sqlalchemy import Integer, Sequence

class Word(Base):
    __tablename__ = "words"

    date = Column(Date, primary_key=True, index=True)
    word = Column(String, nullable=False)

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, Sequence('article_id_seq'), primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    