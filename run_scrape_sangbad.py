import json
from app.routes.helpers import scrape_sangbad

if __name__ == "__main__":
    articles = scrape_sangbad()
    print(f"Scraped {len(articles)} articles from Sangbad.")
    with open("sangbad_scraped.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print("Saved results to sangbad_scraped.json")
