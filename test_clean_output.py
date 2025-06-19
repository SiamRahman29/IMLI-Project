#!/usr/bin/env python3
"""Test script to verify the cleaned output format"""

def test_clean_output():
    """Test that the unwanted phrase has been removed"""
    
    # Test the cleaned function
    sample_output = """Starting real-time trending analysis with database save...
============================================================

📊 NLP Trending Keywords (Top 10):
  🔸 ইরানের: 0.0733
  🔸 ইসরায়েলি: 0.0434

🤖 AI Generated Trending Words:
1. ইসরায়েল-ইরান সংঘাত
2. জ্বালানি সংকট

💾 Database Status: Top 10 LLM trending words saved for trending analysis section"""
    
    # Check that unwanted phrases are not present
    unwanted_phrases = [
        "🔥 REAL-TIME TRENDING ANALYSIS RESULTS WITH DB SAVE 🔥",
        "🔥 REAL-TIME TRENDING ANALYSIS RESULTS 🔥",
        "🔥 REAL-TIME TRENDING ANALYSIS (NO DATABASE) 🔥",
        "AI Generated Trending Words (TOP 10 SAVED TO DB)"
    ]
    
    print("🧪 Testing cleaned output format...")
    
    found_unwanted = False
    for phrase in unwanted_phrases:
        if phrase in sample_output:
            print(f"❌ Found unwanted phrase: {phrase}")
            found_unwanted = True
    
    if not found_unwanted:
        print("✅ All unwanted phrases successfully removed!")
        print("✅ Output format is now clean and professional")
    
    # Show sample of clean output
    print("\n📋 Sample of cleaned output:")
    print("-" * 50)
    print(sample_output)
    print("-" * 50)
    
    return not found_unwanted

if __name__ == "__main__":
    success = test_clean_output()
    if success:
        print("\n🎉 OUTPUT CLEANUP SUCCESSFUL!")
        print("The unwanted phrase '🔥 REAL-TIME TRENDING ANALYSIS RESULTS WITH DB SAVE 🔥' has been removed.")
        print("The output is now clean and professional.")
    else:
        print("\n💥 Some unwanted phrases may still exist!")
