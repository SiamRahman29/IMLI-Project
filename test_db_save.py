#!/usr/bin/env python3
"""Test script to verify LLM trending words are saved to database"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.db.database import SessionLocal, engine
from app.models.word import TrendingPhrase, Base
from app.routes.helpers import save_llm_trending_words_to_db
from datetime import date

def test_llm_save():
    """Test the LLM trending words save functionality"""
    print("🧪 Testing LLM trending words database save...")
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Clear any existing LLM generated data for today
        today = date.today()
        db.query(TrendingPhrase).filter(
            TrendingPhrase.source == 'llm_generated',
            TrendingPhrase.date == today
        ).delete()
        db.commit()
        
        # Test sample LLM response
        test_response = """
1. ইসরায়েল-ইরানের সংঘাত
2. জ্বালানি সংকট  
3. নির্বাচনী প্রচারণা
4. বন্যার পরিস্থিতি
5. শিক্ষা সংস্কার
6. অর্থনৈতিক মন্দা
7. করোনা ভ্যাকসিন
8. ক্রিকেট বিশ্বকাপ
9. রাজনৈতিক সংকট
10. প্রযুক্তি উন্নয়ন
        """
        
        print(f"📝 Test LLM response:")
        print(test_response)
        
        # Test the save function
        save_llm_trending_words_to_db(db, test_response, today, limit=10)
        
        # Verify saved data
        llm_phrases = db.query(TrendingPhrase).filter(
            TrendingPhrase.source == 'llm_generated',
            TrendingPhrase.date == today
        ).all()
        
        print(f"\n✅ Successfully saved {len(llm_phrases)} LLM phrases to database:")
        for i, phrase in enumerate(llm_phrases, 1):
            print(f"  {i}. {phrase.phrase} (score: {phrase.score}, type: {phrase.phrase_type})")
        
        # Test retrieval through trending analysis endpoints
        print(f"\n🔍 Testing retrieval of saved LLM words...")
        
        # Check if they appear in daily trending
        all_today_phrases = db.query(TrendingPhrase).filter(
            TrendingPhrase.date == today
        ).order_by(TrendingPhrase.score.desc()).all()
        
        print(f"📊 Total phrases for today: {len(all_today_phrases)}")
        if all_today_phrases:
            print("Top 5 phrases (all sources):")
            for phrase in all_today_phrases[:5]:
                print(f"  - {phrase.phrase} (source: {phrase.source}, score: {phrase.score})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_llm_save()
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
