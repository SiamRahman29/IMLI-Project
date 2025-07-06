from app.routes.helpers import scrape_prothom_alo
import json

if __name__ == "__main__":
    articles = scrape_prothom_alo()
    print(f"Total articles scraped: {len(articles)}\n")
    for i, article in enumerate(articles, 1):
        print(f"[{i}] Title: {article.get('title')}")
        print(f"    URL: {article.get('url')}")
        print(f"    Heading: {article.get('heading')[:120]}{'...' if len(article.get('heading','')) > 120 else ''}")
        print()
    def default_serializer(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return str(obj)
    with open("prothom_alo_scraped.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2, default=default_serializer)
    print("Scraped articles saved to prothom_alo_scraped.json")
