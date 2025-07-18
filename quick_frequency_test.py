#!/usr/bin/env python3
"""
Quick test of final frequency calculation with real sample data
"""

import sys
sys.path.append('/home/bs01127/IMLI-Project')

# Import the frequency calculation function
from app.services.category_llm_analyzer import calculate_phrase_frequency_in_articles

def test_with_sample_data():
    """Test frequency calculation with sample real data patterns"""
    
    print("🧪 TESTING FINAL FREQUENCY CALCULATION")
    print("=" * 50)
    
    # Sample articles that mimic real scraped data
    sample_articles = [
        {
            'title': 'বিএনপি ক্ষমতায় গেলে ক্ষুদ্র জাতিগোষ্ঠীর উন্নয়নে পৃথক অধিদপ্তর গঠন করা হবে',
            'heading': 'বিএনপি ক্ষমতায় গেলে ক্ষুদ্র জাতিগোষ্ঠীর উন্নয়নে পৃথক অধিদপ্তর গঠন করা হবে',
            'source': 'ethnic_minorities'
        },
        {
            'title': 'আদিবাসী সম্প্রদায়ের অধিকার ও পার্বত্য চট্টগ্রামের স্থিতিশীলতা',
            'heading': 'আদিবাসী সম্প্রদায়ের অধিকার ও পার্বত্য চট্টগ্রামের স্থিতিশীলতা',
            'source': 'ethnic_minorities'
        },
        {
            'title': 'পার্বত্য চট্টগ্রামে আদিবাসীদের ভূমি অধিকার নিয়ে আলোচনা',
            'heading': 'পার্বত্য চট্টগ্রামে আদিবাসীদের ভূমি অধিকার নিয়ে আলোচনা',
            'source': 'ethnic_minorities'
        },
        {
            'title': 'ওঁরাও নারী নেত্রীর সাথে শুভেচ্ছা বিনিময়',
            'heading': 'ওঁরাও নারী নেত্রীর সাথে শুভেচ্ছা বিনিময়',
            'source': 'ethnic_minorities'
        }
    ]
    
    # Test phrases that should work correctly
    test_phrases = [
        ('ক্ষুদ্র নৃগোষ্ঠী', 0),  # Should NOT match "ক্ষুদ্র জাতিগোষ্ঠী"
        ('আদিবাসী', 2),        # Should match in 2 articles
        ('পার্বত্য', 2),         # Should match in 2 articles  
        ('ওঁরাও', 1),            # Should match in 1 article
        ('ক্ষুদ্র জাতিগোষ্ঠী', 1)   # Should match exactly once
    ]
    
    for phrase, expected_count in test_phrases:
        print(f"\n🧮 Testing phrase: '{phrase}'")
        result = calculate_phrase_frequency_in_articles(phrase, sample_articles)
        
        actual_count = result['frequency']
        status = "✅ PASS" if actual_count == expected_count else "❌ FAIL"
        
        print(f"   Expected: {expected_count}, Got: {actual_count}")
        print(f"   Result: {status}")
        
        if actual_count != expected_count:
            print(f"   Full result: {result}")
    
    print(f"\n🎯 FINAL TEST COMPLETED!")

if __name__ == "__main__":
    test_with_sample_data()
