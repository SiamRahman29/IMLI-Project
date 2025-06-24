#!/usr/bin/env python3
"""
Reddit Subreddit-wise Trending Analysis
Process each Reddit subreddit separately to get 2 trending topics per subreddit
Better approach than flair-wise as each subreddit has its own theme and more content
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RedditSubredditTrendingAnalyzer:
    """Analyze trending topics for each Reddit subreddit separately"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 3  # 3 seconds between LLM calls to avoid rate limit
        
        # Subreddit to Bengali category mapping
        self.subreddit_categories = {
            # Main Bangladesh subreddit - General discussions
            'bangladesh': {
                'category': 'সাধারণ আলোচনা',
                'description': 'বাংলাদেশের সাধারণ বিষয়াবলী ও আলোচনা',
                'context': 'বাংলাদেশের যেকোনো বিষয়ে আলোচনা, সংবাদ, মতামত'
            },
            
            # City-specific subreddits - Local issues and discussions  
            'dhaka': {
                'category': 'ঢাকা শহর',
                'description': 'ঢাকা শহরের স্থানীয় বিষয়াবলী',
                'context': 'ঢাকার যাতায়াত, জীবনযাত্রা, স্থানীয় সমস্যা ও সুবিধা'
            },
            'chittagong': {
                'category': 'চট্টগ্রাম শহর', 
                'description': 'চট্টগ্রাম শহরের স্থানীয় বিষয়াবলী',
                'context': 'চট্টগ্রামের ব্যবসা-বাণিজ্য, বন্দর, স্থানীয় সংস্কৃতি'
            },
            'sylhet': {
                'category': 'সিলেট অঞ্চল',
                'description': 'সিলেট অঞ্চলের বিষয়াবলী', 
                'context': 'সিলেটের চা বাগান, প্রবাসী সম্প্রদায়, স্থানীয় সংস্কৃতি'
            },
            
            # Politics subreddit - Political discussions
            'bangladeshpolitics': {
                'category': 'রাজনীতি',
                'description': 'বাংলাদেশের রাজনৈতিক বিষয়াবলী',
                'context': 'রাজনৈতিক দল, নীতি, নির্বাচন, সরকারি কার্যক্রম'
            },
            
            # University subreddits - Education and student life
            'buet': {
                'category': 'প্রকৌশল শিক্ষা',
                'description': 'বুয়েট ও প্রকৌশল শিক্ষা',
                'context': 'ইঞ্জিনিয়ারিং, প্রযুক্তি, গবেষণা, ক্যারিয়ার'
            },
            'nsu': {
                'category': 'বিশ্ববিদ্যালয় জীবন',
                'description': 'বিশ্ববিদ্যালয়ের শিক্ষার্থী জীবন',
                'context': 'উচ্চশিক্ষা, ক্যাম্পাস জীবন, ক্যারিয়ার পরিকল্পনা'
            },
            
            # Backup subreddits (if used)
            'bengalimemes': {
                'category': 'বিনোদন ও হাস্যরস',
                'description': 'বাঙালি সংস্কৃতি ও হাস্যরস',
                'context': 'মিমস, হাস্যরস, সাংস্কৃতিক রেফারেন্স'
            },
            'southasia': {
                'category': 'দক্ষিণ এশিয়া',
                'description': 'দক্ষিণ এশিয়ার আঞ্চলিক বিষয়াবলী', 
                'context': 'আঞ্চলিক রাজনীতি, সংস্কৃতি, অর্থনীতি'
            }
        }
    
    def categorize_posts_by_subreddit(self, posts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize Reddit posts by subreddit"""
        categorized_data = {}
        
        # Initialize categories for known subreddits
        for subreddit in self.subreddit_categories.keys():
            categorized_data[subreddit] = []
        
        # Add uncategorized for unknown subreddits
        categorized_data['uncategorized'] = []
        
        for post in posts:
            # Extract subreddit name from source
            source = post.get('source', '')
            subreddit_name = None
            
            # Parse subreddit name from source (format: reddit_r_subredditname)
            if source.startswith('reddit_r_'):
                subreddit_name = source.replace('reddit_r_', '')
            
            # Categorize by subreddit
            if subreddit_name and subreddit_name in self.subreddit_categories:
                categorized_data[subreddit_name].append(post)
            else:
                categorized_data['uncategorized'].append(post)
        
        # Remove empty categories
        categorized_data = {k: v for k, v in categorized_data.items() if v}
        
        self.logger.info(f"📊 Subreddit categorization complete:")
        for subreddit, posts_list in categorized_data.items():
            if subreddit != 'uncategorized':
                category_info = self.subreddit_categories.get(subreddit, {})
                category_name = category_info.get('category', subreddit)
                self.logger.info(f"   ✅ {subreddit} ({category_name}): {len(posts_list)} posts")
            else:
                self.logger.info(f"   ⚪ {subreddit}: {len(posts_list)} posts")
        
        return categorized_data
    
    def prepare_subreddit_content_for_llm(self, posts: List[Dict[str, Any]], max_posts: int = 15) -> str:
        """Prepare content from posts of a specific subreddit for LLM analysis"""
        if not posts:
            return ""
        
        # Sort by engagement (score + comments)
        sorted_posts = sorted(posts, key=lambda x: x.get('score', 0) + x.get('comments_count', 0), reverse=True)
        
        # Take top posts to stay within token limits
        top_posts = sorted_posts[:max_posts]
        
        combined_texts = []
        for i, post in enumerate(top_posts, 1):
            title = post.get('title', '').strip()
            content = post.get('content', '').strip()
            comments = post.get('comments', [])
            
            # Build post text
            post_parts = []
            if title:
                post_parts.append(f"Title: {title}")
            
            # Use full content (no limits as requested)
            if content and len(content) > 10:
                post_parts.append(f"Content: {content}")
            
            # Add top 10 comments per post
            if comments:
                top_comments = comments[:10]  # Top 10 comments
                comment_texts = []
                for comment in top_comments:
                    if comment and len(comment.strip()) > 5:
                        comment_texts.append(comment)
                
                if comment_texts:
                    post_parts.append(f"Comments: {' | '.join(comment_texts)}")
            
            # Add engagement info
            score = post.get('score', 0)
            comments_count = post.get('comments_count', 0)
            post_parts.append(f"Engagement: {score} upvotes, {comments_count} comments")
            
            combined_texts.append(f"Post {i}:\n" + "\n".join(post_parts))
        
        final_text = "\n\n---\n\n".join(combined_texts)
        return final_text
    
    def create_subreddit_trending_prompt(self, subreddit: str, content_text: str) -> str:
        """Create LLM prompt for a specific subreddit's trending analysis"""
        
        subreddit_info = self.subreddit_categories.get(subreddit, {
            'category': subreddit,
            'description': f'{subreddit} subreddit',
            'context': f'{subreddit} এর বিষয়াবলী'
        })
        
        category = subreddit_info['category']
        description = subreddit_info['description'] 
        context = subreddit_info['context']
        
        prompt = f"""
তুমি একজন বিশেষজ্ঞ বাংলাদেশি সোশ্যাল মিডিয়া ট্রেন্ড বিশ্লেষক। নিচে Reddit এর "r/{subreddit}" সাবরেডিটের পোস্টগুলো দেওয়া হয়েছে।

**সাবরেডিট তথ্য:**
- সাবরেডিট: r/{subreddit}
- ক্যাটেগরি: {category}
- বিবরণ: {description}
- প্রসঙ্গ: {context}

**তোমার কাজ:**
এই সাবরেডিটের পোস্টগুলো বিশ্লেষণ করে **শুধুমাত্র ২টি** সবচেয়ে জনপ্রিয় ও ট্রেন্ডিং বিষয় খুঁজে বের করো।

**নিয়মাবলী:**
1. **শুধুমাত্র ২টি**: অবশ্যই ২টির বেশি দিও না
2. **বাংলা ভাষায়**: সব response বাংলায় হতে হবে  
3. **সংক্ষিপ্ত**: প্রতিটি টপিক ২-৪ শব্দের মধ্যে
4. **প্রাসঙ্গিক**: এই সাবরেডিটের থিম অনুযায়ী relevant হতে হবে
5. **জনপ্রিয়তা**: যে বিষয়গুলো সবচেয়ে বেশি আলোচিত হচ্ছে
6. **Stop words এড়ানো**: সাধারণ শব্দ (এই, সেই, করা, হওয়া) এড়িয়ে চলো

**Reddit Posts (r/{subreddit}) থেকে বিশ্লেষণ করো:**
{content_text}

**আউটপুট ফরম্যাট:**
r/{subreddit} ট্রেন্ডিং (২টি):
১. [বাংলা ট্রেন্ডিং টপিক]
২. [বাংলা ট্রেন্ডিং টপিক]
"""
        
        return prompt
    
    def call_llm_for_subreddit_analysis(self, subreddit: str, prompt: str) -> Optional[List[str]]:
        """Call LLM for a specific subreddit analysis"""
        try:
            from groq import Groq
            
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                self.logger.error("❌ GROQ_API_KEY not found!")
                return None
            
            client = Groq(api_key=api_key)
            
            self.logger.info(f"🤖 Analyzing subreddit: r/{subreddit}")
            
            # Call LLM with appropriate token limit
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "তুমি একজন বিশেষজ্ঞ বাংলা ভাষা বিশ্লেষক। তুমি Reddit এর বিভিন্ন সাবরেডিট থেকে সংক্ষিপ্ত ও নির্ভুল ট্রেন্ডিং টপিক চিহ্নিত করতে পারো।"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=400,  # Slightly higher for subreddit analysis
                top_p=0.9
            )
            
            llm_response = response.choices[0].message.content.strip()
            
            # Parse response to extract 2 topics
            trending_topics = []
            lines = llm_response.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for numbered items (Bengali or English numbers)
                if any(char in line for char in ['১', '২']) or line.startswith(('1.', '2.')):
                    # Remove numbering and common prefixes
                    clean_line = line
                    for num in ['১.', '২.', '1.', '2.']:
                        clean_line = clean_line.replace(num, '').strip()
                    
                    # Remove common response format artifacts
                    clean_line = clean_line.replace(f'r/{subreddit} ট্রেন্ডিং (২টি):', '').strip()
                    clean_line = clean_line.replace('ট্রেন্ডিং (২টি):', '').strip()
                    
                    if clean_line and len(clean_line) > 1 and not clean_line.endswith(':'):
                        trending_topics.append(clean_line)
            
            # Limit to exactly 2 topics
            trending_topics = trending_topics[:2]
            
            self.logger.info(f"✅ Found {len(trending_topics)} topics for r/{subreddit}")
            return trending_topics
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing r/{subreddit}: {e}")
            return None
    
    def analyze_subreddit_wise_trending(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trending topics for each subreddit separately with individual LLM requests"""
        self.logger.info("🚀 Starting subreddit-wise trending analysis...")
        
        # First categorize posts by subreddit
        categorized_data = self.categorize_posts_by_subreddit(posts)
        
        results = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'approach': 'subreddit_wise',
            'subreddit_analysis': {},
            'total_subreddits_processed': 0,
            'total_topics_found': 0,
            'individual_subreddit_results': {}
        }
        
        processed_subreddits = 0
        total_topics = 0
        
        # Process each subreddit individually
        for subreddit, posts_list in categorized_data.items():
            if subreddit == 'uncategorized' or not posts_list:
                self.logger.info(f"⏭️ Skipping {subreddit}: {'uncategorized' if subreddit == 'uncategorized' else 'no posts'}")
                continue
            
            subreddit_info = self.subreddit_categories.get(subreddit, {})
            category_name = subreddit_info.get('category', subreddit)
            
            self.logger.info(f"📊 Processing r/{subreddit} ({category_name}): {len(posts_list)} posts")
            
            # Initialize individual subreddit result
            individual_result = {
                'subreddit': subreddit,
                'category': category_name,
                'posts_count': len(posts_list),
                'success': False,
                'trending_topics': [],
                'error': None,
                'processed_at': datetime.now().isoformat()
            }
            
            try:
                # Step 1: Prepare content for this specific subreddit
                content_text = self.prepare_subreddit_content_for_llm(posts_list)
                
                if not content_text:
                    individual_result['error'] = 'No content available for analysis'
                    self.logger.warning(f"⚠️ No content for r/{subreddit}")
                    results['individual_subreddit_results'][subreddit] = individual_result
                    continue
                
                # Step 2: Create LLM prompt for this specific subreddit
                prompt = self.create_subreddit_trending_prompt(subreddit, content_text)
                
                # Step 3: Rate limiting between requests
                if processed_subreddits > 0:
                    self.logger.info(f"⏳ Rate limit delay: {self.rate_limit_delay}s before processing r/{subreddit}")
                    time.sleep(self.rate_limit_delay)
                
                # Step 4: Call LLM for this specific subreddit
                self.logger.info(f"🤖 Sending individual LLM request for r/{subreddit}")
                trending_topics = self.call_llm_for_subreddit_analysis(subreddit, prompt)
                
                # Step 5: Handle response for this subreddit
                if trending_topics and len(trending_topics) > 0:
                    individual_result['success'] = True
                    individual_result['trending_topics'] = trending_topics
                    individual_result['topics_count'] = len(trending_topics)
                    
                    # Add to main results
                    results['subreddit_analysis'][subreddit] = {
                        'category': category_name,
                        'posts_count': len(posts_list),
                        'trending_topics': trending_topics,
                        'topics_count': len(trending_topics),
                        'success': True
                    }
                    
                    total_topics += len(trending_topics)
                    self.logger.info(f"✅ r/{subreddit} SUCCESS: {trending_topics}")
                    
                else:
                    individual_result['error'] = 'LLM failed to generate trending topics'
                    results['subreddit_analysis'][subreddit] = {
                        'category': category_name,
                        'posts_count': len(posts_list),
                        'trending_topics': [],
                        'topics_count': 0,
                        'success': False,
                        'error': 'LLM analysis failed'
                    }
                    self.logger.error(f"❌ r/{subreddit} FAILED: No topics generated")
                
            except Exception as e:
                individual_result['error'] = f'Exception occurred: {str(e)}'
                results['subreddit_analysis'][subreddit] = {
                    'category': category_name,
                    'posts_count': len(posts_list),
                    'trending_topics': [],
                    'topics_count': 0,
                    'success': False,
                    'error': str(e)
                }
                self.logger.error(f"❌ r/{subreddit} EXCEPTION: {e}")
            
            # Store individual result regardless of success/failure
            results['individual_subreddit_results'][subreddit] = individual_result
            processed_subreddits += 1
            
            self.logger.info(f"🔄 Completed {processed_subreddits}/{len([k for k, v in categorized_data.items() if k != 'uncategorized' and v])} subreddits")
        
        # Update final summary
        results['total_subreddits_processed'] = processed_subreddits
        results['total_topics_found'] = total_topics
        
        successful_subreddits = len([s for s in results['individual_subreddit_results'].values() if s['success']])
        
        if processed_subreddits == 0:
            results['success'] = False
            results['message'] = 'No subreddits could be processed'
        else:
            results['message'] = f'Processed {processed_subreddits} subreddits individually. {successful_subreddits} successful, {total_topics} topics found'
        
        self.logger.info(f"🎉 Subreddit-wise analysis completed: {processed_subreddits} processed, {successful_subreddits} successful, {total_topics} topics")
        
        return results
    
    def save_subreddit_analysis_results(self, results: Dict[str, Any]) -> str:
        """Save subreddit analysis results to file"""
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

# Helper function for pipeline integration
def analyze_reddit_subreddit_trending(reddit_posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main function to be called from pipeline
    Analyzes trending topics for each Reddit subreddit separately
    """
    analyzer = RedditSubredditTrendingAnalyzer()
    return analyzer.analyze_subreddit_wise_trending(reddit_posts)

if __name__ == "__main__":
    # Test the subreddit-wise trending analysis
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Load test data
    try:
        import sys
        sys.path.insert(0, '.')
        from app.services.reddit_integration import RedditIntegration
        
        reddit_integration = RedditIntegration()
        result = reddit_integration.process_reddit_data_for_pipeline()
        
        if result['success']:
            reddit_posts = result['posts']  # Use posts directly, not categorized data
            
            # Analyze subreddit-wise trending
            analyzer = RedditSubredditTrendingAnalyzer()
            subreddit_results = analyzer.analyze_subreddit_wise_trending(reddit_posts)
            
            # Save results
            filename = analyzer.save_subreddit_analysis_results(subreddit_results)
            
            # Display summary
            print("\n🔥 Reddit Subreddit-wise Trending Analysis Results:")
            print("=" * 60)
            print(f"Success: {subreddit_results['success']}")
            print(f"Message: {subreddit_results['message']}")
            print(f"Subreddits Processed: {subreddit_results['total_subreddits_processed']}")
            print(f"Total Topics Found: {subreddit_results['total_topics_found']}")
            
            print(f"\n📊 Trending Topics by Subreddit:")
            print("-" * 40)
            
            for subreddit, analysis in subreddit_results['subreddit_analysis'].items():
                print(f"\n🏷️ r/{subreddit.upper()} - {analysis['category']} ({analysis['posts_count']} posts):")
                if analysis['trending_topics']:
                    for i, topic in enumerate(analysis['trending_topics'], 1):
                        print(f"   {i}. {topic}")
                else:
                    print(f"   ❌ No topics found")
        else:
            print("❌ Failed to load Reddit data")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
