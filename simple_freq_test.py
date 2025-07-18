#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/bs01127/IMLI-Project')

from app.services.category_llm_analyzer import calculate_phrase_frequency_in_articles

# Simple test
test_articles = [
    {
        'title': 'বিএনপি ক্ষমতায় গেলে ক্ষুদ্র জাতিগোষ্ঠীর উন্নয়নে পৃথক অধিদপ্তর গঠন করা হবে',
        'heading': 'বিএনপি ক্ষমতায় গেলে ক্ষুদ্র জাতিগোষ্ঠীর উন্নয়নে পৃথক অধিদপ্তর গঠন করা হবে'
    },
    {
        'title': 'আদিবাসী সম্প্রদায়ের অধিকার',
        'heading': 'আদিবাসী সম্প্রদায়ের অধিকার'
    },
    {
        'title': 'ক্ষুদ্র নৃগোষ্ঠীর উন্নয়ন প্রকল্প',
        'heading': 'ক্ষুদ্র নৃগোষ্ঠীর উন্নয়ন প্রকল্প'
    }
]

def test_frequency():
    print("🧪 Testing improved frequency calculation")
    print("=" * 50)
    
    # Test cases
    test_phrases = [
        'ক্ষুদ্র নৃগোষ্ঠী',
        'ক্ষুদ্র জাতিগোষ্ঠী',
        'আদিবাসী',
        'উন্নয়ন'
    ]
    
    for phrase in test_phrases:
        print(f"\n🔍 Testing phrase: '{phrase}'")
        result = calculate_phrase_frequency_in_articles(phrase, test_articles)
        print(f"Result: {result}")
        
        # Manual verification
        manual_count = 0
        for i, article in enumerate(test_articles):
            article_text = ""
            for field in ['title', 'heading']:
                if article.get(field):
                    article_text += " " + str(article[field])
            article_text = article_text.lower()
            
            if phrase.lower() in article_text:
                manual_count += 1
                print(f"  Manual match in article {i+1}: '{article_text}'")
        
        print(f"  Manual count: {manual_count}")
        print(f"  Function count: {result.get('frequency', 0)}")
        print(f"  Match: {'✅' if manual_count == result.get('frequency', 0) else '❌'}")

if __name__ == "__main__":
    test_frequency()
