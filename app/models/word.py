from sqlalchemy import Column, String, Date
from app.db.database import Base

class Word(Base):
    __tablename__ = "words"

    date = Column(Date, primary_key=True, index=True)
    word = Column(String, nullable=False)
