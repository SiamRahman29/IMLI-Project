"""
Social Media Scraping Service for Bengali Content
Implements scraping from Reddit, Facebook public pages and Twitter-like platforms
"""

import requests
import re
import time
from datetime import datetime, date
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import feedparser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import Reddit scraper - use preferred data scrapper
try:
    from .reddit_data_scrapping import RedditDataScrapper
    REDDIT_SCRAPER_TYPE = "data_scrapper"
except ImportError:
    from .reddit_scraper import RedditScraper
    REDDIT_SCRAPER_TYPE = "fallback"


class SocialMediaScraper:
    ENABLE_SOCIAL_MEDIA_SCRAPING = True  # Enable for Reddit integration
    ENABLE_REDDIT_SCRAPING = True  # Reddit is enabled

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'bn,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Initialize Reddit scraper - use preferred implementation
        if self.ENABLE_REDDIT_SCRAPING:
            if REDDIT_SCRAPER_TYPE == "data_scrapper":
                self.reddit_scraper = RedditDataScrapper()
                self.reddit_scraper_type = "data_scrapper"
            else:
                self.reddit_scraper = RedditScraper()
                self.reddit_scraper_type = "fallback"
        else:
            self.reddit_scraper = None
            self.reddit_scraper_type = None
        
    def setup_selenium_driver(self) -> webdriver.Chrome:
        """Setup Selenium WebDriver for JavaScript-heavy pages"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(50)  # Set implicit wait timeout to 50 seconds
            return driver
        except Exception as e:
            print(f"Failed to setup Chrome driver: {e}")
            return None

    def get_facebook_page_ids(self):
        """Return a list of Facebook public page usernames or IDs to fetch via Graph API"""
        return [
            # 'shortstoriessbd',
            # 'thepost360',
            # 'bnpbd.org',
            # '1NationalCitizenParty',
            # 'gowtamkshuvo.page',
            # 'Dr.Asifnazrul',
            # 'Ishraque.ForMayor',
            # 'ChiefAdviserGOB',
            # 'PinakiRightsActivist',
            # 'pricilanewyork',
        ]

    def fetch_facebook_page_posts(self, page_id, access_token, limit=10):
        # Commented out: Facebook Graph API fetching
        # url = f"https://graph.facebook.com/v23.0/{page_id}/posts"
        # params = {
        #     "access_token": access_token,
        #     "app_id": "1245613587284998",  # Explicitly provide your App ID
        #     "fields": "message,created_time,id,permalink_url",
        #     "limit": limit
        # }
        # try:
        #     response = requests.get(url, params=params)
        #     data = response.json()
        #     posts = []
        #     for post in data.get("data", []):
        #         if 'message' in post:
        #             posts.append({
        #                 'content': post['message'],
        #                 'source': 'facebook',
        #                 'page': page_id,
        #                 'scraped_date': post.get('created_time', ''),
        #                 'platform': 'social_media',
        #                 'url': post.get('permalink_url', '')
        #             })
        #     if 'error' in data:
        #         print(f"[ERROR] Facebook Graph API error for {page_id}: {data['error']}")
        #     return posts
        # except Exception as e:
        #     print(f"[ERROR] Facebook Graph API error for {page_id}: {e}")
        #     return []
        return []

    def scrape_reddit_content(self, hours_back: int = 24) -> List[Dict]:
        """
        Scrape Reddit content from Bangladesh-related subreddits
        
        Args:
            hours_back: Hours to look back for recent content
            
        Returns:
            List of Reddit content items formatted for social media analysis
        """
        if not self.ENABLE_REDDIT_SCRAPING or not self.reddit_scraper:
            print("[INFO] Reddit scraping is disabled")
            return []
        
        try:
            print(f"[INFO] Scraping Reddit content from last {hours_back} hours...")
            
            # Get Bangladesh-related content based on scraper type
            if self.reddit_scraper_type == "data_scrapper":
                # Use RedditDataScrapper
                result = self.reddit_scraper.run_comprehensive_analysis(posts_per_subreddit=20)
                reddit_content = []
                
                # Convert from analysis result to content format
                for subreddit_data in result.get('subreddit_responses', []):
                    for post in subreddit_data.get('posts', []):
                        content_item = {
                            'id': post.get('id'),
                            'title': post.get('title', ''),
                            'content': post.get('content', ''),
                            'subreddit': post.get('subreddit'),
                            'score': post.get('score', 0),
                            'num_comments': post.get('num_comments', 0),
                            'engagement_score': post.get('score', 0) + (post.get('num_comments', 0) * 2),
                            'permalink': post.get('url', ''),
                            'timestamp': post.get('created_utc'),
                            'author': post.get('author'),
                            'comments': post.get('comments', [])
                        }
                        reddit_content.append(content_item)
            else:
                # Use fallback RedditScraper
                reddit_content = self.reddit_scraper.scrape_bangladesh_content(
                    hours_back=hours_back,
                    posts_per_subreddit=20
                )
            
            # Format for social media analysis
            formatted_content = []
            for item in reddit_content:
                # Combine title, content, and top comments for analysis
                combined_text = f"{item['title']} {item['content']}"
                if item.get('comments'):
                    # Add top 3 comments
                    top_comments = " ".join(item['comments'][:3])
                    combined_text += f" {top_comments}"
                
                formatted_item = {
                    'content': combined_text,
                    'source': 'reddit',
                    'platform': 'social_media',
                    'subreddit': item['subreddit'],
                    'score': item['score'],
                    'comments_count': item['num_comments'],
                    'engagement_score': item['engagement_score'],
                    'url': item['permalink'],
                    'scraped_date': item['timestamp'],
                    'post_id': item['id'],
                    'author': item['author'],
                    'flair': item.get('flair'),
                    'original_data': item  # Keep original for reference
                }
                
                formatted_content.append(formatted_item)
            
            print(f"[SUCCESS] Retrieved {len(formatted_content)} Reddit items")
            return formatted_content
            
        except Exception as e:
            print(f"[ERROR] Reddit scraping failed: {e}")
            return []

    def scrape_facebook_public_pages(self) -> List[Dict]:
        """
        Scrape Bengali Facebook public pages using the Graph API
        """
        # Disabled: Facebook scraping
        print("[INFO] Facebook scraping is disabled")
        return []

    def scrape_youtube_comments(self) -> List[Dict]:
        """
        Scrape comments from popular Bengali YouTube channels
        """
        # Disabled: YouTube scraping
        print("[INFO] YouTube scraping is disabled")
        return []

    def scrape_twitter_alternatives(self) -> List[Dict]:
        """
        Scrape Twitter alternatives for Bengali content
        """
        # Disabled: Twitter-alternative scraping
        print("[INFO] Twitter alternatives scraping is disabled")
        return []

    def _contains_bengali_text(self, text: str) -> bool:
        """Check if text contains Bengali characters"""
        bengali_pattern = r'[\u0980-\u09FF]'
        return bool(re.search(bengali_pattern, text))

    def get_all_social_media_content(self) -> List[Dict]:
        """
        Get content from all social media sources (currently Reddit only)
        """
        if not self.ENABLE_SOCIAL_MEDIA_SCRAPING:
            print("[INFO] Social media scraping is disabled")
            return []
        
        all_content = []
        
        # Reddit content
        if self.ENABLE_REDDIT_SCRAPING:
            reddit_content = self.scrape_reddit_content()
            all_content.extend(reddit_content)
            print(f"[INFO] Added {len(reddit_content)} Reddit items")
        
        # Future: Add other platforms here
        # facebook_content = self.scrape_facebook_public_pages()
        # all_content.extend(facebook_content)
        
        print(f"[INFO] Total social media content: {len(all_content)} items")
        return all_content


class BengaliSocialMediaTrends:
    """
    Analyze trends from Bengali social media content
    """
    
    def __init__(self):
        self.scraper = SocialMediaScraper()
        
    def get_trending_topics(self) -> List[Dict]:
        """
        Get trending topics from social media
        """
        # Get social media content
        content = self.scraper.get_all_social_media_content()
        
        # Process and analyze trends
        #TODO This would integrate with your existing TrendingAnalyzer
        
        return content

# Example usage functions
def scrape_social_media_content() -> List[Dict]:
    """
    Main function to scrape social media content (Reddit)
    """
    scraper = SocialMediaScraper()
    return scraper.get_all_social_media_content()

def get_social_media_trends() -> List[Dict]:
    """
    Get trending analysis from social media
    """
    trends_analyzer = BengaliSocialMediaTrends()
    return trends_analyzer.get_trending_topics()

def get_reddit_trending_topics() -> List[Dict]:
    """
    Get trending topics specifically from Reddit
    """
    scraper = SocialMediaScraper()
    if scraper.reddit_scraper:
        content = scraper.scrape_reddit_content()
        return scraper.reddit_scraper.get_trending_topics(
            [item['original_data'] for item in content if 'original_data' in item]
        )
    return []

def print_scraped_posts_pretty(posts: List[Dict]):

    if not posts:
        print("No posts found.")
        return
    for idx, post in enumerate(posts, 1):
        print(f"{'='*60}")
        print(f"Post #{idx}")
        print(f"Source     : {post.get('source', 'N/A')}")
        print(f"Platform   : {post.get('platform', 'N/A')}")
        if 'page' in post:
            print(f"Page       : {post.get('page')}")
        if 'video_url' in post:
            print(f"Video URL  : {post.get('video_url')}")
        print(f"Date       : {post.get('scraped_date', 'N/A')}")
        print(f"Content    :\n{post.get('content', '').strip()}")
        print(f"{'='*60}\n")

def demo_print_scraped_posts():
    posts = scrape_social_media_content()
    print_scraped_posts_pretty(posts)
