#!/usr/bin/env python3
"""
Reddit Subreddit Scrape and Save Only
Scrapes all subreddits using RedditDataScrapper and saves the raw scrapped posts to a timestamped JSON file.
No LLM analysis is performed.
"""
import os
import json
from datetime import datetime
from app.services.reddit_data_scrapping import RedditDataScrapper

def main():
    print("\n🚀 Starting Reddit subreddit scrape (no LLM)...")
    scraper = RedditDataScrapper()

    # Scrape all subreddits (default: 10 posts per subreddit)
    print("\n📝 Scraping Reddit subreddits...")
    posts = scraper.scrape_all_subreddits(posts_per_subreddit=10)

    # Remove AlJazeera bot warning from comments for r/AlJazeera
    warning_text = "# r/AlJazeera is an unofficial subreddit and has no affiliation with the Al Jazeera Media Network."
    for post in posts:
        if post.get('subreddit', '').lower() == 'aljazeera' and 'comments' in post:
            post['comments'] = [c for c in post['comments'] if not c.strip().startswith(warning_text)]

    # Save the scrapped posts to a timestamped JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"reddit_scraped_posts_{timestamp}.json"
    output_path = os.path.join(os.getcwd(), output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Scraped posts saved to: {output_path}\n")

if __name__ == "__main__":
    main()
