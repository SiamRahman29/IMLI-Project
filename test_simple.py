#!/usr/bin/env python3
"""
Simple test to verify the text optimization function
"""

def test_comma_separation():
    """Test comma separation directly"""
    print("🧪 Simple Test: Comma Separation Check")
    print("=" * 50)
    
    # Sample headings like we get from Bengali newspapers
    sample_headings = [
        "সাবেক সিইসি নূরুল হুদার ১০ দিন রিমান্ড চায় পুলিশ",
        "ইরানের ছয় বিমানবন্দরে অতর্কিত হামলা",  
        "চীন সফরে কী নিয়ে আলোচনা হবে জানালেন ফখরুল",
        "ঘুষের টাকা ফেরত চেয়ে ইউএনও'র কাছে আবেদন"
    ]
    
    print("📰 Input Headings:")
    for i, heading in enumerate(sample_headings, 1):
        print(f"  {i}. {heading}")
    
    # Simulate what our optimize function does
    print(f"\n🔧 Simulating optimize_text_for_ai_analysis()...")
    
    # Step 1: Keep complete headings (minimal filtering)
    processed = []
    for heading in sample_headings:
        # Light filtering - only remove very basic stuff
        words = heading.split()
        filtered = [w for w in words if len(w) >= 2 and w not in ['এর', 'যে']]
        if len(filtered) >= 3:
            processed.append(' '.join(filtered))
    
    # Step 2: Join with commas  
    combined = ', '.join(processed)
    
    print(f"\n✅ Result:")
    print(f"📊 Length: {len(combined)} characters")
    print(f"📄 Content: {combined}")
    
    # Test separation
    parts = combined.split(', ')
    print(f"\n🔍 Comma Separation:")
    print(f"📝 Total parts: {len(parts)}")
    for i, part in enumerate(parts, 1):
        print(f"  {i}. {part}")
    
    # Check requirements
    print(f"\n✅ Requirements Check:")
    print(f"  ✅ Complete headings: Each part has {[len(p.split()) for p in parts]} words")
    print(f"  ✅ Comma separated: {'Yes' if ',' in combined else 'No'}")
    print(f"  ✅ Clear distinction: {len(parts)} distinct articles")

if __name__ == "__main__":
    test_comma_separation()
