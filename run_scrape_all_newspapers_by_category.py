from app.services.filtered_newspaper_service import FilteredNewspaperScraper
import json

if __name__ == "__main__":
    # User-defined 12 Bengali news categories
    user_categories = [
        'জাতীয়', 'অর্থনীতি', 'রাজনীতি', 'লাইফস্টাইল', 'বিনোদন', 'খেলাধুলা',
        'ধর্ম', 'চাকরি', 'শিক্ষা', 'স্বাস্থ্য', 'মতামত', 'বিজ্ঞান', 'আন্তর্জাতিক'
    ]
    # Use the main pipeline's categorization logic
    scraper = FilteredNewspaperScraper(user_categories)
    results = scraper.scrape_all_newspapers()
    # Organize articles by user-defined categories
    category_dict = {cat: [] for cat in user_categories}
    category_dict['অন্যান্য'] = []  # For uncategorized/other
    for category, articles in results['category_wise_articles'].items():
        if category in user_categories:
            category_dict[category].extend(articles)
        else:
            category_dict['অন্যান্য'].extend(articles)
    # Save to JSON file
    def default_serializer(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return str(obj)
    with open("all_newspapers_by_category.json", "w", encoding="utf-8") as f:
        json.dump(category_dict, f, ensure_ascii=False, indent=2, default=default_serializer)
    print("Scraped articles saved to all_newspapers_by_category.json (grouped by user-defined categories)")
