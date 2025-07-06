import json
from app.routes.helpers import scrape_noya_diganta

if __name__ == "__main__":
    articles = scrape_noya_diganta()
    print(f"Scraped {len(articles)} articles from Noya Diganta.")
    with open("noya_diganta_scraped.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print("Saved results to noya_diganta_scraped.json")
