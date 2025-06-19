#!/usr/bin/env python3
"""
Test script for the advanced Bengali NLP filtering system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.advanced_bengali_nlp import TrendingBengaliAnalyzer

def test_filtering_system():
    """Test the advanced filtering system with sample data"""
    print("🔬 Testing Advanced Bengali NLP Filtering System")
    print("=" * 60)
    
    analyzer = TrendingBengaliAnalyzer()
    
    # Test data with realistic Bengali examples including issues we want to filter
    test_keywords = [
        ('ইরান', 0.95),
        ('হামলা', 0.90),
        ('ইরানে হামলা', 0.85),                    # Should be consolidated with above
        ('ইসরায়েল-ইরানের সংঘাত', 0.80),            # Good quality phrase
        ('ট্রাম্প', 0.75),                        # Should be filtered (person name)
        ('নেতানিয়াহু', 0.70),                    # Should be filtered (person name)
        ('প্রধানমন্ত্রী শেখ হাসিনা', 0.68),       # Should be filtered (person name)
        ('নির্বাচন', 0.65),                      # Good quality
        ('অর্থনীতি', 0.60),                      # Good quality
        ('বাংলাদেশের অর্থনীতি', 0.55),           # Should be consolidated with above
        ('জ্বালানি সংকট', 0.50),                 # Good quality phrase
        ('করা', 0.45),                           # Should be filtered (stop word)
        ('সরকার বলেছেন যে', 0.40),              # Should be filtered (low quality pattern)
        ('মোদি', 0.35),                          # Should be filtered (person name)
        ('শিক্ষা', 0.30),                        # Good quality
    ]
    
    print("📋 Original Keywords:")
    for i, (keyword, score) in enumerate(test_keywords, 1):
        print(f"  {i:2d}. {keyword:30s} - Score: {score:.3f}")
    
    print(f"\n🔄 Applying Advanced Filtering (max_results=10)...")
    
    # Apply filtering
    filtered = analyzer.filter_and_deduplicate_keywords(test_keywords, max_results=10)
    
    print("\n✨ Filtered Keywords:")
    for i, (keyword, score) in enumerate(filtered, 1):
        print(f"  {i:2d}. {keyword:30s} - Score: {score:.3f}")
    
    print(f"\n📊 Results Summary:")
    print(f"  • Original count: {len(test_keywords)}")
    print(f"  • Filtered count: {len(filtered)}")
    print(f"  • Reduction: {len(test_keywords) - len(filtered)} phrases removed")
    
    # Check what was filtered out
    original_phrases = {phrase for phrase, _ in test_keywords}
    filtered_phrases = {phrase for phrase, _ in filtered}
    removed_phrases = original_phrases - filtered_phrases
    
    print(f"\n🗑️  Removed Phrases:")
    for phrase in removed_phrases:
        print(f"  ❌ {phrase}")
    
    # Check for person names
    person_indicators = ['ট্রাম্প', 'নেতানিয়াহু', 'শেখ', 'মোদি']
    person_names_found = []
    for phrase, _ in filtered:
        for indicator in person_indicators:
            if indicator in phrase:
                person_names_found.append(phrase)
                break
    
    print(f"\n🧑 Person Name Check:")
    if person_names_found:
        print(f"  ❌ Found person names in filtered results:")
        for name in person_names_found:
            print(f"     - {name}")
    else:
        print(f"  ✅ No person names found in filtered results!")
    
    # Check for quality improvements
    stop_words_found = []
    for phrase, _ in filtered:
        if phrase in ['করা', 'হওয়া', 'দেওয়া']:
            stop_words_found.append(phrase)
    
    print(f"\n📝 Stop Word Check:")
    if stop_words_found:
        print(f"  ❌ Found stop words in filtered results:")
        for word in stop_words_found:
            print(f"     - {word}")
    else:
        print(f"  ✅ No stop words found in filtered results!")
    
    # Overall assessment
    print(f"\n🎯 Overall Assessment:")
    success_criteria = [
        len(filtered) <= 10,  # Respects max_results
        len(filtered) < len(test_keywords),  # Actually filtered something
        not person_names_found,  # No person names
        not stop_words_found,  # No stop words
    ]
    
    if all(success_criteria):
        print(f"  🎉 SUCCESS: Advanced filtering system is working correctly!")
        return True
    else:
        print(f"  ⚠️  PARTIAL: Some filtering criteria need improvement")
        return False

if __name__ == "__main__":
    test_filtering_system()
