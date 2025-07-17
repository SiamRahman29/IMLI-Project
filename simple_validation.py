#!/usr/bin/env python3
"""
Simple validation script
"""

print("🧪 Testing parsing logic...")

import re

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
10. দশম শব্দ"""

current_category = None
category_wise_final = {}

lines = mock_response.split('\n')

for i, line in enumerate(lines):
    line = line.strip()
    if not line:
        continue
    
    print(f"Processing line {i}: '{line}'")
    
    # Check if this is a category header
    if line.endswith(':') and not re.match(r'^[১২৩৪৫৬৭৮৯১০1-9][\.\)]\s*', line):
        current_category = line.replace(':', '').strip()
        if current_category not in category_wise_final:
            category_wise_final[current_category] = []
        print(f"✅ Found category: '{current_category}'")
        continue
    
    # Extract numbered items (NO LIMIT CONDITIONS)
    if current_category and (re.match(r'^([১২৩৪৫৬৭৮৯১০]|10|[1-9])[\.\)]\s*', line) or re.match(r'^১০[\.\)]\s*', line)):
        # Remove number prefix and clean up
        word = re.sub(r'^([১২৩৪৫৬৭৮৯১০]|10|[1-9])[\.\)]\s*', '', line).strip()
        word = re.sub(r'^১০[\.\)]\s*', '', word).strip()
        word = re.sub(r'[।\.]+$', '', word).strip()
        
        if word and len(word) > 1:
            category_wise_final[current_category].append(word)
            print(f"✅ Added word to {current_category}: '{word}' ({len(category_wise_final[current_category])}/total)")

# Check results
for category, words in category_wise_final.items():
    print(f"📂 {category}: {len(words)} words")
    if len(words) == 10:
        print(f"✅ Category '{category}' has exactly 10 words")
    else:
        print(f"❌ Category '{category}' has {len(words)} words (expected 10)")

print("\n🎯 Validation completed!")
