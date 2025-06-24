#!/usr/bin/env python3
"""
Reddit Integration Module for Main Pipeline
Handles Reddit data scraping, emoji removal, and flair-wise categorization
"""

import os
import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RedditIntegration:
    """Main Reddit integration class for pipeline"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def remove_emojis(self, text: str) -> str:
        """Remove emojis from text"""
        if not text:
            return ""
        
        # Emoji pattern - covers most Unicode emoji ranges
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"  # enclosed characters
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
            "]+", 
            flags=re.UNICODE
        )
        
        # Remove emojis and extra whitespace
        clean_text = emoji_pattern.sub('', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
    
    def categorize_by_flair(self, posts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize Reddit posts by flair (Reddit-specific categories)"""
        categorized_data = {
            'discussion': [],           # Discussion/আলোচনা
            'askdesh': [],             # AskDesh/দেশ কে জিজ্ঞাসা  
            'education': [],           # Education/শিক্ষা
            'politics': [],            # Politics/রাজনীতি
            'technology': [],          # Science & Technology/বিজ্ঞান ও প্রযুক্তি
            'environment': [],         # Environment/পরিবেশ
            'events': [],              # Events/ঘটনা
            'history': [],             # History/ইতিহাস
            'seeking_advice': [],      # Seeking advice/পরামর্শ
            'uncategorized': []        # No flair or unrecognized flair
        }
        
        # Reddit flair-to-category mapping (exact matches)
        flair_mapping = {
            # Bengali and English flair variations
            'discussion/আলোচনা': 'discussion',
            'discussion': 'discussion',
            'আলোচনা': 'discussion',
            
            'askdesh/দেশ কে জিজ্ঞাসা': 'askdesh',
            'askdesh': 'askdesh',
            'দেশ কে জিজ্ঞাসা': 'askdesh',
            
            'education/শিক্ষা': 'education',
            'education': 'education',
            'শিক্ষা': 'education',
            
            'politics/রাজনীতি': 'politics',
            'politics': 'politics',
            'রাজনীতি': 'politics',
            
            'science & technology/বিজ্ঞান ও প্রযুক্তি': 'technology',
            'science & technology': 'technology',
            'বিজ্ঞান ও প্রযুক্তি': 'technology',
            'technology': 'technology',
            
            'environment/পরিবেশ': 'environment',
            'environment': 'environment',
            'পরিবেশ': 'environment',
            
            'events/ঘটনা': 'events',
            'events': 'events',
            'ঘটনা': 'events',
            
            'history/ইতিহাস': 'history',
            'history': 'history',
            'ইতিহাস': 'history',
            
            'seeking advice/পরামর্শ': 'seeking_advice',
            'seeking advice': 'seeking_advice',
            'পরামর্শ': 'seeking_advice',
        }
        
        for post in posts:
            # Clean emoji from post data
            post['title'] = self.remove_emojis(post.get('title', ''))
            post['content'] = self.remove_emojis(post.get('content', ''))
            
            # Clean comments
            if 'comments' in post and post['comments']:
                post['comments'] = [self.remove_emojis(comment) for comment in post['comments']]
            
            # Get flair and categorize based on exact flair matching
            flair = post.get('flair', '').lower().strip() if post.get('flair') else ''
            
            category = 'uncategorized'
            
            # Check for exact flair match first
            if flair and flair in flair_mapping:
                category = flair_mapping[flair]
            
            # If no exact match, try partial matching for complex flairs
            if category == 'uncategorized' and flair:
                for flair_keyword, cat in flair_mapping.items():
                    if flair_keyword in flair:
                        category = cat
                        break
            
            # Add metadata
            post['category'] = category
            post['processed_at'] = datetime.now().isoformat()
            
            # Add to appropriate category
            categorized_data[category].append(post)
        
        return categorized_data
    
    def scrape_reddit_data(self) -> List[Dict[str, Any]]:
        """Scrape Reddit data using RedditDataScrapper (preferred)"""
        try:
            # Import the preferred reddit data scrapper
            from .reddit_data_scrapping import RedditDataScrapper
            
            scraper = RedditDataScrapper()
            # Run comprehensive analysis and get the posts
            result = scraper.run_comprehensive_analysis(posts_per_subreddit=20)
            
            # Extract posts from the subreddit results
            posts = []
            for subreddit_data in result.get('subreddit_responses', []):
                for post in subreddit_data.get('posts', []):
                    # Convert to the expected format
                    formatted_post = {
                        'source': f'reddit_r_{post.get("subreddit", "unknown")}',
                        'title': post.get('title', ''),
                        'content': post.get('content', ''),
                        'url': post.get('url', ''),
                        'score': post.get('score', 0),
                        'comments_count': post.get('num_comments', 0),
                        'created_utc': post.get('created_utc', 0),
                        'author': post.get('author', ''),
                        'flair': post.get('flair', ''),
                        'comments': post.get('comments', []),
                        'scraped_date': datetime.now().date()
                    }
                    posts.append(formatted_post)
            
            if posts:
                self.logger.info(f"✅ Scraped {len(posts)} Reddit posts using RedditDataScrapper")
                return posts
            else:
                self.logger.warning("⚠️ No Reddit posts scraped from RedditDataScrapper")
                return []
                
        except ImportError as ie:
            self.logger.warning(f"⚠️ RedditDataScrapper not available: {ie}")
            # Fallback to original reddit_scraper
            try:
                from .reddit_scraper import RedditScraper
                
                scraper = RedditScraper()
                posts = scraper.scrape_all_bangladesh_subreddits_praw()  # Correct method name
                
                if posts:
                    self.logger.info(f"✅ Scraped {len(posts)} Reddit posts using fallback RedditScraper")
                    return posts
                else:
                    self.logger.warning("⚠️ No Reddit posts scraped from fallback")
                    return []
                    
            except ImportError:
                # Fallback: try to load from existing test data
                self.logger.info("📂 Loading Reddit data from existing test file...")
                try:
                    import glob
                    reddit_files = glob.glob('reddit_all_posts_*.json')
                    if reddit_files:
                        latest_file = sorted(reddit_files)[-1]
                        with open(latest_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        posts = data.get('all_posts', [])
                        self.logger.info(f"✅ Loaded {len(posts)} posts from {latest_file}")
                        return posts
                    else:
                        self.logger.warning("⚠️ No Reddit test data files found")
                        return []
                except Exception as fallback_error:
                    self.logger.error(f"❌ Fallback loading failed: {fallback_error}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"❌ Error scraping Reddit data: {e}")
            return []
    
    def process_reddit_data_for_pipeline(self) -> Dict[str, Any]:
        """Main function to process Reddit data for pipeline integration"""
        self.logger.info("🚀 Starting Reddit data processing for pipeline...")
        
        # Step 1: Scrape Reddit data
        posts = self.scrape_reddit_data()
        
        if not posts:
            return {
                'success': False,
                'message': 'No Reddit data available',
                'data': {}
            }
        
        # Step 2: Categorize by flair and remove emojis
        categorized_data = self.categorize_by_flair(posts)
        
        # Step 3: Generate summary statistics
        stats = {}
        total_posts = 0
        for category, category_posts in categorized_data.items():
            count = len(category_posts)
            stats[category] = count
            total_posts += count
        
        # Step 4: Prepare result
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'total_posts': total_posts,
            'categories': stats,
            'data': categorized_data,
            'message': f'Successfully processed {total_posts} Reddit posts across {len([k for k, v in stats.items() if v > 0])} categories'
        }
        
        self.logger.info(f"✅ Reddit processing completed: {total_posts} posts categorized")
        self.logger.info(f"📊 Category breakdown: {stats}")
        
        return result
    
    def get_posts_by_category(self, category: str, reddit_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get posts for a specific category"""
        if not reddit_data.get('success', False):
            return []
        
        return reddit_data.get('data', {}).get(category, [])
    
    def get_available_categories(self, reddit_data: Dict[str, Any]) -> List[str]:
        """Get list of categories with posts"""
        if not reddit_data.get('success', False):
            return []
        
        categories = []
        for category, posts in reddit_data.get('data', {}).items():
            if posts:  # Only include categories with posts
                categories.append(category)
        
        return categories

# Helper function for pipeline integration
def get_reddit_data_for_pipeline() -> Dict[str, Any]:
    """
    Main function to be called from helpers.py
    Returns categorized Reddit data ready for trending analysis
    """
    reddit_integration = RedditIntegration()
    return reddit_integration.process_reddit_data_for_pipeline()

def get_reddit_posts_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Get Reddit posts for a specific category
    """
    reddit_integration = RedditIntegration()
    reddit_data = reddit_integration.process_reddit_data_for_pipeline()
    return reddit_integration.get_posts_by_category(category, reddit_data)

if __name__ == "__main__":
    # Test the integration
    logging.basicConfig(level=logging.INFO)
    
    reddit_integration = RedditIntegration()
    result = reddit_integration.process_reddit_data_for_pipeline()
    
    print("🔥 Reddit Integration Test Results:")
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    
    if result['success']:
        print(f"Total Posts: {result['total_posts']}")
        print("Categories:")
        for category, count in result['categories'].items():
            if count > 0:
                print(f"  {category}: {count} posts")
