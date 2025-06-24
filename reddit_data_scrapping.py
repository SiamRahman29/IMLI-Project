#!/usr/bin/env python3
"""
Reddit Data Scrapping with Comprehensive LLM Analysis
Scrapes all subreddits, processes content, and gets 6-8 trending responses from LLM
"""

import sys
import os
sys.path.insert(0, '.')

import json
import time
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class RedditDataScrapper:
    """Comprehensive Reddit scraper that processes all content and gets trending analysis"""
    
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
        
        # All subreddits to scrape (comprehensive list)
        self.all_subreddits = [
            'bangladesh', 'dhaka',   
            'worldnews', 'AlJazeera','geopolitics',
            'technology', 
        ]

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for scraper"""
        logger = logging.getLogger('reddit_data_scrapper')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def clean_text_for_llm(self, text: str) -> str:
        """
        Clean text by removing whitespaces, emojis and unnecessary characters
        
        Args:
            text: Raw text to clean
        
        Returns:
            Cleaned text optimized for LLM
        """
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
        
        # Remove special characters except basic punctuation and Bengali characters
        text = re.sub(r'[^\w\s\u0980-\u09FF.,!?()-]', '', text)
        
        return text.strip()
    
    def scrape_all_subreddits(self, posts_per_subreddit: int = 20) -> List[Dict]:
        """
        Scrape content from all subreddits
        
        Args:
            posts_per_subreddit: Number of posts per subreddit (increased to 20)
        
        Returns:
            List of all posts from all subreddits
        """
        all_posts = []
        successful_subreddits = []
        failed_subreddits = []
        
        self.logger.info(f"🔍 Scraping {len(self.all_subreddits)} subreddits")
        self.logger.info(f"📡 Subreddits: {self.all_subreddits}")
        
        for subreddit in self.all_subreddits:
            try:
                self.logger.info(f"   📡 Scraping r/{subreddit}...")
                posts = self.reddit_scraper.scrape_posts_with_praw(
                    subreddit_name=subreddit, 
                    limit=posts_per_subreddit,
                    sort='top'  # Use top posts instead of new posts
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
                            'subreddit': subreddit,
                            'scraped_date': datetime.now().date().isoformat()
                        }
                        all_posts.append(post_dict)
                    
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
        
        self.logger.info(f"📊 Scraping Summary:")
        self.logger.info(f"   ✅ Successful: {len(successful_subreddits)} subreddits")
        self.logger.info(f"   ❌ Failed: {len(failed_subreddits)} subreddits")
        self.logger.info(f"   📄 Total posts: {len(all_posts)}")
        
        if successful_subreddits:
            self.logger.info(f"   ✅ Success list: {successful_subreddits}")
        if failed_subreddits:
            self.logger.info(f"   ❌ Failed list: {failed_subreddits}")
        
        return all_posts
    
    def prepare_subreddit_content_for_llm(self, posts: List[Dict], subreddit_name: str) -> str:
        """
        Prepare content for LLM analysis for a specific subreddit
        
        Args:
            posts: List of posts from a specific subreddit
            subreddit_name: Name of the subreddit
        
        Returns:
            Cleaned and optimized text for LLM
        """
        if not posts:
            return ""
        
        # Filter posts for this specific subreddit
        subreddit_posts = [post for post in posts if post.get('subreddit') == subreddit_name]
        
        if not subreddit_posts:
            return ""
        
        # Sort by engagement (score + comments)
        sorted_posts = sorted(subreddit_posts, 
                            key=lambda x: x.get('score', 0) + x.get('comments_count', 0) * 2, 
                            reverse=True)
        
        # Take all posts from this subreddit
        content_parts = []

        for post in sorted_posts:
            title = post.get('title', '').strip()
            content = post.get('content', '').strip()
            comments = post.get('comments', [])
            
            # Build comprehensive post content
            post_text = []
            
            # Take full title but clean it
            if title:
                clean_title = self.clean_text_for_llm(title)
                if clean_title:
                    post_text.append(f"Title: {clean_title}")
            
            # Take full content but clean it
            if content and len(content) > 10:
                clean_content = self.clean_text_for_llm(content)
                if clean_content:
                    # Increased content length for better context
                    if len(clean_content) > 800:
                        clean_content = clean_content[:800] + "..."
                    post_text.append(f"Content: {clean_content}")
            
            # Take top 8 comments for each post
            if comments:
                top_comments = comments[:8]
                clean_comments = []
                for comment in top_comments:
                    clean_comment = self.clean_text_for_llm(comment)
                    if clean_comment and len(clean_comment) > 5:
                        # Do not truncate comment, keep full comment
                        clean_comments.append(clean_comment)
                
                if clean_comments:
                    post_text.append(f"Comments: {' | '.join(clean_comments)}")
            
            if post_text:
                content_parts.append(" ".join(post_text))
        
        combined_content = "\n---\n".join(content_parts)
        
        # Token management for single subreddit
        if len(combined_content) > 30000:  # 30K characters per subreddit
            combined_content = combined_content[:30000] + "..."

        return combined_content
        """
        Prepare comprehensive content for LLM analysis with all posts
        
        Args:
            posts: List of all posts from all subreddits
        
        Returns:
            Cleaned and optimized text for LLM
        """
        if not posts:
            return ""
        
        # Sort by engagement (score + comments)
        sorted_posts = sorted(posts, 
                            key=lambda x: x.get('score', 0) + x.get('comments_count', 0) * 2, 
                            reverse=True)
        # Take top posts for analysis (increased for better coverage)
        top_posts = sorted_posts[:20]  # Take top 20 most engaging posts (increased from 10)

        content_parts = []

        for post in top_posts:
            title = post.get('title', '').strip()
            content = post.get('content', '').strip()
            comments = post.get('comments', [])
            subreddit = post.get('subreddit', '')
            
            # Build comprehensive post content
            post_text = []
            
            # Add subreddit context
            if subreddit:
                post_text.append(f"[r/{subreddit}]")
            
            # Take full title but clean it
            if title:
                clean_title = self.clean_text_for_llm(title)
                if clean_title:
                    post_text.append(f"Title: {clean_title}")
            
            # Take full content but clean it
            if content and len(content) > 10:
                clean_content = self.clean_text_for_llm(content)
                if clean_content:
                    # Increased content length for better context
                    if len(clean_content) > 800:  # Increased from 500 to 800
                        clean_content = clean_content[:800] + "..."
                    post_text.append(f"Content: {clean_content}")
            
            # Take top 8 comments for each post
            if comments:
                top_comments = comments[:8]
                clean_comments = []
                for comment in top_comments:
                    clean_comment = self.clean_text_for_llm(comment)
                    if clean_comment and len(clean_comment) > 5:
                        # Increased comment length limit
                        if len(clean_comment) > 300:  # Increased from 200 to 300
                            clean_comment = clean_comment[:300] + "..."
                        clean_comments.append(clean_comment)
                
                if clean_comments:
                    post_text.append(f"Comments: {' | '.join(clean_comments)}")
            
            if post_text:
                content_parts.append(" ".join(post_text))
        
        combined_content = "\n---\n".join(content_parts)
        
        # Token management - increased limit for better analysis with more posts and comments
        if len(combined_content) > 80000:  # Increased from 50K to 80K characters for more data
            combined_content = combined_content[:80000] + "..."

        self.logger.info(f"📝 Prepared comprehensive content: {len(combined_content)} characters")
        self.logger.info(f"📊 Posts processed: {len(top_posts)} from {len(posts)} total")
        
        # Show detailed character count info
        print(f"\n📏 INPUT CONTENT ANALYSIS:")
        print(f"   📄 Total characters: {len(combined_content):,}")
        print(f"   📊 Estimated tokens: {len(combined_content) // 3.5:.0f}")
        print(f"   📱 Posts processed: {len(top_posts)}")
        print(f"   🔤 Character breakdown:")
        print(f"      - ASCII characters: {len([c for c in combined_content if ord(c) < 128]):,}")
        print(f"      - Unicode characters: {len([c for c in combined_content if ord(c) >= 128]):,}")
        
        return combined_content
    
    def create_subreddit_llm_prompt(self, content_text: str, subreddit_name: str) -> str:
        """
        Create LLM prompt for a specific subreddit trending analysis
        
        Args:
            content_text: Processed Reddit content from specific subreddit
            subreddit_name: Name of the subreddit
        
        Returns:
            LLM prompt for subreddit-specific analysis
        """
        prompt = f"""তুমি একজন বাংলাদেশি সোশ্যাল মিডিয়া ট্রেন্ড বিশ্লেষক। নিচের r/{subreddit_name} subreddit এর পোস্ট, কন্টেন্ট এবং মন্তব্যগুলো থেকে এই subreddit এ বর্তমানে সবচেয়ে জনপ্রিয় ও ট্রেন্ডিং একটি বাক্য/বাক্যাংশ চিহ্নিত করো। Jeta niye manus ekhn beshi kotha bolche, eta trending topic.

