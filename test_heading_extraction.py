#!/usr/bin/env python3
"""
Test script to verify heading extraction and text optimization
"""

import requests
import json
from datetime import datetime

def test_text_extraction():
    """Test the text extraction and heading processing"""
    print("🧪 Testing Bengali Newspaper Heading Extraction System")
    print("=" * 60)
    
    try:
        # Test the API endpoint
        url = "http://localhost:8000/api/v2/generate_candidates"
        response = requests.post(url, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ API Response Successful!")
            print(f"📊 Response Length: {len(str(data))} characters")
            
            # Check for AI candidates
            ai_candidates = data.get('ai_candidates', '')
            print(f"\n🤖 AI Candidates Preview:")
            print(f"Length: {len(ai_candidates)} characters")
            print(f"First 300 chars: {ai_candidates[:300]}...")
            
            # Look for comma-separated structure
            if ',' in ai_candidates and 'trending' in ai_candidates.lower():
                print("\n✅ Comma separation detected in AI response")
            else:
                print("\n⚠️ No clear comma separation found")
            
            # Check for Bengali content
            import re
            bengali_words = re.findall(r'[\u0980-\u09FF]+', ai_candidates)
            print(f"\n📝 Bengali words found: {len(bengali_words)}")
            print(f"Sample Bengali words: {bengali_words[:10]}")
            
            # Check for complete sentences/phrases (should be longer than just keywords)
            lines = ai_candidates.split('\n')
            meaningful_lines = [line.strip() for line in lines if line.strip() and len(line.strip()) > 10]
            print(f"\n📄 Meaningful content lines: {len(meaningful_lines)}")
            for i, line in enumerate(meaningful_lines[:5]):
                print(f"  {i+1}. {line[:80]}...")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_text_extraction()
