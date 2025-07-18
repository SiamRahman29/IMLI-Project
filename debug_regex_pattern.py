#!/usr/bin/env python3
"""
Debug regex pattern matching for proximity
"""

import re

def test_regex_pattern():
    phrase_words = ['ক্ষুদ্র', 'নৃগোষ্ঠী']
    
    # Create pattern
    pattern_parts = []
    for i, word in enumerate(phrase_words):
        pattern_parts.append(re.escape(word))
        if i < len(phrase_words) - 1:
            # Between words, allow whitespace, punctuation, and short connector words
            pattern_parts.append(r'\s*(?:[।,\-\s]|ও|এবং|এর)*\s*')
    
    pattern = ''.join(pattern_parts)
    print(f"Regex pattern: {pattern}")
    
    # Test cases
    test_cases = [
        'ক্ষুদ্র ও নৃগোষ্ঠী উন্নয়ন',
        'ক্ষুদ্র এবং নৃগোষ্ঠী',
        'ক্ষুদ্র নৃগোষ্ঠী',
        'ক্ষুদ্র জাতিগোষ্ঠী',
        'ক্ষুদ্র ব্যবসায়ী নৃগোষ্ঠী'
    ]
    
    for test_case in test_cases:
        matches = re.findall(pattern, test_case, re.IGNORECASE)
        print(f"Text: '{test_case}' -> Matches: {len(matches)} {matches}")

if __name__ == "__main__":
    test_regex_pattern()