গুরুত্বপূর্ণ তথ্য:
- response শুধুমাত্র বাংলায় দিতে হবে
- উত্তরে শুধুমাত্র একটি ২-৪ শব্দের সংক্ষিপ্ত বাক্যাংশ দাও, যা ট্রেন্ডিং হওয়ার সম্ভাবনা বেশি।
বিশ্লেষণের নিয়মাবলী:
1.ফ্রিকোয়েন্সি ও প্রাসঙ্গিকতা: Topic ta বেশি পোস্টে বেশি ব্যবহৃত হয়েছে কি না, তা বিবেচনা করো। (first priority)
2.ট্রেন্ডিং বিষয়: এই subreddit এ বর্তমানে জনপ্রিয় topic ta ফোকাস করো
3.Stop words এড়াও
4.ব্যক্তির নাম নয়: ব্যক্তির নাম বাদ দাও
5.সংক্ষিপ্ত বাক্যাংশ: ২-৪ শব্দের মধ্যে স্পষ্ট বাংলা বাক্যাংশ দাও(jeta ekta topic er moto)

r/{subreddit_name} subreddit content(Mixed Language):
{content_text}

আউটপুট ফরম্যাট (শুধুমাত্র বাংলায়):
r/{subreddit_name} emerging word:[একটি বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]"""
        
        return prompt
        """
        Create comprehensive LLM prompt for trending analysis
        
        Args:
            content_text: All processed Reddit content
        
        Returns:
            LLM prompt for comprehensive analysis
        """
        prompt = f"""তুমি একজন বাংলাদেশি সোশ্যাল মিডিয়া ট্রেন্ড বিশ্লেষক। নিচের Reddit পোস্ট, কন্টেন্ট এবং মন্তব্যগুলো থেকে বর্তমানে সবচেয়ে জনপ্রিয় ও ট্রেন্ডিং বিষয়বস্তু চিহ্নিত করো এবং সেগুলোর জন্য বাংলা শব্দ বা বাক্যাংশ তৈরি করো। (mainly tmke ekta emerging word ber korte hobe)
