#!/usr/bin/env python3

import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath('.'))

from app.db.database import engine
from app.models.word import TrendingPhrase
from sqlalchemy.orm import sessionmaker
from datetime import date

def create_test_phrases():
    """Create some test phrases to demonstrate frequency handling"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        today = date.today()
        
        # Test phrases with different frequencies
        test_phrases = [
            {"phrase": "জাতীয় নির্বাচন", "frequency": 3, "score": 75.5},
            {"phrase": "বাংলাদেশ ক্রিকেট", "frequency": 5, "score": 85.2},
            {"phrase": "করোনা ভাইরাস", "frequency": 8, "score": 92.1},
            {"phrase": "প্রধানমন্ত্রী", "frequency": 12, "score": 98.7},
        ]
        
        for test_phrase in test_phrases:
            # Check if phrase already exists
            existing = session.query(TrendingPhrase).filter(
                TrendingPhrase.date == today,
                TrendingPhrase.phrase == test_phrase["phrase"],
                TrendingPhrase.phrase_type == "test",
                TrendingPhrase.source == "test_data"
            ).first()
            
            if existing:
                existing.frequency = test_phrase["frequency"]
                existing.score = test_phrase["score"]
                print(f"Updated existing phrase: '{test_phrase['phrase']}' with frequency {test_phrase['frequency']}")
            else:
                new_phrase = TrendingPhrase(
                    date=today,
                    phrase=test_phrase["phrase"],
                    score=test_phrase["score"],
                    frequency=test_phrase["frequency"],
                    phrase_type="test",
                    source="test_data"
                )
                session.add(new_phrase)
                print(f"Created new phrase: '{test_phrase['phrase']}' with frequency {test_phrase['frequency']}")
        
        session.commit()
        print("Test phrases created successfully!")
        
        # Show all test phrases
        test_phrases_in_db = session.query(TrendingPhrase).filter(
            TrendingPhrase.source == "test_data"
        ).all()
        
        print("\nTest phrases in database:")
        for phrase in test_phrases_in_db:
            print(f"- '{phrase.phrase}' | Frequency: {phrase.frequency} | Score: {phrase.score}")
        
    except Exception as e:
        print(f"Error creating test phrases: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    print("Creating test phrases with different frequencies...")
    create_test_phrases()
