"""
Social Media Scraping Service for Bengali Content
Implements scraping from Facebook public pages and Twitter-like platforms
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


class SocialMediaScraper:
    ENABLE_SOCIAL_MEDIA_SCRAPING = True  # Set to True to enable scraping

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'bn,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
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

    def get_facebook_sources(self):
        """Return a modular list of Facebook public pages, groups, and individuals to scrape"""
        return [
            # Only add unique, non-news-organization pages/groups if needed
            # Example Public Groups (add more as needed)
            'https://www.facebook.com/groups/ProthomAloReaders',
            'https://www.facebook.com/groups/bdnews24group',
            # Example Individuals (public profiles)
            # 'https://www.facebook.com/publicprofileid',
        ]

    def scrape_facebook_public_pages(self) -> List[Dict]:
        """
        Scrape Bengali Facebook public groups and individuals (modular, no news orgs)
        """
        posts = []
        public_pages = self.get_facebook_sources()
        if not public_pages:
            return posts
        driver = self.setup_selenium_driver()
        if not driver:
            return posts
        try:
            for page_url in public_pages:
                print(f"Scraping Facebook page/group: {page_url}")
                try:
                    driver.get(page_url)
                    time.sleep(3)
                    for _ in range(3):
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                    post_elements = driver.find_elements(By.CSS_SELECTOR, '[data-pagelet="FeedUnit_0"], [role="article"]')
                    for post_element in post_elements[:10]:
                        try:
                            text_content = post_element.text
                            if self._contains_bengali_text(text_content):
                                posts.append({
                                    'content': text_content,
                                    'source': 'facebook',
                                    'page': page_url.split('/')[-1],
                                    'scraped_date': datetime.now().date(),
                                    'platform': 'social_media',
                                    'url': page_url
                                })
                        except Exception as e:
                            print(f"Error extracting post: {e}")
                            continue
                except Exception as e:
                    print(f"Error scraping {page_url}: {e}")
                    continue
        finally:
            driver.quit()
        return posts

    def scrape_youtube_comments(self) -> List[Dict]:
        """
        Scrape comments from popular Bengali YouTube channels
        """
        comments = []
        
        # Popular Bengali YouTube channels
        channels = [
            'UCKREJp-MrNaORDXDQhw3hNw',  # Prothom Alo
            'UC-LG7HdKCmvvDJOQmOhzJOQ',  # Channel i
            'UCrGhoBcQRl6jzrfh2wCKV_Q',  # Independent TV
        ]
        # TODO: BeautifulSoup - web app scraping
        # FIXME : Selenium - web app scraping
        # BUG
        driver = self.setup_selenium_driver()
        if not driver:
            return comments
            
        try:
            for channel_id in channels:
                # Get recent videos from channel
                videos_url = f"https://www.youtube.com/channel/{channel_id}/videos"
                
                try:
                    driver.get(videos_url)
                    time.sleep(3)
                    
                    video_links = driver.find_elements(By.CSS_SELECTOR, '#video-title')[:5]
                    
                    for video_link in video_links:
                        try:
                            video_url = video_link.get_attribute('href')
                            if video_url:
                                video_comments = self._scrape_video_comments(driver, video_url)
                                comments.extend(video_comments)
                        except Exception as e:
                            print(f"Error getting video comments: {e}")
                            continue
                            
                except Exception as e:
                    print(f"Error scraping channel {channel_id}: {e}")
                    continue
                    
        finally:
            driver.quit()
            
        return comments

    def _scrape_video_comments(self, driver: webdriver.Chrome, video_url: str) -> List[Dict]:
        comments = []
        
        try:
            driver.get(video_url)
            time.sleep(3)
            
            # Scroll to load comments
            driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(2)
            
            # Find comment elements
            comment_elements = driver.find_elements(By.CSS_SELECTOR, '#content-text')[:20]
            
            for comment_element in comment_elements:
                try:
                    comment_text = comment_element.text
                    
                    if self._contains_bengali_text(comment_text) and len(comment_text) > 10:
                        comments.append({
                            'content': comment_text,
                            'source': 'youtube',
                            'video_url': video_url,
                            'scraped_date': datetime.now().date(),
                            'platform': 'social_media'
                        })
                        
                except Exception as e:
                    print(f"Error extracting comment: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error scraping video comments: {e}")
            
        return comments

    def scrape_twitter_alternatives(self) -> List[Dict]:
        """
        Scrape Twitter alternatives for Bengali content
        """
        posts = []
        
        # Note: This would require specific implementation based on available platforms
        #TODO For now, implementing a placeholder structure
        
        return posts

    def _contains_bengali_text(self, text: str) -> bool:
        """Check if text contains Bengali characters"""
        bengali_pattern = r'[\u0980-\u09FF]'
        return bool(re.search(bengali_pattern, text))

    def get_all_social_media_content(self) -> List[Dict]:
        """
        Get content from all social media sources
        """
        if not self.ENABLE_SOCIAL_MEDIA_SCRAPING:
            print("[INFO] Social media scraping is currently disabled. Set ENABLE_SOCIAL_MEDIA_SCRAPING=True to enable.")
            return []
        # TODO: Implement actual scraping logic here
        # Example: return self.scrape_facebook_public_pages() + self.scrape_youtube_comments() + self.scrape_twitter_alternatives()
        return []


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
    Main function to scrape social media content
    """
    scraper = SocialMediaScraper()
    return scraper.get_all_social_media_content()

def get_social_media_trends() -> List[Dict]:
    """
    Get trending analysis from social media
    """
    trends_analyzer = BengaliSocialMediaTrends()
    return trends_analyzer.get_trending_topics()

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
