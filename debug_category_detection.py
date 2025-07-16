#!/usr/bin/env python3
"""
Debug script to check category detection issue for ক্ষুদ্র নৃগোষ্ঠী
"""

import sys
sys.path.append('/home/bs01127/IMLI-Project')

def debug_category_detection():
    """Debug category detection for ক্ষুদ্র নৃগোষ্ঠী"""
    print("=== Debugging Category Detection ===")
    
    # Test scrapers
    try:
        from app.routes.helpers import scrape_ethnic_minorities, scrape_sahitya_sanskriti
        
        print("Testing scrape_ethnic_minorities()...")
        ethnic_articles = scrape_ethnic_minorities()
        print(f"Ethnic minorities articles: {len(ethnic_articles)}")
        
        if ethnic_articles:
            for i, article in enumerate(ethnic_articles[:2]):
                print(f"  Article {i+1}:")
                print(f"    Category: '{article.get('category', 'MISSING')}'")
                print(f"    Source: '{article.get('source', 'MISSING')}'")
                print(f"    Title: {article.get('title', 'MISSING')[:50]}...")
        
        print("\nTesting scrape_sahitya_sanskriti()...")
        sahitya_articles = scrape_sahitya_sanskriti()
        print(f"Sahitya sanskriti articles: {len(sahitya_articles)}")
        
        if sahitya_articles:
            for i, article in enumerate(sahitya_articles[:2]):
                print(f"  Article {i+1}:")
                print(f"    Category: '{article.get('category', 'MISSING')}'")
                print(f"    Source: '{article.get('source', 'MISSING')}'")
                print(f"    Title: {article.get('title', 'MISSING')[:50]}...")
                
    except Exception as e:
        print(f"Error testing scrapers: {e}")
        import traceback
        traceback.print_exc()

def debug_main_scraper():
    """Debug main scraper to see all categories"""
    print("\n=== Debugging Main Scraper Categories ===")
    
    try:
        from app.routes.helpers import scrape_bengali_news
        
        print("Running main scraper...")
        all_articles = scrape_bengali_news()
        print(f"Total articles from main scraper: {len(all_articles)}")
        
        # Count by category
        category_counts = {}
        for article in all_articles:
            category = article.get('category', 'NO_CATEGORY')
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1
        
        print("\nCategory distribution:")
        for category, count in category_counts.items():
            print(f"  '{category}': {count} articles")
            
        # Check for our target categories specifically
        target_categories = ['সাহিত্য-সংস্কৃতি', 'ক্ষুদ্র নৃগোষ্ঠী']
        for target in target_categories:
            found_articles = [art for art in all_articles if art.get('category') == target]
            print(f"\nFound {len(found_articles)} articles for '{target}'")
            if found_articles:
                for i, art in enumerate(found_articles[:2]):
                    print(f"  {i+1}. {art.get('title', '')[:50]}... (source: {art.get('source', '')})")
                    
    except Exception as e:
        print(f"Error testing main scraper: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all debug tests"""
    print("🔍 Starting category detection debugging...\n")
    
    debug_category_detection()
    debug_main_scraper()
    
    print("\n✅ Debug completed!")

if __name__ == "__main__":
    main()
