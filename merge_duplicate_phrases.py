#!/usr/bin/env python3

import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath('.'))

from app.db.database import engine
from app.models.word import TrendingPhrase
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from collections import defaultdict

def merge_duplicate_phrases():
    """Merge duplicate trending phrases and fix frequency counts"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("Finding duplicate phrases...")
        
        # Find all phrases grouped by date, phrase, phrase_type, source
        duplicates = session.query(
            TrendingPhrase.date,
            TrendingPhrase.phrase, 
            TrendingPhrase.phrase_type,
            TrendingPhrase.source,
            func.count(TrendingPhrase.id).label('count')
        ).group_by(
            TrendingPhrase.date,
            TrendingPhrase.phrase,
            TrendingPhrase.phrase_type,
            TrendingPhrase.source
        ).having(func.count(TrendingPhrase.id) > 1).all()
        
        print(f"Found {len(duplicates)} sets of duplicate phrases")
        
        merged_count = 0
        deleted_count = 0
        
        for dup in duplicates:
            # Get all instances of this duplicate
            instances = session.query(TrendingPhrase).filter(
                TrendingPhrase.date == dup.date,
                TrendingPhrase.phrase == dup.phrase,
                TrendingPhrase.phrase_type == dup.phrase_type,
                TrendingPhrase.source == dup.source
            ).order_by(TrendingPhrase.id).all()
            
            if len(instances) <= 1:
                continue
                
            print(f"Merging {len(instances)} instances of '{dup.phrase}' on {dup.date}")
            
            # Keep the first instance and merge others into it
            main_instance = instances[0]
            total_frequency = sum(inst.frequency for inst in instances)
            max_score = max(inst.score for inst in instances)
            
            # Update main instance
            main_instance.frequency = total_frequency
            main_instance.score = max_score
            
            # Delete other instances
            for inst in instances[1:]:
                session.delete(inst)
                deleted_count += 1
                
            merged_count += 1
            
        session.commit()
        print(f"Merge completed!")
        print(f"Merged {merged_count} phrase groups")
        print(f"Deleted {deleted_count} duplicate entries")
        
        # Show some stats
        total_phrases = session.query(TrendingPhrase).count()
        print(f"Total phrases after merge: {total_phrases}")
        
    except Exception as e:
        print(f"Error during merge: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def show_sample_frequencies():
    """Show sample phrases with their frequencies"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get phrases with highest frequencies
        high_freq_phrases = session.query(TrendingPhrase).filter(
            TrendingPhrase.frequency > 1
        ).order_by(TrendingPhrase.frequency.desc()).limit(10).all()
        
        print("\nTop phrases by frequency:")
        for phrase in high_freq_phrases:
            print(f"'{phrase.phrase}' - Frequency: {phrase.frequency}, Score: {phrase.score:.2f}, Date: {phrase.date}")
            
    except Exception as e:
        print(f"Error showing samples: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    print("Merging duplicate trending phrases...")
    merge_duplicate_phrases()
    show_sample_frequencies()
