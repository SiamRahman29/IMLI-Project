# Simple script to run scrape_ajker_patrika and print the output
from app.routes.helpers import scrape_ajker_patrika
import json

if __name__ == "__main__":
    articles = scrape_ajker_patrika()
    print(f"Total articles scraped: {len(articles)}\n")
    for i, article in enumerate(articles, 1):
        print(f"[{i}] Title: {article.get('title')}")
        print(f"    URL: {article.get('url')}")
        print(f"    Heading: {article.get('heading')[:120]}{'...' if len(article.get('heading','')) > 120 else ''}")
        print()
    # Save output to JSON file
    def default_serializer(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return str(obj)
    with open("ajker_patrika_scraped.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2, default=default_serializer)
    print("Scraped articles saved to ajker_patrika_scraped.json")
