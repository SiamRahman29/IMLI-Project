#!/usr/bin/env python3
"""
Enhanced Reddit Category-wise Scraper with LLM Integration
Categorizes subreddits and gets 2 LLM responses per category
"""

import sys
import os
sys.path.insert(0, '.')

import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class EnhancedRedditCategoryScraper:
    """Enhanced Reddit scraper that processes content by category and gets multiple LLM responses per category"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        
        # Import the existing Reddit scraper
        try:
            from app.services.reddit_scraper import RedditScraper
            self.reddit_scraper = RedditScraper()
            self.logger.info("✅ Reddit scraper initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Reddit scraper: {e}")
            raise
        
        # Define subreddit categories as per your requirements
        self.subreddit_categories = {
            'bangladesh': {
                'name': 'বাংলাদেশ',
                'subreddits': ['bangladesh', 'dhaka'],
                'description': 'Bangladesh-specific content and discussions'
            },
            'news': {
                'name': 'সংবাদ',
                'subreddits': ['news', 'worldnews', 'AlJazeera'],
                'description': 'News and current affairs'
            },
            'technology': {
                'name': 'প্রযুক্তি',
                'subreddits': ['technology'],
                'description': 'Technology and innovation discussions'
            },
            'education': {
                'name': 'শিক্ষা',
                'subreddits': ['buet', 'nsu'],  # Removed 'du' as it doesn't exist
                'description': 'Education and university discussions'
            },
            'culture': {
                'name': 'সংস্কৃতি',
                'subreddits': ['bengalimemes', 'southasia'],  # Removed 'desitwitter' as it has no posts
                'description': 'Cultural and social discussions'
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for enhanced scraper"""
        logger = logging.getLogger('enhanced_reddit_scraper')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def scrape_category_content(self, category: str, subreddits: List[str], 
                               posts_per_subreddit: int = 15) -> List[Dict]:
        """
        Scrape content from subreddits in a specific category
        
        Args:
            category: Category name
            subreddits: List of subreddit names
            posts_per_subreddit: Number of posts per subreddit
        
        Returns:
            List of posts from this category
        """
        category_posts = []
        successful_subreddits = []
        failed_subreddits = []
        
        self.logger.info(f"🔍 Scraping category '{category}' with {len(subreddits)} subreddits")
        
        for subreddit in subreddits:
            try:
                self.logger.info(f"   📡 Scraping r/{subreddit}...")
                posts = self.reddit_scraper.scrape_posts_with_praw(
                    subreddit_name=subreddit, 
                    limit=posts_per_subreddit
                )
                
                if posts:
                    # Convert RedditPost objects to dictionaries
                    for post in posts:
                        post_dict = {
                            'id': post.id,
                            'title': post.title,
                            'content': post.content,
                            'source': f'reddit_r_{post.subreddit}',
                            'score': post.score,
                            'comments_count': post.num_comments,
                            'created_utc': post.created_utc,
                            'author': post.author,
                            'flair': post.flair,
                            'comments': post.comments or [],
                            'url': post.permalink,
                            'category': category,
                            'scraped_date': datetime.now().date().isoformat()
                        }
                        category_posts.append(post_dict)
                    
                    successful_subreddits.append(subreddit)
                    self.logger.info(f"   ✅ r/{subreddit}: {len(posts)} posts")
                else:
                    failed_subreddits.append(subreddit)
                    self.logger.warning(f"   ⚠️ r/{subreddit}: No posts found")
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                failed_subreddits.append(subreddit)
                self.logger.error(f"   ❌ r/{subreddit}: {e}")
                continue
        
        self.logger.info(f"📊 Category '{category}' summary:")
        self.logger.info(f"   ✅ Successful: {successful_subreddits}")
        self.logger.info(f"   ❌ Failed: {failed_subreddits}")
        self.logger.info(f"   📄 Total posts: {len(category_posts)}")
        
        return category_posts
    
    def clean_text_for_llm(self, text: str) -> str:
        """
        Clean text by removing whitespaces, emojis and unnecessary characters
        
        Args:
            text: Raw text to clean
        
        Returns:
            Cleaned text optimized for LLM
        """
        import re
        
        if not text:
            return ""
        
        # Remove emojis using regex
        emoji_pattern = re.compile("["
                                  u"\U0001F600-\U0001F64F"  # emoticons
                                  u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                  u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                  u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                  u"\U00002702-\U000027B0"
                                  u"\U000024C2-\U0001F251"
                                  "]+", flags=re.UNICODE)
        text = emoji_pattern.sub('', text)
        
        # Remove extra whitespaces, newlines, tabs
        text = re.sub(r'\s+', ' ', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove special characters except basic punctuation
        text = re.sub(r'[^\w\s\u0980-\u09FF.,!?()-]', '', text)
        
        return text.strip()

    def prepare_category_content_for_llm(self, posts: List[Dict], category: str) -> str:
        """
        Prepare optimized category content for LLM analysis with token reduction
        
        Args:
            posts: List of posts from the category
            category: Category name
        
        Returns:
            Optimized text for LLM with reduced tokens
        """
        if not posts:
            return ""
        
        # Sort by engagement (score + comments)
        sorted_posts = sorted(posts, 
                            key=lambda x: x.get('score', 0) + x.get('comments_count', 0) * 2, 
                            reverse=True)
        
        # Take top posts (reduced for token efficiency)
        top_posts = sorted_posts[:15]  # Reduced from 20 to 15
        
        content_parts = []
        
        for post in top_posts:
            title = post.get('title', '').strip()
            content = post.get('content', '').strip()
            comments = post.get('comments', [])
            
            # Build optimized post content
            post_text = []
            
            # Take full title but clean it
            if title:
                clean_title = self.clean_text_for_llm(title)
                if clean_title:
                    post_text.append(f"Title:{clean_title}")
            
            # Take full content but clean it (no truncation)
            if content and len(content) > 10:
                clean_content = self.clean_text_for_llm(content)
                if clean_content:
                    post_text.append(f"Content:{clean_content}")
            
            # Take only top 10 comments (reduced from all comments)
            if comments:
                top_comments = comments[:10]  # Top 10 comments only
                clean_comments = []
                for comment in top_comments:
                    clean_comment = self.clean_text_for_llm(comment)
                    if clean_comment:
                        clean_comments.append(clean_comment)
                
                if clean_comments:
                    post_text.append(f"Comments:{' | '.join(clean_comments)}")
            
            if post_text:
                content_parts.append(" ".join(post_text))
        
        combined_content = "\n---\n".join(content_parts)
        
        # More aggressive length control for token optimization
        if len(combined_content) > 20000:  # Reduced from 30000 to 20000
            combined_content = combined_content[:20000] + "..."
        
        self.logger.info(f"📝 Optimized content for '{category}': {len(combined_content)} characters")
        
        return combined_content
    
    def create_category_llm_prompt(self, content: str, category: str, category_name: str, 
                                  response_number: int) -> str:
        """
        Create optimized LLM prompt for category-wise analysis (token efficient)
        
        Args:
            content: Reddit content from the category
            category: Category key
            category_name: Bengali category name
            response_number: Response number (1 or 2)
        
        Returns:
            Optimized LLM prompt
        """
        # Shortened and optimized prompt to save tokens
        prompt = f"""তুমি বাংলাদেশি সোশ্যাল মিডিয়া ট্রেন্ড বিশ্লেষক। '{category_name}' বিভাগের Reddit content থেকে ট্রেন্ডিং বিষয় চিহ্নিত করো।

বিভাগ: {category_name}
বিশ্লেষণ: #{response_number}

নিয়ম:
- বাংলায় response দাও
- {category_name} বিভাগের সাথে প্রাসঙ্গিক বিষয়ে ফোকাস করো
- ২-৪ শব্দের সংক্ষিপ্ত বাক্যাংশ দাও
- ব্যক্তির নাম এড়াও

Reddit Content:
{content}

Output Format:
{category_name} ট্রেন্ডিং (#{response_number}):
১. [বাংলা শব্দ/বাক্যাংশ]
২. [বাংলা শব্দ/বাক্যাংশ]
৩. [বাংলা শব্দ/বাক্যাংশ]
৪. [বাংলা শব্দ/বাক্যাংশ]
৫. [বাংলা শব্দ/বাক্যাংশ]"""
        
        return prompt
    
    def call_groq_llm_for_category_analysis(self, prompt: str, category: str, 
                                          response_number: int) -> Optional[str]:
        """
        Call Groq LLM API for category-wise trending analysis
        
        Args:
            prompt: LLM prompt
            category: Category name
            response_number: Response number (1 or 2)
        
        Returns:
            LLM response or None if failed
        """
        self.logger.info(f"🤖 Calling Groq LLM for category '{category}' (Response #{response_number})")
        
        try:
            from groq import Groq
            
            # Get API key
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                self.logger.error("❌ GROQ_API_KEY not found in environment variables!")
                return None
            
            # Initialize Groq client
            client = Groq(api_key=api_key)
            
            # Call Groq API with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Log token estimation for debugging
                    estimated_tokens = len(prompt) // 3.5
                    self.logger.info(f"📊 Estimated tokens for '{category}' #{response_number}: {estimated_tokens:.0f}")
                    
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system", 
                                "content": "তুমি বাংলা ভাষা বিশ্লেষক। ইংরেজি, বাংলিশ, বাংলা বুঝো কিন্তু response বাংলায় দাও।"  # Shortened system message
                            },
                            {
                                "role": "user", 
                                "content": prompt
                            }
                        ],
                        temperature=0.3,  # Lower temperature for consistency
                        max_tokens=400,   # Reduced from 800 to 400
                        top_p=0.8
                    )
                    
                    llm_response = response.choices[0].message.content.strip()
                    self.logger.info(f"✅ Received response for '{category}' #{response_number} ({len(llm_response)} chars)")
                    
                    return llm_response
                    
                except Exception as api_error:
                    self.logger.warning(f"⚠️ Attempt {attempt + 1} failed for '{category}' #{response_number}: {api_error}")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 3
                        self.logger.info(f"🔄 Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"❌ All {max_retries} attempts failed for '{category}' #{response_number}")
                        return None
                        
        except ImportError:
            self.logger.error("❌ Groq library not found! Install with: pip install groq")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error calling Groq API for '{category}' #{response_number}: {e}")
            return None
    
    def parse_llm_response(self, llm_response: str) -> List[str]:
        """Parse LLM response to extract trending words"""
        if not llm_response:
            return []
        
        trending_words = []
        lines = llm_response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for numbered items (Bengali or English numbers)
            if any(char in line for char in ['১', '২', '৩', '৪', '৫', '৬', '৭', '৮']) or \
               line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.')):
                # Remove numbering
                clean_line = line
                for num in ['১.', '২.', '৩.', '৪.', '৫.', '৬.', '৭.', '৮.', 
                           '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.']:
                    clean_line = clean_line.replace(num, '').strip()
                
                if clean_line and len(clean_line) > 1:
                    trending_words.append(clean_line)
        
        return trending_words
    
    def scrape_all_categories_with_llm_analysis(self, posts_per_subreddit: int = 10) -> Dict[str, Any]:
        """
        Main function: Scrape all categories and get 2 LLM responses per category
        
        Args:
            posts_per_subreddit: Number of posts per subreddit
        
        Returns:
            Complete analysis results
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'Reddit Category-wise Trending Analysis',
            'categories_analyzed': {},
            'summary': {
                'total_categories': len(self.subreddit_categories),
                'successful_categories': 0,
                'failed_categories': 0,
                'total_posts': 0,
                'total_llm_responses': 0
            }
        }
        
        self.logger.info(f"🚀 Starting category-wise Reddit analysis")
        self.logger.info(f"📊 Categories to analyze: {list(self.subreddit_categories.keys())}")
        
        for category_key, category_info in self.subreddit_categories.items():
            category_name = category_info['name']
            subreddits = category_info['subreddits']
            
            self.logger.info(f"\n" + "="*60)
            self.logger.info(f"🏷️ Processing Category: {category_name} ({category_key})")
            self.logger.info(f"📡 Subreddits: {subreddits}")
            self.logger.info(f"="*60)
            
            try:
                # Step 1: Scrape category content
                category_posts = self.scrape_category_content(
                    category=category_key,
                    subreddits=subreddits,
                    posts_per_subreddit=posts_per_subreddit
                )
                
                if not category_posts:
                    self.logger.warning(f"⚠️ No posts found for category '{category_name}', skipping LLM analysis")
                    results['categories_analyzed'][category_key] = {
                        'category_name': category_name,
                        'subreddits': subreddits,
                        'posts_count': 0,
                        'status': 'failed',
                        'error': 'No posts found',
                        'llm_responses': []
                    }
                    results['summary']['failed_categories'] += 1
                    continue
                
                # Step 2: Prepare content for LLM
                content_text = self.prepare_category_content_for_llm(category_posts, category_key)
                
                # Step 3: Get 2 LLM responses for this category
                llm_responses = []
                
                for response_num in range(1, 3):  # Get 2 responses
                    self.logger.info(f"🤖 Getting LLM response #{response_num} for '{category_name}'")
                    
                    prompt = self.create_category_llm_prompt(
                        content=content_text,
                        category=category_key,
                        category_name=category_name,
                        response_number=response_num
                    )
                    
                    llm_response = self.call_groq_llm_for_category_analysis(
                        prompt=prompt,
                        category=category_key,
                        response_number=response_num
                    )
                    
                    if llm_response:
                        trending_words = self.parse_llm_response(llm_response)
                        llm_responses.append({
                            'response_number': response_num,
                            'raw_response': llm_response,
                            'trending_words': trending_words,
                            'status': 'success'
                        })
                        self.logger.info(f"✅ Response #{response_num}: {len(trending_words)} trending words extracted")
                        
                        # Show the words
                        for i, word in enumerate(trending_words, 1):
                            self.logger.info(f"   {i}. {word}")
                    else:
                        llm_responses.append({
                            'response_number': response_num,
                            'raw_response': None,
                            'trending_words': [],
                            'status': 'failed',
                            'error': 'LLM call failed'
                        })
                        self.logger.error(f"❌ Response #{response_num}: Failed")
                    
                    # Short delay between responses
                    time.sleep(2)
                
                # Store category results
                results['categories_analyzed'][category_key] = {
                    'category_name': category_name,
                    'subreddits': subreddits,
                    'posts_count': len(category_posts),
                    'status': 'success',
                    'llm_responses': llm_responses,
                    'posts_sample': category_posts[:5]  # Store sample posts for reference
                }
                
                results['summary']['successful_categories'] += 1
                results['summary']['total_posts'] += len(category_posts)
                results['summary']['total_llm_responses'] += len([r for r in llm_responses if r['status'] == 'success'])
                
                self.logger.info(f"✅ Category '{category_name}' completed successfully")
                self.logger.info(f"   📄 Posts: {len(category_posts)}")
                self.logger.info(f"   🤖 LLM Responses: {len([r for r in llm_responses if r['status'] == 'success'])}/2")
                
            except Exception as e:
                self.logger.error(f"❌ Error processing category '{category_name}': {e}")
                results['categories_analyzed'][category_key] = {
                    'category_name': category_name,
                    'subreddits': subreddits,
                    'posts_count': 0,
                    'status': 'failed',
                    'error': str(e),
                    'llm_responses': []
                }
                results['summary']['failed_categories'] += 1
                continue  # Continue with next category
        
        # Final summary
        self.logger.info(f"\n" + "="*60)
        self.logger.info(f"🎉 Category-wise Analysis Complete!")
        self.logger.info(f"📊 Summary:")
        self.logger.info(f"   ✅ Successful categories: {results['summary']['successful_categories']}")
        self.logger.info(f"   ❌ Failed categories: {results['summary']['failed_categories']}")
        self.logger.info(f"   📄 Total posts: {results['summary']['total_posts']}")
        self.logger.info(f"   🤖 Total LLM responses: {results['summary']['total_llm_responses']}")
        self.logger.info(f"="*60)
        
        return results
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """Save analysis results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reddit_category_trending_analysis_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 Results saved to: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"❌ Error saving results: {e}")
            return ""
    
    def display_results_summary(self, results: Dict[str, Any]):
        """Display a formatted summary of results"""
        print(f"\n" + "="*80)
        print(f"🏆 REDDIT CATEGORY-WISE TRENDING ANALYSIS RESULTS")
        print(f"="*80)
        
        for category_key, category_data in results['categories_analyzed'].items():
            category_name = category_data['category_name']
            status = category_data['status']
            
            if status == 'success':
                print(f"\n✅ {category_name} ({category_key})")
                print(f"   📊 Posts: {category_data['posts_count']}")
                
                for response in category_data['llm_responses']:
                    if response['status'] == 'success':
                        print(f"\n   🤖 LLM Response #{response['response_number']}:")
                        for i, word in enumerate(response['trending_words'], 1):
                            print(f"      {i}. {word}")
                    else:
                        print(f"\n   ❌ LLM Response #{response['response_number']}: Failed")
            else:
                print(f"\n❌ {category_name} ({category_key}): {category_data.get('error', 'Unknown error')}")
        
        summary = results['summary']
        print(f"\n" + "-"*80)
        print(f"📈 OVERALL SUMMARY:")
        print(f"   Categories Processed: {summary['successful_categories']}/{summary['total_categories']}")
        print(f"   Total Posts Analyzed: {summary['total_posts']}")
        print(f"   Total LLM Responses: {summary['total_llm_responses']}")
        print(f"=" * 80)


def main():
    """Main function to run category-wise Reddit analysis"""
    try:
        # Create enhanced scraper
        scraper = EnhancedRedditCategoryScraper()
        
        # Run category-wise analysis
        results = scraper.scrape_all_categories_with_llm_analysis(posts_per_subreddit=8)
        
        # Save results
        filename = scraper.save_results(results)
        
        # Display summary
        scraper.display_results_summary(results)
        
        print(f"\n🎯 Analysis complete! Results saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Error running analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
