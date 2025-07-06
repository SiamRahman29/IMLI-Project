#!/usr/bin/env python3
"""
Reddit Flair-wise Trending Analysis
Process each Reddit flair separately to get 1-2 trending topics per flair
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

class RedditFlairTrendingAnalyzer:
    """Analyze trending topics for each Reddit flair separately"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 3  # 3 seconds between LLM calls to avoid rate limit
        
    def prepare_flair_content_for_llm(self, posts: List[Dict[str, Any]], max_posts: int = 20) -> str:
        """Prepare content from posts of a specific flair for LLM analysis"""
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
            
            # No limit on content - use full content
            if content and len(content) > 10:
                post_parts.append(f"Content: {content}")
            
            # Add top 10 comments per post (as requested)
            if comments:
                top_comments = comments[:10]  # Top 10 comments
                comment_texts = []
                for comment in top_comments:
                    if comment and len(comment.strip()) > 5:
                        comment_texts.append(comment)
                
                if comment_texts:
                    post_parts.append(f"Comments: {' | '.join(comment_texts)}")
            
            # Add score info
            score = post.get('score', 0)
            post_parts.append(f"Engagement: {score} upvotes")
            
            combined_texts.append(f"Post {i}:\n" + "\n".join(post_parts))
        
        final_text = "\n\n---\n\n".join(combined_texts)
        return final_text
    
    def create_flair_trending_prompt(self, flair_name: str, content_text: str) -> str:
        """Create LLM prompt for a specific flair's trending analysis"""
        
        # Map flair to Bengali context
        flair_context = {
            'discussion': 'আলোচনা ও সাধারণ বিষয়াবলী',
            'askdesh': 'দেশ সম্পর্কিত প্রশ্ন ও জিজ্ঞাসা',
            'education': 'শিক্ষা ও একাডেমিক বিষয়াবলী',
            'politics': 'রাজনীতি ও রাজনৈতিক বিষয়াবলী',
            'technology': 'বিজ্ঞান ও প্রযুক্তি',
            'environment': 'পরিবেশ ও প্রকৃতি',
            'events': 'ঘটনা ও সংবাদ',
            'history': 'ইতিহাস ও ঐতিহ্য',
            'seeking_advice': 'পরামর্শ ও সাহায্য'
        }
        
        context = flair_context.get(flair_name, flair_name)
        
        prompt = f"""
তুমি একজন বিশেষজ্ঞ বাংলাদেশি সোশ্যাল মিডিয়া ট্রেন্ড বিশ্লেষক। নিচে Reddit এর "{flair_name}" ফ্লেয়ারের ({context}) পোস্টগুলো দেওয়া হয়েছে।

**তোমার কাজ:**
এই নির্দিষ্ট ফ্লেয়ারের পোস্টগুলো বিশ্লেষণ করে **শুধুমাত্র ২টি** সবচেয়ে জনপ্রিয় ও ট্রেন্ডিং বিষয় খুঁজে বের করো।

**নিয়মাবলী:**
1. **শুধুমাত্র ২টি**: অবশ্যই ২টির বেশি দিও না
2. **বাংলা ভাষায়**: সব response বাংলায় হতে হবে
3. **সংক্ষিপ্ত**: প্রতিটি টপিক ২-৪ শব্দের মধ্যে
4. **প্রাসঙ্গিক**: এই ফ্লেয়ারের context অনুযায়ী relevant হতে হবে
5. **জনপ্রিয়তা**: যে বিষয়গুলো সবচেয়ে বেশি আলোচিত হচ্ছে
6. **Stop words নয়**: সাধারণ শব্দ (এই, সেই, করা, হওয়া) এড়িয়ে চলো

**Reddit Posts থেকে বিশ্লেষণ করো:**
{content_text}

**আউটপুট ফরম্যাট:**
{flair_name} ফ্লেয়ার ট্রেন্ডিং (২টি):
১. [বাংলা ট্রেন্ডিং টপিক]
২. [বাংলা ট্রেন্ডিং টপিক]
"""
        
        return prompt
    
    def call_llm_for_flair_analysis(self, flair_name: str, prompt: str) -> Optional[List[str]]:
        """Call LLM for a specific flair analysis"""
        try:
            from groq import Groq
            
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                self.logger.error("❌ GROQ_API_KEY not found!")
                return None
            
            client = Groq(api_key=api_key)
            
            self.logger.info(f"🤖 Analyzing flair: {flair_name}")
            
            # Call LLM with smaller token limit for faster response
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "তুমি একজন বিশেষজ্ঞ বাংলা ভাষা বিশ্লেষক। তুমি সংক্ষিপ্ত ও নির্ভুল ট্রেন্ডিং টপিক চিহ্নিত করতে পারো।"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=300,  # Small token limit for 2 topics only
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
                    clean_line = clean_line.replace(f'{flair_name} ফ্লেয়ার ট্রেন্ডিং (২টি):', '').strip()
                    clean_line = clean_line.replace('ফ্লেয়ার ট্রেন্ডিং (২টি):', '').strip()
                    
                    if clean_line and len(clean_line) > 1 and not clean_line.endswith(':'):
                        trending_topics.append(clean_line)
            
            # Limit to exactly 2 topics
            trending_topics = trending_topics[:2]
            
            self.logger.info(f"✅ Found {len(trending_topics)} topics for {flair_name}")
            return trending_topics
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing {flair_name}: {e}")
            return None
    
    def analyze_flair_wise_trending(self, categorized_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze trending topics for each flair separately with individual LLM requests"""
        self.logger.info("🚀 Starting flair-wise trending analysis...")
        
        results = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'flair_analysis': {},
            'total_flairs_processed': 0,
            'total_topics_found': 0,
            'individual_flair_results': {}
        }
        
        processed_flairs = 0
        total_topics = 0
        
        # Process each flair individually
        for flair_name, posts in categorized_data.items():
            if flair_name == 'uncategorized' or not posts:
                self.logger.info(f"⏭️ Skipping {flair_name}: {'uncategorized' if flair_name == 'uncategorized' else 'no posts'}")
                continue
            
            self.logger.info(f"📊 Processing flair: {flair_name} ({len(posts)} posts)")
            
            # Initialize individual flair result
            individual_result = {
                'flair_name': flair_name,
                'posts_count': len(posts),
                'success': False,
                'trending_topics': [],
                'error': None,
                'processed_at': datetime.now().isoformat()
            }
            
            try:
                # Step 1: Prepare content for this specific flair
                content_text = self.prepare_flair_content_for_llm(posts)
                
                if not content_text:
                    individual_result['error'] = 'No content available for analysis'
                    self.logger.warning(f"⚠️ No content for flair: {flair_name}")
                    results['individual_flair_results'][flair_name] = individual_result
                    continue
                
                # Step 2: Create LLM prompt for this specific flair
                prompt = self.create_flair_trending_prompt(flair_name, content_text)
                
                # Step 3: Rate limiting between requests
                if processed_flairs > 0:
                    self.logger.info(f"⏳ Rate limit delay: {self.rate_limit_delay}s before processing {flair_name}")
                    time.sleep(self.rate_limit_delay)
                
                # Step 4: Call LLM for this specific flair
                self.logger.info(f"🤖 Sending individual LLM request for flair: {flair_name}")
                trending_topics = self.call_llm_for_flair_analysis(flair_name, prompt)
                
                # Step 5: Handle response for this flair
                if trending_topics and len(trending_topics) > 0:
                    individual_result['success'] = True
                    individual_result['trending_topics'] = trending_topics
                    individual_result['topics_count'] = len(trending_topics)
                    
                    # Add to main results
                    results['flair_analysis'][flair_name] = {
                        'posts_count': len(posts),
                        'trending_topics': trending_topics,
                        'topics_count': len(trending_topics),
                        'success': True
                    }
                    
                    total_topics += len(trending_topics)
                    self.logger.info(f"✅ {flair_name} SUCCESS: {trending_topics}")
                    
                else:
                    individual_result['error'] = 'LLM failed to generate trending topics'
                    results['flair_analysis'][flair_name] = {
                        'posts_count': len(posts),
                        'trending_topics': [],
                        'topics_count': 0,
                        'success': False,
                        'error': 'LLM analysis failed'
                    }
                    self.logger.error(f"❌ {flair_name} FAILED: No topics generated")
                
            except Exception as e:
                individual_result['error'] = f'Exception occurred: {str(e)}'
                results['flair_analysis'][flair_name] = {
                    'posts_count': len(posts),
                    'trending_topics': [],
                    'topics_count': 0,
                    'success': False,
                    'error': str(e)
                }
                self.logger.error(f"❌ {flair_name} EXCEPTION: {e}")
            
            # Store individual result regardless of success/failure
            results['individual_flair_results'][flair_name] = individual_result
            processed_flairs += 1
            
            self.logger.info(f"🔄 Completed {processed_flairs}/{len([k for k, v in categorized_data.items() if k != 'uncategorized' and v])} flairs")
        
        # Update final summary
        results['total_flairs_processed'] = processed_flairs
        results['total_topics_found'] = total_topics
        
        successful_flairs = len([f for f in results['individual_flair_results'].values() if f['success']])
        
        if processed_flairs == 0:
            results['success'] = False
            results['message'] = 'No flairs could be processed'
        else:
            results['message'] = f'Processed {processed_flairs} flairs individually. {successful_flairs} successful, {total_topics} topics found'
        
        self.logger.info(f"🎉 Individual flair analysis completed: {processed_flairs} processed, {successful_flairs} successful, {total_topics} topics")
        
        return results
    
    def save_flair_analysis_results(self, results: Dict[str, Any]) -> str:
        """Save flair analysis results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reddit_flair_trending_analysis_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 Results saved to: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"❌ Error saving results: {e}")
            return ""

