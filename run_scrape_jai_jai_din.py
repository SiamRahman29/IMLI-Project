import json
from app.routes.helpers import scrape_jai_jai_din

if __name__ == "__main__":
    articles = scrape_jai_jai_din()
    print(f"Scraped {len(articles)} articles from Jai Jai Din.")
    with open("jai_jai_din_scraped.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print("Saved results to jai_jai_din_scraped.json")
