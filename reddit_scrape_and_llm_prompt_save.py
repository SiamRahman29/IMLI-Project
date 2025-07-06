#!/usr/bin/env python3
"""
Reddit Data Scrape and LLM Prompt Saver
Scrapes Reddit data using the pipeline's RedditDataScrapper and saves the full LLM prompt (with all context) to a timestamped JSON file.
"""
import os
import json
from datetime import datetime
from app.services.reddit_data_scrapping import RedditDataScrapper

def main():
    print("\n🚀 Starting Reddit data scrape and LLM prompt save...")
    # Initialize the RedditDataScrapper
    scraper = RedditDataScrapper()

    # Scrape all subreddits and run LLM analysis (default: 20 posts per subreddit)
    print("\n📝 Scraping Reddit and running LLM analysis...")
    results = scraper.run_comprehensive_analysis(posts_per_subreddit=20)

    # Save the full LLM prompt and results to a timestamped JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"reddit_llm_prompt_{timestamp}.json"
    output_path = os.path.join(os.getcwd(), output_filename)

    # Save the entire results dict (contains LLM prompt, responses, metadata)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ LLM prompt and Reddit analysis saved to: {output_path}\n")

if __name__ == "__main__":
    main()
