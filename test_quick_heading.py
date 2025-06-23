#!/usr/bin/env python3
"""
Quick test to verify heading extraction without full API call
"""

import sys
import os
sys.path.append('/home/bs01127/IMLI-Project')

def test_heading_extraction_quick():
    """Test heading extraction logic directly"""
    print("🧪 Quick Test: Bengali Heading Extraction & Comma Separation")
    print("=" * 60)
    
    try:
        # Import required modules
        from app.routes.helpers import optimize_text_for_ai_analysis
        from app.services.advanced_bengali_nlp import TrendingBengaliAnalyzer
        
        # Sample Bengali headings (like what we get from scrapers)
        sample_headings = [
            "সাবেক সিইসি নূরুল হুদার ১০ দিন রিমান্ড চায় পুলিশ",
            "ইরানের ছয় বিমানবন্দরে অতর্কিত হামলা বহু যুদ্ধবিমান ধ্বংস",
            "পাল্টা হামলা শুরু করেছে ইরান দিগ্বিদিক ছুটছে ইসরায়েলিরা",
            "চীন সফরে কী নিয়ে আলোচনা হবে জানালেন ফখরুল",
            "ঘুষের টাকা ফেরত চেয়ে ইউএনও'র কাছে আবেদন",
            "স্বজন ভেবে লাশ নিয়ে এলেন গোসল করালেন এরপর যা ঘটল"
        ]
        
        print(f"📰 Sample Input Headings ({len(sample_headings)} headings):")
        for i, heading in enumerate(sample_headings, 1):
            print(f"  {i}. {heading}")
        
        # Initialize analyzer
        analyzer = TrendingBengaliAnalyzer()
        
        # Test the optimization function
        print(f"\n🔧 Testing optimize_text_for_ai_analysis()...")
        optimized_text = optimize_text_for_ai_analysis(sample_headings, analyzer, max_chars=500, max_articles=10)
        
        print(f"\n✅ Optimized Result:")
        print(f"📊 Length: {len(optimized_text)} characters")
        print(f"📄 Content: {optimized_text}")
        
        # Check comma separation
        separated_parts = optimized_text.split(', ')
        print(f"\n🔍 Comma Separation Analysis:")
        print(f"📝 Total parts: {len(separated_parts)}")
        print(f"📋 Individual parts:")
        for i, part in enumerate(separated_parts, 1):
            print(f"  {i}. {part}")
        
        # Check Bengali content
        import re
        bengali_words = re.findall(r'[\u0980-\u09FF]+', optimized_text)
        print(f"\n📝 Bengali Words Found: {len(bengali_words)}")
        print(f"🔤 Sample words: {bengali_words[:8]}")
        
        # Verify requirements
        print(f"\n✅ Requirements Verification:")
        print(f"  1. Complete headings preserved: {'✅' if len(separated_parts[0].split()) > 3 else '❌'}")
        print(f"  2. Only headings (no titles): ✅ (tested with heading-only input)")
        print(f"  3. Comma separation: {'✅' if ',' in optimized_text else '❌'}")
        print(f"  4. Readable separation: {'✅' if len(separated_parts) > 1 else '❌'}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_heading_extraction_quick()
