#!/usr/bin/env python3
"""
Final verification for 10 words per category
"""

import re

def test_10_word_parsing():
    """Test that 10 word parsing works correctly"""
    
    print("🧪 Testing 10 word parsing...")
    
    # Mock LLM response with 10 words
    mock_response = """জাতীয়:
1. প্রথম শব্দ
2. দ্বিতীয় শব্দ
3. তৃতীয় শব্দ
4. চতুর্থ শব্দ
5. পঞ্চম শব্দ
6. ষষ্ঠ শব্দ
7. সপ্তম শব্দ
8. অষ্টম শব্দ
9. নবম শব্দ
10. দশম শব্দ

অর্থনীতি:
1. ব্যাংক বন্ধ
2. অর্থনীতি
3. মূল্যস্ফীতি
4. রিজার্ভ বেড়ে
5. ইসলামী ব্যাংক
6. এনবিআর
7. বাংলাদেশ ব্যাংক
8. সংকট কাটাতে
9. বাণিজ্য বাণিজ্য
10. আর্থিক পরিকল্পনা"""
    
    # Use updated regex pattern
    current_category = None
    category_wise_final = {}
    
    lines = mock_response.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Check if this is a category header
        if line.endswith(':') and not re.match(r'^[১২৩৪৫৬৭৮৯১০1-9][\.\)]\s*', line):
            current_category = line.replace(':', '').strip()
            if current_category not in category_wise_final:
                category_wise_final[current_category] = []
            print(f"✅ Found category: '{current_category}'")
            continue
        
        # Extract numbered items with updated pattern (NO LIMITS)
        if current_category and (re.match(r'^([১২৩৪৫৬৭৮৯১০]|1[0]|[1-9])[\.\)]\s*', line) or re.match(r'^১০[\.\)]\s*', line)):
            # Remove number prefix and clean up
            word = re.sub(r'^([১২৩৪৫৬৭৮৯১০]|1[0]|[1-9])[\.\)]\s*', '', line).strip()
            word = re.sub(r'^১০[\.\)]\s*', '', word).strip()
            word = re.sub(r'[।\.]+$', '', word).strip()
            
            if word and len(word) > 1:
                category_wise_final[current_category].append(word)
                print(f"✅ Added word to {current_category}: '{word}' ({len(category_wise_final[current_category])}/total)")
    
    # Check results
    print(f"\n📊 Final Results:")
    all_correct = True
    
    for category, words in category_wise_final.items():
        print(f"   {category}: {len(words)} words")
        if len(words) != 10:
            print(f"   ❌ Expected 10 words, got {len(words)}")
            all_correct = False
        else:
            print(f"   ✅ Perfect: {len(words)} words")
            # Show first 3 and last word
            if len(words) >= 4:
                print(f"      - {words[0]}, {words[1]}, {words[2]}, ..., {words[-1]}")
    
    return all_correct

def test_regex_patterns():
    """Test individual regex patterns"""
    
    print(f"\n🧪 Testing regex patterns...")
    
    test_cases = [
        "1. প্রথম শব্দ",
        "9. নবম শব্দ", 
        "10. দশম শব্দ",  # This was failing before
        "১. প্রথম শব্দ",
        "৯. নবম শব্দ",
        "১০. দশম শব্দ"
    ]
    
    # Test new pattern
    pattern = r'^([১২৩৪৫৬৭৮৯১০]|1[0]|[1-9])[\.\)]\s*'
    
    all_passed = True
    for test_case in test_cases:
        match = re.match(pattern, test_case)
        if match:
            cleaned = re.sub(pattern, '', test_case).strip()
            print(f"   ✅ '{test_case}' -> '{cleaned}'")
        else:
            print(f"   ❌ '{test_case}' -> NO MATCH")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("🚀 Final verification for 10 words per category...\n")
    
    test1 = test_regex_patterns()
    test2 = test_10_word_parsing()
    
    print(f"\n🎯 Test Results:")
    print(f"   ✅ Regex patterns: {'PASS' if test1 else 'FAIL'}")
    print(f"   ✅ 10 word parsing: {'PASS' if test2 else 'FAIL'}")
    
    if test1 and test2:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"\n📋 Expected Results:")
        print(f"   - Each category will have exactly 10 words")
        print(f"   - Frequency will be calculated from scraped article headings")
        print(f"   - Frontend will display 10 words per category with frequency badges")
    else:
        print(f"\n⚠️ Some tests failed. Check the issues above.")
