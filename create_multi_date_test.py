#!/usr/bin/env python3

import sys
import os
from datetime import date, timedelta

# Add project root to Python path
sys.path.append(os.path.abspath('.'))

from app.db.database import engine
from app.models.word import TrendingPhrase
from app.routes.helpers import add_or_update_trending_phrase
from sqlalchemy.orm import sessionmaker

def create_multi_date_phrases():
    """Create phrases with multiple dates to test graph functionality"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        today = date.today()
        
        # Create a phrase across multiple dates
        test_phrase = "বাংলাদেশ ক্রিকেট"
        
        # Add same phrase for last 5 days with different frequencies
        used_dates = set()
        for i in range(5):
            target_date = today - timedelta(days=i)
            if target_date in used_dates:
                continue  # Skip duplicate date
            used_dates.add(target_date)
            frequency = i + 1  # 1, 2, 3, 4, 5
            score = 80.0 + (i * 5)  # 80, 85, 90, 95, 100
            
            # Use the helper function to properly handle frequency
            phrase_obj = add_or_update_trending_phrase(
                db=session,
                date=target_date,
                phrase=test_phrase,
                score=score,
                frequency=frequency,
                phrase_type="test",
                source="test_data"
            )
            
            if phrase_obj:
                print(f"✅ Added/Updated '{test_phrase}' for {target_date} with frequency {frequency}")
            else:
                print(f"❌ Failed to add '{test_phrase}' for {target_date}")
        
        session.commit()
        print(f"\n🎉 Successfully created multi-date data for '{test_phrase}'")
        
        # Verify the data
        all_entries = session.query(TrendingPhrase).filter(
            TrendingPhrase.phrase == test_phrase,
            TrendingPhrase.source == "test_data"
        ).order_by(TrendingPhrase.date.desc()).all()
        
        print(f"\n📊 Verification - Found {len(all_entries)} entries:")
        for entry in all_entries:
            print(f"  Date: {entry.date}, Frequency: {entry.frequency}, Score: {entry.score}")
            
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    print("Creating multi-date phrase data for graph testing...")
    create_multi_date_phrases()