# Helper function for pipeline integration
def analyze_reddit_flair_trending(categorized_reddit_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Main function to be called from pipeline
    Analyzes trending topics for each Reddit flair separately
    """
    analyzer = RedditFlairTrendingAnalyzer()
    return analyzer.analyze_flair_wise_trending(categorized_reddit_data)

if __name__ == "__main__":
    # Test the flair-wise trending analysis
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Load test data
    try:
        import sys
        sys.path.insert(0, '.')
        from app.services.reddit_integration import RedditIntegration
        
        reddit_integration = RedditIntegration()
        result = reddit_integration.process_reddit_data_for_pipeline()
        
        if result['success']:
            categorized_data = result['data']
            
            # Analyze flair-wise trending
            analyzer = RedditFlairTrendingAnalyzer()
            flair_results = analyzer.analyze_flair_wise_trending(categorized_data)
            
            # Save results
            filename = analyzer.save_flair_analysis_results(flair_results)
            
            # Display summary
            print("\n🔥 Reddit Flair-wise Trending Analysis Results:")
            print("=" * 60)
            print(f"Success: {flair_results['success']}")
            print(f"Message: {flair_results['message']}")
            print(f"Flairs Processed: {flair_results['total_flairs_processed']}")
            print(f"Total Topics Found: {flair_results['total_topics_found']}")
            
            print(f"\n📊 Trending Topics by Flair:")
            print("-" * 40)
            
            for flair, analysis in flair_results['flair_analysis'].items():
                print(f"\n🏷️ {flair.upper()} ({analysis['posts_count']} posts):")
                if analysis['trending_topics']:
                    for i, topic in enumerate(analysis['trending_topics'], 1):
                        print(f"   {i}. {topic}")
                else:
                    print(f"   ❌ No topics found")
        else:
            print("❌ Failed to load Reddit data")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
