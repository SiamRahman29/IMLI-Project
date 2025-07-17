#!/usr/bin/env python3
"""
Debug frequency counting
"""

import sys
sys.path.append('/home/bs01127/IMLI-Project')

from app.services.category_llm_analyzer import calculate_phrase_frequency_in_articles

def debug_frequency():
    """Debug frequency calculation"""
    
    articles = [
        {
            'title': 'নতুন শিক্ষা নীতি ঘোষণা',
            'heading': 'শিক্ষা ব্যবস্থায় পরিবর্তন',
            'content': 'বিস্তারিত তথ্য...',
            'source': 'prothom_alo'
        },
        {
            'title': 'অর্থনৈতিক উন্নয়নে নতুন পদক্ষেপ',
            'heading': 'সরকারের নতুন ঘোষণা',
            'content': 'অর্থনীতি নিয়ে আলোচনা...',
            'source': 'bdnews24'
        }
    ]
    
    phrase = "নতুন"
    phrase_lower = phrase.lower().strip()
    
    print(f"🔍 Debugging frequency calculation for phrase: '{phrase}'")
    print(f"🔍 Phrase lowercase: '{phrase_lower}'")
    
    total_count = 0
    for i, article in enumerate(articles):
        article_text = ""
        # ONLY use heading/title fields for frequency calculation
        for field in ['title', 'heading']:
            if article.get(field):
                article_text += " " + str(article[field])
        
        article_text = article_text.lower()
        print(f"\n📄 Article {i+1}:")
        print(f"   Title: {article.get('title', 'N/A')}")
        print(f"   Heading: {article.get('heading', 'N/A')}")
        print(f"   Combined text: '{article_text.strip()}'")
        
        # Count occurrences in this article
        count_in_article = article_text.count(phrase_lower)
        total_count += count_in_article
        print(f"   Count in this article: {count_in_article}")
    
    print(f"\n📊 Total count: {total_count}")
    
    # Now run the actual function
    freq_stats = calculate_phrase_frequency_in_articles(phrase, articles)
    print(f"📊 Function result: {freq_stats}")

if __name__ == "__main__":
    debug_frequency()
