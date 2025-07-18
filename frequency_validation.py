#!/usr/bin/env python3
"""
Final validation script for frequency calculation fix
"""

import sys
import os
sys.path.append('/home/bs01127/IMLI-Project')

def test_frequency_calculation():
    """Test the improved frequency calculation function"""
    
    print("🎯 FINAL VALIDATION: Frequency Calculation Fix")
    print("=" * 60)
    
    # Import the function
    try:
        from app.services.category_llm_analyzer import calculate_phrase_frequency_in_articles
        print("✅ Successfully imported frequency calculation function")
    except Exception as e:
        print(f"❌ Failed to import function: {e}")
        return False
    
    # Test case 1: Exact match
    print("\n1️⃣ Testing exact phrase matching:")
    test_articles_1 = [
        {'title': 'ক্ষুদ্র নৃগোষ্ঠীর উন্নয়ন প্রকল্প', 'heading': 'ক্ষুদ্র নৃগোষ্ঠীর উন্নয়ন প্রকল্প'},
        {'title': 'আদিবাসী সম্প্রদায়ের অধিকার', 'heading': 'আদিবাসী সম্প্রদায়ের অধিকার'},
        {'title': 'ক্ষুদ্র নৃগোষ্ঠী বিষয়ক মন্ত্রণালয়', 'heading': 'ক্ষুদ্র নৃগোষ্ঠী বিষয়ক মন্ত্রণালয়'}
    ]
    
    result_1 = calculate_phrase_frequency_in_articles('ক্ষুদ্র নৃগোষ্ঠী', test_articles_1)
    expected_1 = 2  # Should find 2 exact matches
    
    print(f"   Expected: {expected_1}, Got: {result_1.get('frequency', 0)}")
    print(f"   Result: {'✅ PASS' if result_1.get('frequency', 0) == expected_1 else '❌ FAIL'}")
    
    # Test case 2: No false positives for similar phrases
    print("\n2️⃣ Testing false positive prevention:")
    test_articles_2 = [
        {'title': 'ক্ষুদ্র জাতিগোষ্ঠীর উন্নয়ন', 'heading': 'ক্ষুদ্র জাতিগোষ্ঠীর উন্নয়ন'},
        {'title': 'ক্ষুদ্র ব্যবসায়ী নৃগোষ্ঠী', 'heading': 'ক্ষুদ্র ব্যবসায়ী নৃগোষ্ঠী'},  # Words far apart
        {'title': 'নৃগোষ্ঠী ও ক্ষুদ্র কৃষক', 'heading': 'নৃগোষ্ঠী ও ক্ষুদ্র কৃষক'}     # Words far apart
    ]
    
    result_2 = calculate_phrase_frequency_in_articles('ক্ষুদ্র নৃগোষ্ঠী', test_articles_2)
    expected_2 = 0  # Should find 0 matches (no exact phrase, only similar)
    
    print(f"   Expected: {expected_2}, Got: {result_2.get('frequency', 0)}")
    print(f"   Result: {'✅ PASS' if result_2.get('frequency', 0) == expected_2 else '❌ FAIL'}")
    
    # Test case 3: Proximity matching for reasonable variations
    print("\n3️⃣ Testing proximity matching:")
    test_articles_3 = [
        {'title': 'ক্ষুদ্র ও নৃগোষ্ঠী উন্নয়ন', 'heading': 'ক্ষুদ্র ও নৃগোষ্ঠী উন্নয়ন'},  # Close words
        {'title': 'ক্ষুদ্র এবং নৃগোষ্ঠী', 'heading': 'ক্ষুদ্র এবং নৃগোষ্ঠী'},           # Close words
    ]
    
    result_3 = calculate_phrase_frequency_in_articles('ক্ষুদ্র নৃগোষ্ঠী', test_articles_3)
    expected_3 = 2  # Should find 2 proximity matches
    
    print(f"   Expected: {expected_3}, Got: {result_3.get('frequency', 0)}")
    print(f"   Result: {'✅ PASS' if result_3.get('frequency', 0) == expected_3 else '❌ FAIL'}")
    
    # Summary
    all_tests_passed = (
        result_1.get('frequency', 0) == expected_1 and
        result_2.get('frequency', 0) == expected_2 and
        result_3.get('frequency', 0) == expected_3
    )
    
    print(f"\n🎯 FINAL RESULT: {'✅ ALL TESTS PASSED' if all_tests_passed else '❌ SOME TESTS FAILED'}")
    
    if all_tests_passed:
        print("\n✅ FREQUENCY CALCULATION IS NOW WORKING CORRECTLY!")
        print("   - Exact phrase matching: ✅")
        print("   - False positive prevention: ✅") 
        print("   - Proximity matching: ✅")
        print("\n🚀 Ready to deploy the improved frequency calculation!")
    else:
        print("\n❌ Some issues still exist in frequency calculation")
        
    return all_tests_passed

if __name__ == "__main__":
    test_frequency_calculation()
