#!/usr/bin/env python3

import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath('.'))

from app.db.database import engine
from app.models.word import TrendingPhrase
from sqlalchemy.orm import sessionmaker

def check_db():
    """Quick check of database state"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check current database state for জাতীয় নির্বাচন
        result = session.query(TrendingPhrase).filter(
            TrendingPhrase.phrase == 'জাতীয় নির্বাচন'
        ).all()

        print('জাতীয় নির্বাচন entries:')
        for entry in result:
            print(f'ID: {entry.id}, Date: {entry.date}, Frequency: {entry.frequency}, Type: {entry.phrase_type}, Source: {entry.source}')

        # Count total phrases
        total_count = session.query(TrendingPhrase).count()
        print(f'\nTotal trending phrases: {total_count}')
        
        # Check recent phrases
        recent = session.query(TrendingPhrase).order_by(TrendingPhrase.id.desc()).limit(5).all()
        print('\nRecent 5 phrases:')
        for phrase in recent:
            print(f'- {phrase.phrase} (Freq: {phrase.frequency}, Source: {phrase.source})')
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    check_db()
