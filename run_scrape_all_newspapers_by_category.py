from app.routes.helpers import scrape_bengali_news, categorize_articles
import json

if __name__ == "__main__":
    articles = scrape_bengali_news()
    # Add category detection to each article
    categorized_articles = categorize_articles(articles)
    # User-defined 12 Bengali news categories
    user_categories = [
        'জাতীয়', 'অর্থনীতি', 'রাজনীতি', 'লাইফস্টাইল', 'বিনোদন', 'খেলাধুলা',
        'ধর্ম', 'চাকরি', 'শিক্ষা', 'স্বাস্থ্য', 'মতামত', 'বিজ্ঞান'
    ]
    # Organize articles by user-defined categories
    category_dict = {cat: [] for cat in user_categories}
    category_dict['অন্যান্য'] = []  # For uncategorized/other
    for article in categorized_articles:
        cat = article.get('category', 'অন্যান্য')
        if cat in user_categories:
            category_dict[cat].append(article)
        else:
            category_dict['অন্যান্য'].append(article)
    # Save to JSON file
    def default_serializer(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return str(obj)
    with open("all_newspapers_by_category.json", "w", encoding="utf-8") as f:
        json.dump(category_dict, f, ensure_ascii=False, indent=2, default=default_serializer)
    print("Scraped articles saved to all_newspapers_by_category.json (grouped by user-defined categories)")
