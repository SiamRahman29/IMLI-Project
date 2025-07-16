import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random

def robust_request(url, retries=3, timeout=10):
    """Robust HTTP request with retries"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return response
            else:
                print(f"HTTP {response.status_code} for {url}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url} (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(random.uniform(1, 3))  # Random delay between retries
    
    return None

def scrape_ajker_patrika_from_urls(urls):
    """
    Scrape articles from specific Ajker Patrika URLs
    
    Args:
        urls (list): List of Ajker Patrika article URLs to scrape
    
    Returns:
        list: List of scraped articles with title, heading, url, published_date, source
    """
    articles = []
    seen_urls = set()
    
    print(f"🚀 Starting to scrape {len(urls)} Ajker Patrika URLs...")
    
    for i, url in enumerate(urls, 1):
        # Skip if URL already processed
        if url in seen_urls:
            print(f"⚠️ [{i}/{len(urls)}] Skipping duplicate URL: {url}")
            continue
        
        seen_urls.add(url)
        
        print(f"📄 [{i}/{len(urls)}] Scraping: {url}")
        
        # Make request to the article URL
        article_res = robust_request(url)
        if not article_res:
            print(f"❌ [{i}/{len(urls)}] Failed to fetch: {url}")
            continue
        
        try:
            article_soup = BeautifulSoup(article_res.text, "html.parser")
            
            # Extract headings - prioritize h1, then h2 if no h1 found
            headings = [tag.text.strip() for tag in article_soup.find_all('h1') if tag.text.strip()]
            
            # If no h1 found, try h2
            if not headings:
                headings = [tag.text.strip() for tag in article_soup.find_all('h2') if tag.text.strip()]
            
            # Join all headings
            heading_text = ' '.join(headings)
            
            # Extract article content/body text (optional, for better context)
            content_paragraphs = []
            for p_tag in article_soup.find_all('p'):
                text = p_tag.get_text().strip()
                if text and len(text) > 20:  # Filter out very short paragraphs
                    content_paragraphs.append(text)
            
            # Take first 3 paragraphs for context
            content_text = ' '.join(content_paragraphs[:3]) if content_paragraphs else ""
            
            print(f"✅ [{i}/{len(urls)}] Success - Title: {headings[0] if headings else 'No title'}")
            print(f"    📝 Headings found: {len(headings)}")
            print(f"    📄 Content paragraphs: {len(content_paragraphs)}")
            
            # Create article object
            article = {
                "title": headings[0] if headings else "",
                "heading": heading_text,
                "content": content_text,  # Added content for better LLM analysis
                "url": url,
                "published_date": datetime.now().date(),
                "source": "ajker_patrika"
            }
            
            articles.append(article)
            
            # Add small delay between requests to be respectful
            time.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            print(f"❌ [{i}/{len(urls)}] Error scraping article: {e}")
            continue
    
    print(f"🎉 Successfully scraped {len(articles)} articles from {len(urls)} URLs")
    return articles

def scrape_ajker_patrika_categories_from_urls(category_urls_dict):
    """
    Scrape articles from category-wise URLs
    
    Args:
        category_urls_dict (dict): Dictionary with category names as keys and lists of URLs as values
                                 Example: {
                                     'জাতীয়': ['url1', 'url2', ...],
                                     'রাজনীতি': ['url3', 'url4', ...],
                                     ...
                                 }
    
    Returns:
        dict: Dictionary with category names as keys and lists of articles as values
    """
    category_articles = {}
    total_urls = sum(len(urls) for urls in category_urls_dict.values())
    processed_urls = 0
    
    print(f"🚀 Starting category-wise scraping for {len(category_urls_dict)} categories, {total_urls} total URLs...")
    
    for category, urls in category_urls_dict.items():
        print(f"\n📂 Processing category: {category} ({len(urls)} URLs)")
        
        # Scrape articles for this category
        articles = scrape_ajker_patrika_from_urls(urls)
        
        # Add category info to each article
        for article in articles:
            article['category'] = category
        
        category_articles[category] = articles
        processed_urls += len(urls)
        
        print(f"✅ Category {category}: {len(articles)} articles scraped")
        print(f"📊 Progress: {processed_urls}/{total_urls} URLs processed")
        
        # Add delay between categories
        if category != list(category_urls_dict.keys())[-1]:  # Not the last category
            time.sleep(random.uniform(2, 4))
    
    total_articles = sum(len(articles) for articles in category_articles.values())
    print(f"\n🎉 Category-wise scraping completed!")
    print(f"📊 Total articles scraped: {total_articles}")
    print(f"📂 Categories processed: {len(category_articles)}")
    
    return category_articles

# Example usage
if __name__ == "__main__":
    # Example: Single URL list
    sample_urls = [
        "https://www.ajkerpatrika.com/news/details/123456",
        "https://www.ajkerpatrika.com/news/details/123457",
        # Add your URLs here
    ]
    
    # Scrape from URL list
    articles = scrape_ajker_patrika_from_urls(sample_urls)
    print(f"Scraped {len(articles)} articles")
    
    # Example: Category-wise URLs
    category_urls = {
        'জাতীয়': [
            "https://www.ajkerpatrika.com/news/details/123456",
            "https://www.ajkerpatrika.com/news/details/123457",
        ],
        'রাজনীতি': [
            "https://www.ajkerpatrika.com/news/details/123458",
            "https://www.ajkerpatrika.com/news/details/123459",
        ]
    }
    
    # Scrape category-wise
    category_articles = scrape_ajker_patrika_categories_from_urls(category_urls)
    print(f"Scraped from {len(category_articles)} categories")
