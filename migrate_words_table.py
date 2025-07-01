#!/usr/bin/env python3
"""
Database migration script to add selected_words JSON column to words table
"""
import sys
import os
sys.path.append('.')

def migrate_database():
    """Add selected_words column to words table"""
    print("🔄 Starting database migration...")
    
    try:
        from app.db.database import engine
        import sqlite3
        
        # Connect to SQLite database
        db_path = "words.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(words)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'selected_words' in columns:
            print("✅ Column 'selected_words' already exists")
            conn.close()
            return True
        
        # Add the new column
        print("🆕 Adding 'selected_words' column...")
        cursor.execute("ALTER TABLE words ADD COLUMN selected_words TEXT")
        
        conn.commit()
        conn.close()
        
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def test_migration():
    """Test that the migration worked"""
    print("\n🧪 Testing migration...")
    
    try:
        from app.db.database import SessionLocal
        from app.models.word import Word
        from datetime import date
        import json
        
        db = SessionLocal()
        
        # Test creating a word with selected_words
        test_data = [
            {'word': 'টেস্ট শব্দ', 'category': 'পরীক্ষা', 'originalText': 'টেস্ট শব্দ'}
        ]
        
        today = date.today()
        existing_word = db.query(Word).filter(Word.date == today).first()
        
        if existing_word:
            existing_word.selected_words = test_data
        else:
            test_word = Word(
                date=today,
                word='টেস্ট শব্দ',
                selected_words=test_data
            )
            db.add(test_word)
        
        db.commit()
        
        # Retrieve and verify
        saved_word = db.query(Word).filter(Word.date == today).first()
        if saved_word and saved_word.selected_words:
            print(f"✅ Test passed! Selected words: {saved_word.selected_words}")
        else:
            print("⚠️ Test warning: No selected_words found")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Database Migration Tool")
    print("=" * 50)
    
    # Run migration
    migration_success = migrate_database()
    
    if migration_success:
        # Test migration
        test_migration()
    
    print("\n✅ Migration process completed!")