গুরুত্বপূর্ণ তথ্য:
- response শুধুমাত্র বাংলায় দিতে হবে
বিশ্লেষণের নিয়মাবলী:
1. ট্রেন্ডিং বিষয়: সোশ্যাল মিডিয়ায় বর্তমানে জনপ্রিয় বিষয়গুলোতে ফোকাস করো
2. Stop words এড়াও
3. ব্যক্তির নাম নয়: ব্যক্তির নাম বাদ দাও
4. একটি টপিকের জন্য শুধুমাত্র একটি প্রতিনিধিত্বকারী বাংলা শব্দ/বাক্যাংশ দাও(jemon:ইরান-ইসরায়েল দ্বন্দ্ব and ইসরায়েল-ইরান যুদ্ধ nah diye jeikono ekti deo) eta shudu ekta example.eta thakte e hobe,eta mandatory nah.
5. সংক্ষিপ্ত বাক্যাংশ: ২-৪ শব্দের মধ্যে সংক্ষিপ্ত ও স্পষ্ট বাংলা বাক্যাংশ দাও
৬. প্রাসঙ্গিকতা: বর্তমান সামাজিক, রাজনৈতিক, অর্থনৈতিক, শিক্ষা, প্রযুক্তি বা সাংস্কৃতিক প্রসঙ্গ বিবেচনা করো
Reddit বিষয়বস্তু (Mixed Language):
{content_text}
আউটপুট ফরম্যাট (শুধুমাত্র বাংলায়):
Reddit ট্রেন্ডিং শব্দ/বাক্যাংশ (৮টি):
১.[বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
২.[বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
৩.[বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
৪.[বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
৫.[বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
৬.[বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
৭.[বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
৮.[বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]"""
        
        # Show complete prompt details
        print(f"\n📋 COMPLETE LLM PROMPT ANALYSIS:")
        print(f"   📄 Prompt length: {len(prompt):,} characters")
        print(f"   📊 Estimated tokens: {len(prompt) // 3.5:.0f}")
        print(f"   🔤 Content portion: {len(content_text):,} characters")
        print(f"   📝 Template portion: {len(prompt) - len(content_text):,} characters")
        
        print(f"\n📋 COMPLETE PROMPT (FULL TEXT):")
        print("=" * 80)
        print(prompt)
        print("=" * 80)
        
        return prompt
    
    def call_groq_llm_for_subreddit_analysis(self, prompt: str, subreddit_name: str) -> Dict:
        """
        Call Groq LLM API for subreddit-specific trending analysis
        
        Args:
            prompt: LLM prompt
            subreddit_name: Name of the subreddit
        
        Returns:
            Single LLM response with emerging word for this subreddit
        """
        self.logger.info(f"🤖 Calling Groq LLM for r/{subreddit_name} analysis")
        
        try:
            from groq import Groq
            
            # Get API key
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                self.logger.error("❌ GROQ_API_KEY not found in environment variables!")
                return {'status': 'failed', 'error': 'No API key', 'subreddit': subreddit_name}
            
            # Initialize Groq client
            client = Groq(api_key=api_key)
            
            try:
                # Log token estimation for debugging
                estimated_tokens = len(prompt) // 3.5
                self.logger.info(f"📊 r/{subreddit_name} tokens: {estimated_tokens:.0f}")
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system", 
                            "content": "তুমি বাংলা ভাষা বিশ্লেষক। ইংরেজি, বাংলিশ, বাংলা বুঝো কিন্তু response বাংলায় দাও। শুধুমাত্র একটি emerging word দাও।"
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=200,  # Reduced since we only need one word
                    top_p=0.9
                )
                
                llm_response = response.choices[0].message.content.strip()
                self.logger.info(f"✅ r/{subreddit_name} response: {llm_response[:50]}...")
                
                # Parse the response to extract the emerging word
                emerging_word = self.parse_subreddit_response(llm_response, subreddit_name)
                
                result = {
                    'subreddit': subreddit_name,
                    'raw_response': llm_response,
                    'emerging_word': emerging_word,
                    'status': 'success'
                }
                
                return result
                
            except Exception as api_error:
                self.logger.error(f"❌ r/{subreddit_name} API call failed: {api_error}")
                return {
                    'subreddit': subreddit_name,
                    'raw_response': None,
                    'emerging_word': '',
                    'status': 'failed',
                    'error': str(api_error)
                }
                        
        except ImportError:
            self.logger.error("❌ Groq library not found! Install with: pip install groq")
            return {'status': 'failed', 'error': 'Groq library not found', 'subreddit': subreddit_name}
        except Exception as e:
            self.logger.error(f"❌ Error calling Groq API for r/{subreddit_name}: {e}")
            return {'status': 'failed', 'error': str(e), 'subreddit': subreddit_name}
        """
        Call Groq LLM API for comprehensive trending analysis - single response
        
        Args:
            prompt: LLM prompt
        
        Returns:
            Single LLM response with trending words
        """
        self.logger.info(f"🤖 Calling Groq LLM for comprehensive trending analysis")
        
        try:
            from groq import Groq
            
            # Get API key
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                self.logger.error("❌ GROQ_API_KEY not found in environment variables!")
                return {'status': 'failed', 'error': 'No API key'}
            
            # Initialize Groq client
            client = Groq(api_key=api_key)
            
            try:
                # Log token estimation for debugging
                estimated_tokens = len(prompt) // 3.5
                print(f"\n🔢 TOKEN ESTIMATION:")
                print(f"   📄 Total prompt characters: {len(prompt):,}")
                print(f"   📊 Estimated input tokens: {estimated_tokens:.0f}")
                print(f"   🎯 Token calculation: {len(prompt):,} chars ÷ 3.5 = {estimated_tokens:.0f} tokens")
                print(f"   💰 Cost estimate: ~${estimated_tokens * 0.00001:.6f} (approx)")
                
                self.logger.info(f"📊 Estimated tokens: {estimated_tokens:.0f}")
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system", 
                            "content": "তুমি বাংলা ভাষা বিশ্লেষক। ইংরেজি, বাংলিশ, বাংলা বুঝো কিন্তু response বাংলায় দাও।"
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=800,
                    top_p=0.9
                )
                
                llm_response = response.choices[0].message.content.strip()
                self.logger.info(f"✅ Response received ({len(llm_response)} chars)")
                
                # Parse the response
                trending_words = self.parse_llm_response(llm_response)
                
                result = {
                    'raw_response': llm_response,
                    'trending_words': trending_words,
                    'status': 'success',
                    'word_count': len(trending_words)
                }
                
                # Show trending words
                self.logger.info(f"📝 Trending words found ({len(trending_words)}):")
                for i, word in enumerate(trending_words, 1):
                    self.logger.info(f"   {i}. {word}")
                
                return result
                
            except Exception as api_error:
                self.logger.error(f"❌ LLM API call failed: {api_error}")
                return {
                    'raw_response': None,
                    'trending_words': [],
                    'status': 'failed',
                    'error': str(api_error),
                    'word_count': 0
                }
                        
        except ImportError:
            self.logger.error("❌ Groq library not found! Install with: pip install groq")
            return []
        except Exception as e:
            self.logger.error(f"❌ Error calling Groq API: {e}")
            return []
    
    def parse_subreddit_response(self, llm_response: str, subreddit_name: str) -> str:
        """Parse LLM response to extract emerging word for a specific subreddit"""
        if not llm_response:
            return ""
        
        # Look for the emerging word pattern
        lines = llm_response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for pattern like "r/bangladesh emerging word: ..."
            if f"r/{subreddit_name} emerging word:" in line:
                emerging_word = line.split(f"r/{subreddit_name} emerging word:")[-1].strip()
                return emerging_word
            elif "emerging word:" in line:
                emerging_word = line.split("emerging word:")[-1].strip()
                return emerging_word
            # If no specific pattern, take the last meaningful line
            elif len(line) > 1 and not line.startswith(('r/', 'emerging', 'word')):
                return line
        
        # Fallback: return the cleaned response
        clean_response = llm_response.replace(f"r/{subreddit_name}", "").replace("emerging word:", "").strip()
        return clean_response if clean_response else ""
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
    
    def run_comprehensive_analysis(self, posts_per_subreddit: int = 20) -> Dict[str, Any]:
        """
        Main function: Scrape all subreddits and get LLM analysis for each subreddit separately
        
        Args:
            posts_per_subreddit: Number of posts per subreddit
        
        Returns:
            Complete analysis results with one emerging word per subreddit
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'Reddit Subreddit-wise Trending Analysis',
            'scraping_summary': {},
            'subreddit_responses': [],  # List of responses for each subreddit
            'emerging_words': [],  # List of emerging words from each subreddit
            'summary': {
                'total_subreddits': len(self.all_subreddits),
                'successful_subreddits': 0,
                'total_posts': 0,
                'successful_llm_responses': 0,
                'total_emerging_words': 0
            }
        }
        
        self.logger.info(f"🚀 Starting subreddit-wise Reddit trending analysis")
        self.logger.info(f"📊 Subreddits to analyze: {len(self.all_subreddits)}")
        
        try:
            # Step 1: Scrape all subreddits
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"📡 STEP 1: SCRAPING ALL SUBREDDITS")
            self.logger.info(f"{'='*60}")
            
            all_posts = self.scrape_all_subreddits(posts_per_subreddit)
            
            if not all_posts:
                self.logger.error("❌ No posts found from any subreddit!")
                results['summary']['status'] = 'failed'
                results['summary']['error'] = 'No posts found'
                return results
            
            # Update scraping summary
            subreddit_counts = {}
            for post in all_posts:
                subreddit = post.get('subreddit', 'unknown')
                subreddit_counts[subreddit] = subreddit_counts.get(subreddit, 0) + 1
            
            results['scraping_summary'] = {
                'subreddit_post_counts': subreddit_counts,
                'total_posts': len(all_posts),
                'successful_subreddits': len(subreddit_counts)
            }
            
            results['summary']['successful_subreddits'] = len(subreddit_counts)
            results['summary']['total_posts'] = len(all_posts)
            
            # Step 2: Process each subreddit separately
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"🔧 STEP 2: PROCESSING EACH SUBREDDIT SEPARATELY")
            self.logger.info(f"{'='*60}")
            
            successful_responses = 0
            emerging_words = []
            
            for subreddit in self.all_subreddits:
                if subreddit not in subreddit_counts:
                    self.logger.warning(f"⚠️ No posts found for r/{subreddit}, skipping LLM analysis")
                    continue
                
                self.logger.info(f"\n📡 Processing r/{subreddit}...")
                
                # Prepare content for this specific subreddit
                content_text = self.prepare_subreddit_content_for_llm(all_posts, subreddit)
                
                if not content_text:
                    self.logger.warning(f"⚠️ No content prepared for r/{subreddit}")
                    continue
                
                print(f"\n📏 r/{subreddit} CONTENT ANALYSIS:")
                print(f"   📄 Characters: {len(content_text):,}")
                print(f"   📊 Estimated tokens: {len(content_text) // 3.5:.0f}")
                print(f"   📱 Posts: {subreddit_counts.get(subreddit, 0)}")
                
                # Create prompt for this subreddit
                prompt = self.create_subreddit_llm_prompt(content_text, subreddit)
                
                # Get LLM analysis for this subreddit
                self.logger.info(f"🤖 Getting LLM analysis for r/{subreddit}")
                subreddit_response = self.call_groq_llm_for_subreddit_analysis(prompt, subreddit)
                
                # Store the response
                results['subreddit_responses'].append(subreddit_response)
                
                if subreddit_response.get('status') == 'success':
                    successful_responses += 1
                    emerging_word = subreddit_response.get('emerging_word', '')
                    if emerging_word:
                        emerging_words.append({
                            'subreddit': subreddit,
                            'emerging_word': emerging_word
                        })
                        self.logger.info(f"✅ r/{subreddit} emerging word: {emerging_word}")
                    else:
                        self.logger.warning(f"⚠️ No emerging word found for r/{subreddit}")
                else:
                    self.logger.error(f"❌ Failed to get response for r/{subreddit}")
                
                # Small delay between requests
                time.sleep(1)
            
            # Step 3: Finalize results
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"📊 STEP 3: FINALIZING RESULTS")
            self.logger.info(f"{'='*60}")
            
            results['emerging_words'] = emerging_words
            
            # Final summary
            results['summary']['successful_llm_responses'] = successful_responses
            results['summary']['total_emerging_words'] = len(emerging_words)
            results['summary']['status'] = 'success' if emerging_words else 'partial'
            
            self.logger.info(f"✅ Analysis completed!")
            self.logger.info(f"📊 Final Summary:")
            self.logger.info(f"   📡 Successful subreddits: {results['summary']['successful_subreddits']}")
            self.logger.info(f"   📄 Total posts: {results['summary']['total_posts']}")
            self.logger.info(f"   🤖 Successful LLM responses: {results['summary']['successful_llm_responses']}")
            self.logger.info(f"   🔥 Emerging words found: {results['summary']['total_emerging_words']}")
            
            if emerging_words:
                self.logger.info(f"📝 Emerging words by subreddit:")
                for item in emerging_words:
                    self.logger.info(f"   r/{item['subreddit']}: {item['emerging_word']}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error in comprehensive analysis: {e}")
            results['summary']['status'] = 'failed'
            results['summary']['error'] = str(e)
            return results
        """
        Main function: Scrape all subreddits and get comprehensive LLM analysis
        
        Args:
            posts_per_subreddit: Number of posts per subreddit
        
        Returns:
            Complete analysis results
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'Reddit Comprehensive Trending Analysis',
            'scraping_summary': {},
            'llm_response': {},  # Single response instead of list
            'trending_words': [],  # Direct trending words instead of consolidated
            'summary': {
                'total_subreddits': len(self.all_subreddits),
                'successful_subreddits': 0,
                'total_posts': 0,
                'successful_llm_responses': 0,
                'total_trending_words': 0
            }
        }
        
        self.logger.info(f"🚀 Starting comprehensive Reddit trending analysis")
        self.logger.info(f"📊 Subreddits to scrape: {len(self.all_subreddits)}")
        
        try:
            # Step 1: Scrape all subreddits
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"📡 STEP 1: SCRAPING ALL SUBREDDITS")
            self.logger.info(f"{'='*60}")
            
            all_posts = self.scrape_all_subreddits(posts_per_subreddit)
            
            if not all_posts:
                self.logger.error("❌ No posts found from any subreddit!")
                results['summary']['status'] = 'failed'
                results['summary']['error'] = 'No posts found'
                return results
            
            # Update scraping summary
            subreddit_counts = {}
            for post in all_posts:
                subreddit = post.get('subreddit', 'unknown')
                subreddit_counts[subreddit] = subreddit_counts.get(subreddit, 0) + 1
            
            results['scraping_summary'] = {
                'subreddit_post_counts': subreddit_counts,
                'total_posts': len(all_posts),
                'successful_subreddits': len(subreddit_counts)
            }
            
            results['summary']['successful_subreddits'] = len(subreddit_counts)
            results['summary']['total_posts'] = len(all_posts)
            
            # Step 2: Prepare content for LLM
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"🔧 STEP 2: PREPARING CONTENT FOR LLM")
            self.logger.info(f"{'='*60}")
            
            content_text = self.prepare_comprehensive_content_for_llm(all_posts)
            
            if not content_text:
                self.logger.error("❌ No content prepared for LLM!")
                results['summary']['status'] = 'failed'
                results['summary']['error'] = 'No content for LLM'
                return results
            
            # Step 3: Get LLM analysis
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"🤖 STEP 3: GETTING LLM TRENDING ANALYSIS")
            self.logger.info(f"{'='*60}")
            
            prompt = self.create_comprehensive_llm_prompt(content_text)
            llm_response = self.call_groq_llm_for_trending_analysis(prompt)
            
            if not llm_response or llm_response.get('status') != 'success':
                self.logger.error("❌ No LLM response received!")
                results['summary']['status'] = 'failed'
                results['summary']['error'] = 'No LLM response'
                return results
            
            results['llm_response'] = llm_response
            
            # Step 4: Extract trending words
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"📊 STEP 4: EXTRACTING TRENDING WORDS")
            self.logger.info(f"{'='*60}")
            
            trending_words = llm_response.get('trending_words', [])
            
            if trending_words:
                results['trending_words'] = trending_words
                
                self.logger.info(f"✅ Found {len(trending_words)} trending words:")
                for i, word in enumerate(trending_words, 1):
                    self.logger.info(f"   {i}. {word}")
            else:
                self.logger.warning("⚠️ No trending words extracted from LLM response")
                results['trending_words'] = []
            
            # Final summary
            results['summary']['successful_llm_responses'] = 1 if llm_response.get('status') == 'success' else 0
            results['summary']['total_trending_words'] = len(trending_words)
            results['summary']['status'] = 'success'
            
            self.logger.info(f"✅ Analysis completed successfully!")
            self.logger.info(f"📊 Final Summary:")
            self.logger.info(f"   📡 Successful subreddits: {results['summary']['successful_subreddits']}")
            self.logger.info(f"   📄 Total posts: {results['summary']['total_posts']}")
            self.logger.info(f"   🤖 Successful LLM responses: {results['summary']['successful_llm_responses']}")
            self.logger.info(f"   🔥 Unique trending words: {results['summary']['total_trending_words']}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error in comprehensive analysis: {e}")
            results['summary']['status'] = 'failed'
            results['summary']['error'] = str(e)
            return results
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """Save analysis results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reddit_subreddit_trending_analysis_{timestamp}.json"
        
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
        print(f"\n{'='*80}")
        print(f"🏆 REDDIT SUBREDDIT-WISE TRENDING ANALYSIS RESULTS")
        print(f"{'='*80}")
        
        # Scraping summary
        scraping = results.get('scraping_summary', {})
        if scraping:
            print(f"\n📡 SCRAPING SUMMARY:")
            print(f"   Successful subreddits: {scraping.get('successful_subreddits', 0)}")
            print(f"   Total posts: {scraping.get('total_posts', 0)}")
            
            subreddit_counts = scraping.get('subreddit_post_counts', {})
            if subreddit_counts:
                print(f"   Posts per subreddit:")
                for subreddit, count in sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"     r/{subreddit}: {count} posts")
        
        # Subreddit responses summary
        subreddit_responses = results.get('subreddit_responses', [])
        if subreddit_responses:
            print(f"\n🤖 SUBREDDIT LLM RESPONSES:")
            successful = len([r for r in subreddit_responses if r.get('status') == 'success'])
            print(f"   Successful responses: {successful}/{len(subreddit_responses)}")
        
        # Emerging words
        emerging_words = results.get('emerging_words', [])
        if emerging_words:
            print(f"\n🔥 EMERGING WORDS BY SUBREDDIT:")
            for i, item in enumerate(emerging_words, 1):
                print(f"   {i}. r/{item['subreddit']}: {item['emerging_word']}")
        else:
            print(f"\n🔥 EMERGING WORDS:")
            print(f"   No emerging words found")
        
        # Summary
        summary = results.get('summary', {})
        print(f"\n{'-'*80}")
        print(f"📈 OVERALL SUMMARY:")
        print(f"   Status: {summary.get('status', 'unknown')}")
        print(f"   Subreddits: {summary.get('successful_subreddits', 0)}/{summary.get('total_subreddits', 0)}")
        print(f"   Posts: {summary.get('total_posts', 0)}")
        print(f"   LLM Responses: {summary.get('successful_llm_responses', 0)}")
        print(f"   Emerging Words: {summary.get('total_emerging_words', 0)}")
        print(f"{'='*80}")


def main():
    """Main function to run subreddit-wise Reddit analysis"""
    try:
        print(f"🚀 REDDIT SUBREDDIT-WISE TRENDING ANALYSIS")
        print(f"{'='*60}")
        print(f"📊 Approach: Each subreddit → Separate LLM analysis → One emerging word per subreddit")
        print(f"🎯 Goal: Get one emerging word from each subreddit")
        print(f"{'='*60}")
        
        # Create scraper
        scraper = RedditDataScrapper()
        
        # Run subreddit-wise analysis with 20 posts per subreddit and 8 comments per post
        results = scraper.run_comprehensive_analysis(posts_per_subreddit=20)
        
        # Save results
        filename = scraper.save_results(results)
        
        # Display summary
        scraper.display_results_summary(results)
        
        if results.get('summary', {}).get('status') in ['success', 'partial']:
            print(f"\n🎉 Analysis complete! Results saved to: {filename}")
            
            # Show final emerging words by subreddit
            emerging_words = results.get('emerging_words', [])
            if emerging_words:
                print(f"\n🔥 FINAL EMERGING WORDS BY SUBREDDIT:")
                for i, item in enumerate(emerging_words, 1):
                    print(f"   {i}. r/{item['subreddit']}: {item['emerging_word']}")
            else:
                print(f"\n⚠️ No emerging words found")
        else:
            print(f"\n❌ Analysis failed: {results.get('summary', {}).get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ Error running analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
