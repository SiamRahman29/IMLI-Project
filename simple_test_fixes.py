#!/usr/bin/env python3
"""
Simple test to verify JSON parsing fix
"""

import sys
sys.path.append('/home/bs01127/IMLI-Project')

def test_json_parsing():
    """Test the robust JSON parsing"""
    print("Testing JSON parsing...")
    
    try:
        from app.services.category_llm_analyzer import parse_llm_response_robust
        
        # Test cases
        test_cases = [
            # Good JSON
            '{"trending_words": ["শব্দ১", "শব্দ২", "শব্দ৩"]}',
            
            # Malformed JSON (like the error you showed)
            '''
            Some text before
            "trending_words": [
                "মোবাইল নিরাপত্তা",
                "সাইবার নিরাপত্তা",
                "ম্যালওয়্যার হামলা"
            ]
            Some text after
            ''',
            
            # Bengali text without proper JSON
            '''
            ১. সাইবার নিরাপত্তা
            ২. কৃত্রিম বুদ্ধিমত্তা  
            ৩. রোবট প্রযুক্তি
            '''
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest case {i}:")
            print(f"Input: {test_case[:100]}...")
            try:
                result = parse_llm_response_robust(test_case)
                print(f"Output: {result}")
                print(f"Count: {len(result)}")
            except Exception as e:
                print(f"Error: {e}")
                
    except Exception as e:
        print(f"Import error: {e}")
        import traceback
        traceback.print_exc()

def test_simple_category_check():
    """Simple category check"""
    print("\nTesting category articles...")
    
    # Sample articles with different categories
    sample_articles = [
        {'category': 'সাহিত্য-সংস্কৃতি', 'title': 'Test 1'},
        {'category': 'ক্ষুদ্র নৃগোষ্ঠী', 'title': 'Test 2'},
        {'category': 'অর্থনীতি', 'title': 'Test 3'},
    ]
    
    target_categories = ['সাহিত্য-সংস্কৃতি', 'ক্ষুদ্র নৃগোষ্ঠী']
    
    for target in target_categories:
        matching = [art for art in sample_articles if art.get('category') == target]
        print(f"Category '{target}': {len(matching)} articles")
        for art in matching:
            print(f"  - {art['title']}")

if __name__ == "__main__":
    print("🧪 Starting simple tests...\n")
    test_json_parsing()
    test_simple_category_check()
    print("\n✅ Tests completed!")
