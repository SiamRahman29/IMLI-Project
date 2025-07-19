#!/usr/bin/env python3

from app.db.database import SessionLocal
from app.models.word import Word, TrendingPhrase
from sqlalchemy import desc
from datetime import date
import json

def fix_trending_frequencies():
    db = SessionLocal()
    today = date.today()

    # Get today's word entry
    word_entry = db.query(Word).filter(Word.date == today).first()
    if word_entry and word_entry.selected_words:
        print('✅ Found selected_words data for today')
        selected_words = word_entry.selected_words
        print(f'📊 Total phrases: {len(selected_words)}')
        
        # Sample a few to see the structure
        for i, word_obj in enumerate(selected_words[:3]):
            print(f'🔍 Sample {i+1}: {word_obj}')
            
        print('\n🔄 Updating TrendingPhrase frequencies...')
        update_count = 0
        
        for word_obj in selected_words:
            word = word_obj.get('word', '').strip()
            category = word_obj.get('category', 'অজানা').strip()
            
            # Extract frequency from originalText structure
            frequency = 1
            if 'originalText' in word_obj and isinstance(word_obj['originalText'], dict):
                frequency = word_obj['originalText'].get('frequency', 1)
            elif 'frequency' in word_obj:
                frequency = word_obj.get('frequency', 1)
                
            if word and frequency > 1:
                # Find and update the corresponding TrendingPhrase
                trending_phrase = db.query(TrendingPhrase).filter(
                    TrendingPhrase.date == today,
                    TrendingPhrase.phrase == word,
                    TrendingPhrase.phrase_type == 'selected',
                    TrendingPhrase.source == 'user_selection'
                ).first()
                
                if trending_phrase:
                    old_freq = trending_phrase.frequency
                    trending_phrase.frequency = frequency
                    print(f'✅ Updated "{word}": {old_freq} → {frequency}')
                    update_count += 1
                else:
                    print(f'❌ Not found: "{word}"')
        
        db.commit()
        print(f'\n🎯 Updated {update_count} phrases with correct frequencies')
        return update_count
    else:
        print('❌ No selected_words data found for today')
        return 0

    db.close()

if __name__ == "__main__":
    fix_trending_frequencies()
