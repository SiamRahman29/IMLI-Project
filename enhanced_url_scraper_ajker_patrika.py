import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random
import re
from urllib.parse import urljoin, urlparse

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
                time.sleep(random.uniform(1, 3))
    
    return None

def extract_sub_routes_from_category(category_url, max_sub_routes=20):
    """
    Extract sub-route URLs from a category page
    
    Args:
        category_url (str): The category URL (e.g., https://www.ajkerpatrika.com/trivia)
        max_sub_routes (int): Maximum number of sub-routes to extract
    
    Returns:
        list: List of sub-route URLs found on the category page
    """
    print(f"🔍 Extracting sub-routes from: {category_url}")
    
    response = robust_request(category_url)
    if not response:
        print(f"❌ Failed to fetch category page: {category_url}")
        return []
    
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Parse the base URL
    parsed_url = urlparse(category_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    sub_routes = []
    seen_urls = set()
    
    # Different selectors to find article links
    selectors = [
        "a[href*='/news/']",
        "a[href*='/details/']", 
        "a[href*='/story/']",
        "a[href*='/article/']",
        "a[href*='/post/']",
        ".news-title a",
        ".headline a",
        ".story-headline a",
        ".title a",
        "h1 a",
        "h2 a", 
        "h3 a",
        "h4 a",
        ".news-item a",
        ".article-link",
        ".content-title a"
    ]
    
    print(f"🔎 Searching with {len(selectors)} different selectors...")
    
    for selector in selectors:
        links = soup.select(selector)
        print(f"   {selector}: Found {len(links)} links")
        
        for link in links:
            href = link.get('href')
            if not href:
                continue
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = base_url + href
            elif not href.startswith('http'):
                href = urljoin(category_url, href)
            
            # Filter for valid article URLs and avoid duplicates
            if (href not in seen_urls and 
                'ajkerpatrika.com' in href and
                any(pattern in href for pattern in ['/news/', '/details/', '/story/', '/article/', '/post/']) and
                not any(skip in href for skip in ['#', 'javascript:', 'mailto:', '.pdf', '.jpg', '.png'])):
                
                sub_routes.append(href)
                seen_urls.add(href)
                
                if len(sub_routes) >= max_sub_routes:
                    break
        
        if len(sub_routes) >= max_sub_routes:
            break
    
    # Also try finding links by pattern matching
    all_links = soup.find_all('a', href=True)
    print(f"🔎 Pattern matching on {len(all_links)} total links...")
    
    for link in all_links:
        if len(sub_routes) >= max_sub_routes:
            break
            
        href = link.get('href')
        if not href:
            continue
            
        # Convert relative URLs to absolute
        if href.startswith('/'):
            href = base_url + href
        elif not href.startswith('http'):
            href = urljoin(category_url, href)
        
        # Pattern for Ajker Patrika article URLs (ending with numeric ID or containing specific patterns)
        if (href not in seen_urls and 
            'ajkerpatrika.com' in href and 
            (re.search(r'/[a-z0-9]{8,}/?$', href) or  # Alphanumeric IDs
             re.search(r'/\d{4,}/?$', href) or        # Numeric IDs  
             re.search(r'/(news|details|story|article|post)/', href)) and
            not any(skip in href for skip in ['#', 'javascript:', 'mailto:', '.pdf', '.jpg', '.png', '/tag/', '/author/'])):
            
            sub_routes.append(href)
            seen_urls.add(href)
    
    print(f"✅ Extracted {len(sub_routes)} sub-routes from {category_url}")
    return sub_routes[:max_sub_routes]

def scrape_article_from_url(article_url):
    """
    Scrape a single article from its URL
    
    Args:
        article_url (str): The article URL to scrape
    
    Returns:
        dict: Article data or None if scraping failed
    """
    response = robust_request(article_url)
    if not response:
        return None
    
    try:
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract headings with comprehensive selectors
        headings = []
        heading_selectors = ['h1', 'h2', 'h3', '.title', '.headline', '.news-title', '.article-title', '.story-title']
        
        for selector in heading_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and text not in headings and len(text) > 5:  # Avoid very short headings
                    headings.append(text)
        
        # Extract content paragraphs for better context
        content_paragraphs = []
        for p_tag in soup.find_all('p'):
            text = p_tag.get_text().strip()
            if text and len(text) > 20:  # Filter out very short paragraphs
                content_paragraphs.append(text)
        
        # Take first 3 paragraphs for context
        content_text = ' '.join(content_paragraphs[:3]) if content_paragraphs else ""
        
        if headings:
            return {
                "title": headings[0],
                "heading": ' '.join(headings),
                "content": content_text,
                "url": article_url,
                "published_date": datetime.now().date(),
                "source": "ajker_patrika"
            }
        else:
            print(f"⚠️ No headings found for: {article_url}")
            return None
            
    except Exception as e:
        print(f"❌ Error scraping article {article_url}: {e}")
        return None

def scrape_ajker_patrika_enhanced(category_urls, max_sub_routes_per_category=15, max_articles_per_sub_route=1):
    """
    Enhanced scraper that extracts sub-routes from category URLs and scrapes articles
    
    Args:
        category_urls (list): List of category URLs (e.g., ['https://www.ajkerpatrika.com/trivia'])
        max_sub_routes_per_category (int): Maximum sub-routes to extract per category
        max_articles_per_sub_route (int): Maximum articles to scrape per sub-route (usually 1)
    
    Returns:
        dict: Results with extracted articles and statistics
    """
    all_articles = []
    all_sub_routes = []
    category_stats = {}
    
    print(f"🚀 Starting enhanced Ajker Patrika scraping for {len(category_urls)} categories...")
    
    for i, category_url in enumerate(category_urls, 1):
        print(f"\n📂 [{i}/{len(category_urls)}] Processing category: {category_url}")
        
        # Extract sub-routes from this category
        sub_routes = extract_sub_routes_from_category(category_url, max_sub_routes_per_category)
        
        if not sub_routes:
            print(f"❌ No sub-routes found for {category_url}")
            category_stats[category_url] = {"sub_routes": 0, "articles": 0}
            continue
        
        all_sub_routes.extend(sub_routes)
        category_articles = []
        
        print(f"📄 Scraping {len(sub_routes)} sub-routes from {category_url}...")
        
        # Scrape articles from each sub-route
        for j, sub_route in enumerate(sub_routes, 1):
            print(f"   📰 [{j}/{len(sub_routes)}] Scraping: {sub_route}")
            
            article = scrape_article_from_url(sub_route)
            if article:
                # Add category info
                article['category'] = category_url.split('/')[-1]  # Extract category name from URL
                category_articles.append(article)
                all_articles.append(article)
                print(f"   ✅ Article extracted: {article['title'][:50]}...")
            else:
                print(f"   ❌ Failed to extract article from: {sub_route}")
            
            # Add small delay between articles
            time.sleep(random.uniform(0.5, 1.0))
        
        category_stats[category_url] = {
            "sub_routes": len(sub_routes),
            "articles": len(category_articles)
        }
        
        print(f"✅ Category {category_url}: {len(category_articles)} articles from {len(sub_routes)} sub-routes")
        
        # Add delay between categories
        if i < len(category_urls):
            print(f"⏳ Waiting 2-4 seconds before next category...")
            time.sleep(random.uniform(2, 4))
    
    # Summary
    print(f"\n🎉 Enhanced scraping completed!")
    print(f"📊 Total categories processed: {len(category_urls)}")
    print(f"📊 Total sub-routes found: {len(all_sub_routes)}")
    print(f"📊 Total articles scraped: {len(all_articles)}")
    
    print(f"\n📈 Category-wise breakdown:")
    for category, stats in category_stats.items():
        print(f"   {category}: {stats['articles']} articles from {stats['sub_routes']} sub-routes")
    
    return {
        "articles": all_articles,
        "sub_routes": all_sub_routes,
        "category_stats": category_stats,
        "summary": {
            "total_categories": len(category_urls),
            "total_sub_routes": len(all_sub_routes),
            "total_articles": len(all_articles),
            "success_rate": f"{len(all_articles)/len(all_sub_routes)*100:.1f}%" if all_sub_routes else "0%"
        }
    }

# Example usage
if __name__ == "__main__":
    # Test with your provided URL
    test_category_urls = [
        "https://www.ajkerpatrika.com/trivia",
        "https://www.ajkerpatrika.com/sports",
        "https://www.ajkerpatrika.com/bangladesh",
        "https://www.ajkerpatrika.com/international",
        "https://www.ajkerpatrika.com/entertainment"
    ]
    
    print("🧪 Testing enhanced Ajker Patrika scraper...")
    results = scrape_ajker_patrika_enhanced(test_category_urls, max_sub_routes_per_category=10)
    
    # Show some sample articles
    print(f"\n📋 Sample articles:")
    for i, article in enumerate(results["articles"][:3], 1):
        print(f"{i}. {article['title']}")
        print(f"   URL: {article['url']}")
        print(f"   Category: {article.get('category', 'Unknown')}")
        print()
