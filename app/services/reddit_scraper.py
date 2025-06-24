#!/usr/bin/env python3
"""
Reddit Scraper for Bangladesh-related content
Collects trending posts, comments, and discussions from Bangladeshi subreddits
"""

import os
import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
import praw  # Reddit API wrapper

# Load environment variables
load_dotenv()

@dataclass
class RedditPost:
    """Data structure for Reddit posts"""
    id: str
    title: str
    content: str
    subreddit: str
    author: str
    score: int
    num_comments: int
    created_utc: float
    url: str
    permalink: str
    flair: Optional[str] = None
    is_self: bool = True
    comments: List[str] = None

class RedditScraper:
    """
    Reddit scraper for Bangladesh-related content
    Uses Reddit API to collect trending posts and comments
    """
    
    def __init__(self):
        self.logger = self._setup_logging()
        
        # Get Reddit API credentials from environment variables
        self.client_id = os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = os.getenv('REDDIT_USER_AGENT', 'BangladeshTrendingAnalyzer/1.0 (Educational Research Project)')
        
        if not self.client_id or not self.client_secret:
            self.logger.error("Reddit API credentials not found in environment variables!")
            self.logger.error("Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env file")
            raise ValueError("Reddit API credentials missing")
        
        # Initialize Reddit API client
        try:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            self.logger.info("Reddit API client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Reddit API client: {e}")
            raise
        
        # Fallback session for direct API calls if needed
        self.base_url = "https://www.reddit.com"
        self.session = self._create_session()
        
        # Bangladesh-related subreddits
        self.bangladesh_subreddits = [
            'bangladesh',
            'bengali',
            'dhaka',
            'chittagong',
            'sylhet',
            'bangladeshpolitics',
            'bangladesheconomy',
            'dhakauni',
            'buet',
            'du',
            'nsu',
            'ulab'
        ]
        
        # Headers for fallback requests
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for Reddit scraper"""
        logger = logging.getLogger('reddit_scraper')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def get_subreddit_posts(self, subreddit: str, sort: str = 'hot', 
                           time_filter: str = 'day', limit: int = 25) -> List[RedditPost]:
        """
        Get posts from a specific subreddit
        
        Args:
            subreddit: Subreddit name
            sort: Sort method ('hot', 'new', 'top', 'rising')
            time_filter: Time filter for 'top' sort ('hour', 'day', 'week', 'month', 'year', 'all')
            limit: Number of posts to retrieve (max 100)
        
        Returns:
            List of RedditPost objects
        """
        posts = []
        
        try:
            # Construct URL
            if sort == 'top':
                url = f"{self.base_url}/r/{subreddit}/{sort}.json?t={time_filter}&limit={limit}"
            else:
                url = f"{self.base_url}/r/{subreddit}/{sort}.json?limit={limit}"
            
            self.logger.info(f"Fetching posts from r/{subreddit} ({sort})")
            
            response = self.session.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data and 'children' in data['data']:
                for child in data['data']['children']:
                    post_data = child['data']
                    
                    # Extract post information
                    post = RedditPost(
                        id=post_data.get('id', ''),
                        title=post_data.get('title', ''),
                        content=post_data.get('selftext', ''),
                        subreddit=post_data.get('subreddit', ''),
                        author=post_data.get('author', ''),
                        score=post_data.get('score', 0),
                        num_comments=post_data.get('num_comments', 0),
                        created_utc=post_data.get('created_utc', 0),
                        url=post_data.get('url', ''),
                        permalink=f"{self.base_url}{post_data.get('permalink', '')}",
                        flair=post_data.get('link_flair_text'),
                        is_self=post_data.get('is_self', True),
                        comments=[]
                    )
                    
                    posts.append(post)
            
            self.logger.info(f"Retrieved {len(posts)} posts from r/{subreddit}")
            time.sleep(1)  # Rate limiting
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching posts from r/{subreddit}: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON response from r/{subreddit}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error fetching posts from r/{subreddit}: {e}")
        
        return posts
    
    def get_post_comments(self, post_id: str, subreddit: str, limit: int = 10) -> List[str]:
        """
        Get top comments from a specific post
        
        Args:
            post_id: Reddit post ID
            subreddit: Subreddit name
            limit: Number of top comments to retrieve
        
        Returns:
            List of comment texts
        """
        comments = []
        
        try:
            url = f"{self.base_url}/r/{subreddit}/comments/{post_id}.json?limit={limit}"
            
            response = self.session.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if len(data) > 1 and 'data' in data[1] and 'children' in data[1]['data']:
                for child in data[1]['data']['children']:
                    if child['kind'] == 't1':  # Comment
                        comment_data = child['data']
                        comment_text = comment_data.get('body', '')
                        
                        # Filter out deleted/removed comments
                        if comment_text and comment_text not in ['[deleted]', '[removed]']:
                            comments.append(comment_text)
                            
                            if len(comments) >= limit:
                                break
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            self.logger.error(f"Error fetching comments for post {post_id}: {e}")
        
        return comments
    
    def scrape_bangladesh_content(self, hours_back: int = 24, 
                                 posts_per_subreddit: int = 15) -> List[Dict[str, Any]]:
        """
        Scrape trending content from all Bangladesh-related subreddits
        
        Args:
            hours_back: How many hours back to look for content
            posts_per_subreddit: Number of posts to get from each subreddit
        
        Returns:
            List of processed Reddit content
        """
        all_content = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        cutoff_timestamp = cutoff_time.timestamp()
        
        self.logger.info(f"Starting Reddit scrape for Bangladesh content (last {hours_back} hours)")
        
        for subreddit in self.bangladesh_subreddits:
            try:
                # Get hot posts
                hot_posts = self.get_subreddit_posts(
                    subreddit=subreddit,
                    sort='hot',
                    limit=posts_per_subreddit
                )
                
                # Get new posts for recent content
                new_posts = self.get_subreddit_posts(
                    subreddit=subreddit,
                    sort='new',
                    limit=posts_per_subreddit // 2
                )
                
                # Combine and filter by time
                all_posts = hot_posts + new_posts
                recent_posts = [p for p in all_posts if p.created_utc >= cutoff_timestamp]
                
                for post in recent_posts:
                    # Get some comments for popular posts
                    if post.num_comments > 5:
                        comments = self.get_post_comments(post.id, post.subreddit, limit=5)
                        post.comments = comments
                    
                    # Convert to dictionary format
                    content_item = {
                        'id': post.id,
                        'title': post.title,
                        'content': post.content,
                        'subreddit': post.subreddit,
                        'author': post.author,
                        'score': post.score,
                        'num_comments': post.num_comments,
                        'created_utc': post.created_utc,
                        'url': post.url,
                        'permalink': post.permalink,
                        'flair': post.flair,
                        'comments': post.comments or [],
                        'source': 'reddit',
                        'platform': 'reddit',
                        'timestamp': datetime.fromtimestamp(post.created_utc).isoformat(),
                        'engagement_score': post.score + (post.num_comments * 2),  # Simple engagement metric
                        'text_content': f"{post.title} {post.content} {' '.join(post.comments or [])}"
                    }
                    
                    all_content.append(content_item)
                
                self.logger.info(f"Processed {len(recent_posts)} recent posts from r/{subreddit}")
                
            except Exception as e:
                self.logger.error(f"Error processing subreddit r/{subreddit}: {e}")
                continue
        
        # Sort by engagement score (score + comments)
        all_content.sort(key=lambda x: x['engagement_score'], reverse=True)
        
        self.logger.info(f"Total Reddit content collected: {len(all_content)} items")
        
        return all_content
    
    def get_trending_topics(self, content: List[Dict[str, Any]], 
                           min_score: int = 5) -> List[Dict[str, Any]]:
        """
        Extract trending topics from Reddit content
        
        Args:
            content: List of Reddit content items
            min_score: Minimum score threshold for trending topics
        
        Returns:
            List of trending topics with metadata
        """
        trending_topics = []
        
        # Filter high-engagement content
        high_engagement = [item for item in content if item['engagement_score'] >= min_score]
        
        # Group by subreddit for diversity
        subreddit_groups = {}
        for item in high_engagement:
            subreddit = item['subreddit']
            if subreddit not in subreddit_groups:
                subreddit_groups[subreddit] = []
            subreddit_groups[subreddit].append(item)
        
        # Extract trending topics
        for subreddit, items in subreddit_groups.items():
            # Sort by engagement within subreddit
            items.sort(key=lambda x: x['engagement_score'], reverse=True)
            
            # Take top items from each subreddit
            for item in items[:3]:  # Top 3 from each subreddit
                topic = {
                    'topic': item['title'],
                    'description': item['content'][:200] if item['content'] else '',
                    'subreddit': item['subreddit'],
                    'score': item['score'],
                    'comments': item['num_comments'],
                    'engagement': item['engagement_score'],
                    'url': item['permalink'],
                    'timestamp': item['timestamp'],
                    'source': 'reddit'
                }
                trending_topics.append(topic)
        
        # Sort all topics by engagement
        trending_topics.sort(key=lambda x: x['engagement'], reverse=True)
        
        return trending_topics[:20]  # Return top 20 trending topics
    
    def save_content_to_file(self, content: List[Dict[str, Any]], 
                           filename: Optional[str] = None) -> str:
        """
        Save scraped content to JSON file
        
        Args:
            content: List of content items
            filename: Optional filename (auto-generated if not provided)
        
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reddit_bangladesh_content_{timestamp}.json"
        
        filepath = os.path.join(os.getcwd(), filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Saved {len(content)} items to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving content to file: {e}")
            return ""
    
    def scrape_posts_with_praw(self, subreddit_name: str, limit: int = 25, sort: str = 'hot') -> List[RedditPost]:
        """
        Scrape Reddit posts using PRAW (Python Reddit API Wrapper)
        More reliable than direct API calls
        
        Args:
            subreddit_name: Name of subreddit to scrape
            limit: Number of posts to retrieve
            sort: Sort method ('hot', 'new', 'top', 'rising')
        
        Returns:
            List of RedditPost objects
        """
        posts = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            self.logger.info(f"Fetching {limit} {sort} posts from r/{subreddit_name}")
            
            # Get posts based on sort method
            if sort == 'hot':
                submissions = subreddit.hot(limit=limit)
            elif sort == 'new':
                submissions = subreddit.new(limit=limit)
            elif sort == 'top':
                submissions = subreddit.top(limit=limit, time_filter='day')
            elif sort == 'rising':
                submissions = subreddit.rising(limit=limit)
            else:
                submissions = subreddit.hot(limit=limit)
            
            for submission in submissions:
                # Get top comments for the post
                submission.comments.replace_more(limit=0)  # Remove "more comments" objects
                top_comments = []
                
                for comment in submission.comments[:3]:  # Get top 3 comments
                    if hasattr(comment, 'body') and len(comment.body) > 10:
                        top_comments.append(comment.body)
                
                post = RedditPost(
                    id=submission.id,
                    title=submission.title,
                    content=submission.selftext if submission.is_self else '',
                    subreddit=submission.subreddit.display_name,
                    author=str(submission.author) if submission.author else '[deleted]',
                    score=submission.score,
                    num_comments=submission.num_comments,
                    created_utc=submission.created_utc,
                    url=submission.url,
                    permalink=f"https://www.reddit.com{submission.permalink}",
                    flair=submission.link_flair_text,
                    is_self=submission.is_self,
                    comments=top_comments
                )
                
                posts.append(post)
            
            self.logger.info(f"Successfully retrieved {len(posts)} posts from r/{subreddit_name}")
            
        except Exception as e:
            self.logger.error(f"Error scraping r/{subreddit_name} with PRAW: {e}")
        
        return posts
    
    def scrape_all_bangladesh_subreddits_praw(self, limit_per_subreddit: int = 10) -> List[Dict]:
        """
        Scrape all Bangladesh-related subreddits using PRAW
        
        Args:
            limit_per_subreddit: Number of posts to get from each subreddit
        
        Returns:
            List of formatted post dictionaries
        """
        all_posts = []
        
        self.logger.info(f"Starting to scrape {len(self.bangladesh_subreddits)} Bangladesh subreddits")
        
        for subreddit_name in self.bangladesh_subreddits:
            try:
                posts = self.scrape_posts_with_praw(subreddit_name, limit_per_subreddit)
                
                for post in posts:
                    formatted_post = {
                        'source': f'reddit_r_{post.subreddit}',
                        'title': post.title,
                        'content': post.content,
                        'url': post.permalink,
                        'score': post.score,
                        'comments_count': post.num_comments,
                        'created_utc': post.created_utc,
                        'author': post.author,
                        'flair': post.flair,
                        'comments': post.comments,
                        'scraped_date': datetime.now().date()
                    }
                    all_posts.append(formatted_post)
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Failed to scrape r/{subreddit_name}: {e}")
                continue
        
        self.logger.info(f"Total posts collected: {len(all_posts)}")
        return all_posts

def main():
    """Test the Reddit scraper"""
    scraper = RedditScraper()
    
    print("🔍 Testing Reddit Scraper for Bangladesh Content")
    print("=" * 60)
    
    # Test individual subreddit
    posts = scraper.get_subreddit_posts('bangladesh', limit=5)
    print(f"📊 Retrieved {len(posts)} posts from r/bangladesh")
    
    if posts:
        print(f"📄 Sample post: {posts[0].title}")
        print(f"💬 Comments: {posts[0].num_comments}")
        print(f"⬆️ Score: {posts[0].score}")
    
    # Test full scraping
    print("\n🌐 Testing full Bangladesh content scraping...")
    content = scraper.scrape_bangladesh_content(hours_back=24, posts_per_subreddit=5)
    
    print(f"📊 Total content items: {len(content)}")
    
    if content:
        # Show sample
        sample = content[0]
        print(f"📄 Top item: {sample['title']}")
        print(f"📍 Subreddit: r/{sample['subreddit']}")
        print(f"🎯 Engagement: {sample['engagement_score']}")
        
        # Get trending topics
        trending = scraper.get_trending_topics(content)
        print(f"\n🔥 Trending topics found: {len(trending)}")
        
        for i, topic in enumerate(trending[:3], 1):
            print(f"   {i}. {topic['topic']} (r/{topic['subreddit']}) - {topic['engagement']} engagement")

if __name__ == "__main__":
    main()