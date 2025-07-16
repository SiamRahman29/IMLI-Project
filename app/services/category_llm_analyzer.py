#!/usr/bin/env python3
"""
Category-wise LLM Trending Word Extractor using Groq API
"""

import os
import json
import re
import traceback
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Import the clean_heading_text function from helpers
import sys
sys.path.append('/home/bs01127/IMLI-Project')
from app.routes.helpers import clean_heading_text, NEWSPAPER_STOPWORDS

load_dotenv()

class CategoryLLMAnalyzer:
    """LLM-based analyzer for extracting trending words from category-specific articles"""
    
    def __init__(self):
        """Initialize the LLM analyzer with Groq client"""
        self.groq_api_key = os.getenv('GROQ_API_KEY_NEWSPAPER')
        self.model = "llama-3.3-70b-versatile"
        self.client = None
        
        if not self.groq_api_key:
            print("❌ GROQ_API_KEY_NEWSPAPER not found in environment variables!")
            raise ValueError("GROQ_API_KEY_NEWSPAPER is required")

        try:
            from groq import Groq
            self.client = Groq(api_key=self.groq_api_key)
            print("✅ Groq client initialized successfully")
        except ImportError:
            print("❌ Groq library not found! Install with: pip install groq")
            raise
    
    def extract_trending_words_for_category(self, category: str, articles: List[Dict]) -> List[str]:
        """
        Extract trending words for a specific category using LLM
        
        Args:
            category: Category name in Bengali
            articles: List of articles for this category
            
        Returns:
            List of trending words/phrases for this category
        """
        if not articles:
            print(f"⚠️ No articles found for category: {category}")
            return []
        
        print(f"🤖 Extracting trending words for category: {category} ({len(articles)} articles)")
        
        # Prepare content from articles
        content_text = self._prepare_content_from_articles(articles)
        
        # Create category-specific prompt
        prompt = self._create_category_prompt(category, content_text)
        
        # Call LLM
        try:
            trending_words = self._call_groq_llm(prompt)
            print(f"✅ Extracted {len(trending_words)} trending words for {category}")
            return trending_words
        except Exception as e:
            print(f"❌ Error extracting trending words for {category}: {e}")
            return []
    
    def _prepare_content_from_articles(self, articles: List[Dict]) -> str:
        """Prepare text content from articles for LLM analysis with stopword filtering"""
        content_pieces = []
        
        for article in articles:
            # Extract title and headings
            title = article.get('title', '').strip()
            headings = article.get('headings', [])
            
            if title:
                # Apply stopword filtering to title
                cleaned_title = clean_heading_text(title)
                if cleaned_title:
                    content_pieces.append(f"শিরোনাম: {cleaned_title}")
            
            if headings:
                # Take all headings
                for heading in headings:
                    if heading and heading.strip():
                        # Apply stopword filtering to heading
                        cleaned_heading = clean_heading_text(heading.strip())
                        if cleaned_heading:
                            content_pieces.append(f"সংবাদ: {cleaned_heading}")
        
        # Combine all content
        combined_content = "\n".join(content_pieces)
        
        # Limit content length to avoid token limits (approximately 8000 characters)
        if len(combined_content) > 8000:
            combined_content = combined_content[:8000] + "..."
        
        return combined_content
    
    def _create_category_prompt(self, category: str, content_text: str) -> str:
        """Create category-specific prompt for LLM"""
        
        # Category-specific instructions
        category_instructions = {
            'জাতীয়': 'জাতীয় সংবাদ, দেশের গুরুত্বপূর্ণ ঘটনা, সরকারি নীতি ও সিদ্ধান্ত',
            'আন্তর্জাতিক': 'আন্তর্জাতিক সংবাদ, বৈশ্বিক ঘটনা, বিদেশি নীতি ও সম্পর্ক',
            'অর্থনীতি': 'অর্থনৈতিক সংবাদ, ব্যবসা-বাণিজ্য, বাজার, মুদ্রা, ব্যাংকিং',
            'রাজনীতি': 'রাজনৈতিক ঘটনা, নেতাদের বক্তব্য, দলীয় কার্যক্রম, নির্বাচন',
            'লাইফস্টাইল': 'জীবনযাত্রা, স্বাস্থ্য টিপস, ফ্যাশন, খাবার-দাবার',
            'বিনোদন': 'চলচ্চিত্র, সংগীত, টেলিভিশন, বিনোদন শিল্প',
            'খেলাধুলা': 'ক্রিকেট, ফুটবল, অন্যান্য খেলা, খেলোয়াড়দের খবর',
            'ধর্ম': 'ধর্মীয় বিষয়াবলী, ইসলামিক শিক্ষা, ধর্মীয় অনুষ্ঠান',
            'চাকরি': 'চাকরির সুযোগ, নিয়োগ বিজ্ঞপ্তি, ক্যারিয়ার গাইড',
            'শিক্ষা': 'শিক্ষাপ্রতিষ্ঠান, পরীক্ষা, শিক্ষানীতি, ভর্তি',
            'স্বাস্থ্য': 'চিকিৎসা, রোগ-ব্যাধি, স্বাস্থ্য সেবা, মেডিকেল',
            'মতামত': 'সম্পাদকীয়, মতামত, বিশ্লেষণ, কলাম',
            'বিজ্ঞান': 'বৈজ্ঞানিক আবিষ্কার, গবেষণা, প্রযুক্তি, উদ্ভাবন',
            'প্রযুক্তি': 'তথ্যপ্রযুক্তি, নতুন প্রযুক্তি, উদ্ভাবন, গ্যাজেট, সফটওয়্যার',
            'সাহিত্য-সংস্কৃতি': 'সাহিত্য, কবিতা, গল্প, উপন্যাস, সাংস্কৃতিক অনুষ্ঠান, ঐতিহ্য, শিল্পকলা',
            'ক্ষুদ্র নৃগোষ্ঠী': 'আদিবাসী, ক্ষুদ্র জাতিগোষ্ঠী, উপজাতি, তাদের অধিকার, সংস্কৃতি, সমস্যা'
        }
        
        category_context = category_instructions.get(category, 'সাধারণ সংবাদ ও তথ্য')
        # **ক্যাটাগরি প্রসঙ্গ:** {category_context}

        prompt = f"""তুমি একজন বিশেষজ্ঞ বাংলাদেশি সংবাদ বিশ্লেষক। তোমার কাজ হল '{category}' ক্যাটাগরির সংবাদ থেকে বর্তমানে সবচেয়ে ট্রেন্ডিং ও গুরুত্বপূর্ণ ১৫টি শব্দ/বাক্যাংশ চিহ্নিত করা।
        যে Topic(২-৪ শব্দের) নিয়ে বেশি আলোচনা হচ্ছে (beshi headings a royeche), সেটা ট্রেন্ডিং টপিক। এমন শব্দ/বাক্যাংশ দাও যেটা শুনলে মানুষ বুঝতে পারবে যে এটা কীসের সাথে সম্পর্কিত। 
        যার একটা অর্থ থাকবে, এমন কিছু দেবে না যেটা অর্থহীন এবং যেটা দেখলে কনটেক্সট বোঝা যাবে না।

বিশ্লেষণের নিয়মাবলী:
1. ক্যাটাগরি ফোকাস: শুধুমাত্র '{category}' সম্পর্কিত ট্রেন্ডিং topic নিয়ে কাজ করো
2. ট্রেন্ডিং অগ্রাধিকার: যে topic (২-৪ শব্দের) গুলো বারবার আসছে এবং আলোচিত হচ্ছে
3. ২-৪ শব্দের মধ্যে স্পষ্ট বাংলা শব্দ/বাক্যাংশ
4. ব্যক্তিনাম নয়: সাধারণত ব্যক্তির নাম এড়িয়ে বিষয়বস্তুর উপর ফোকাস করো
5. Stop words এড়াও
6. ঠিক ১৫টি শব্দ/বাক্যাংশ

{category} ক্যাটাগরির সংবাদ বিষয়বস্তু:**
{content_text}

উত্তর শুধুমাত্র এই ফরম্যাটে দাও:
{{
  "trending_words": [
    "শব্দ১",
    "শব্দ২", 
    "....",
    "শব্দ১৩",
    "শব্দ১৪",
    "শব্দ১৫"
  ]
}}

গুরুত্বপূর্ণ: অন্য কোনো টেক্সট লিখো না, শুধু JSON দাও।"""
        return prompt
    
    def _call_groq_llm(self, prompt: str) -> List[str]:
        """Call Groq LLM API and extract trending words"""
        try:
            print("📤 Sending prompt to Groq API...")
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=5000,
                top_p=0.9
            )
            
            # Extract response content
            llm_response = response.choices[0].message.content.strip()
            print(f"✅ Received response from Groq API ({len(llm_response)} characters)")
            
            # Parse trending words from response
            trending_words = self._parse_trending_words(llm_response)
            return trending_words
            
        except Exception as e:
            print(f"❌ Error calling Groq API: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return []
    
    def _parse_trending_words(self, llm_response: str) -> List[str]:
        """Parse trending words from LLM response - simplified approach for better flow"""
        phrases = []
        
        print(f"🔍 Parsing LLM response for category trending words...")
        
        try:
            # Clean the response text first
            cleaned_text = llm_response.strip()
            
            # Look for JSON-like structure
            json_start = cleaned_text.find('{')
            json_end = cleaned_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_part = cleaned_text[json_start:json_end]
                
                data = json.loads(json_part)
                if isinstance(data, dict) and 'trending_words' in data:
                    phrases = data['trending_words'][:15]  # Limit to 15 words per category
                    print(f"✅ Successfully parsed JSON: {len(phrases)} words")
                    return phrases
            
            # If no valid JSON found, try manual extraction
            print("⚠️ No valid JSON found, trying manual extraction...")
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parsing failed ({e}), trying manual extraction...")
            
        # Manual extraction using regex patterns for Bengali text
        bengali_patterns = [
            r'"([^"]*[\u0980-\u09FF][^"]*)"',  # Bengali text in double quotes
            r'[""]([^""]*[\u0980-\u09FF][^""]*)[""]',  # Bengali text in smart quotes
            r'([^\s,\[\]]+[\u0980-\u09FF][^\s,\[\]]*)',  # Bengali words/phrases
        ]
        
        for pattern in bengali_patterns:
            matches = re.findall(pattern, llm_response)
            for match in matches:
                match = match.strip()
                if match and len(match) >= 3 and len(match) <= 50:
                    phrases.append(match)
            
            if len(phrases) >= 15:  # Stop when we have enough
                break
        
        # Clean and filter phrases
        cleaned_phrases = []
        seen = set()
        
        for phrase in phrases:
            phrase = phrase.strip()
            # Only keep Bengali phrases with proper length
            if (phrase and 
                len(phrase) >= 3 and 
                len(phrase) <= 50 and
                any('\u0980' <= char <= '\u09FF' for char in phrase) and
                phrase not in seen):
                cleaned_phrases.append(phrase)
                seen.add(phrase)
                
        result = cleaned_phrases[:15]  # Limit to 15 words per category
        print(f"✅ Manual extraction completed: {len(result)} unique phrases")
        return result


def get_category_trending_words(category: str, articles: List[Dict]) -> List[str]:
    """
    Helper function to get trending words for a specific category
    
    Args:
        category: Category name in Bengali
        articles: List of articles for this category
        
    Returns:
        List of trending words/phrases
    """
    try:
        analyzer = CategoryLLMAnalyzer()
        return analyzer.extract_trending_words_for_category(category, articles)
    except Exception as e:
        print(f"❌ Error in get_category_trending_words for {category}: {e}")
        return []


# Individual category functions as requested
def get_জাতীয়_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for জাতীয় category"""
    return get_category_trending_words('জাতীয়', articles)

def get_আন্তর্জাতিক_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for আন্তর্জাতিক category"""
    return get_category_trending_words('আন্তর্জাতিক', articles)

def get_অর্থনীতি_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for অর্থনীতি category"""
    return get_category_trending_words('অর্থনীতি', articles)

def get_রাজনীতি_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for রাজনীতি category"""
    return get_category_trending_words('রাজনীতি', articles)

# def get_লাইফস্টাইল_trending_words(articles: List[Dict]) -> List[str]:
#     """Get trending words for লাইফস্টাইল category"""
#     return get_category_trending_words('লাইফস্টাইল', articles)

def get_বিনোদন_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for বিনোদন category"""
    return get_category_trending_words('বিনোদন', articles)

def get_খেলাধুলা_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for খেলাধুলা category"""
    return get_category_trending_words('খেলাধুলা', articles)

# def get_ধর্ম_trending_words(articles: List[Dict]) -> List[str]:
#     """Get trending words for ধর্ম category"""
#     return get_category_trending_words('ধর্ম', articles)

# def get_চাকরি_trending_words(articles: List[Dict]) -> List[str]:
#     """Get trending words for চাকরি category"""
#     return get_category_trending_words('চাকরি', articles)

def get_শিক্ষা_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for শিক্ষা category"""
    return get_category_trending_words('শিক্ষা', articles)

def get_স্বাস্থ্য_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for স্বাস্থ্য category"""
    return get_category_trending_words('স্বাস্থ্য', articles)

# def get_মতামত_trending_words(articles: List[Dict]) -> List[str]:
#     """Get trending words for মতামত category"""
#     return get_category_trending_words('মতামত', articles)

def get_বিজ্ঞান_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for বিজ্ঞান category"""
    return get_category_trending_words('বিজ্ঞান', articles)

def get_প্রযুক্তি_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for প্রযুক্তি category"""
    return get_category_trending_words('প্রযুক্তি', articles)

def get_সাহিত্য_সংস্কৃতি_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for সাহিত্য-সংস্কৃতি category"""
    return get_category_trending_words('সাহিত্য-সংস্কৃতি', articles)

def get_ক্ষুদ্র_নৃগোষ্ঠী_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for ক্ষুদ্র নৃগোষ্ঠী category"""
    return get_category_trending_words('ক্ষুদ্র নৃগোষ্ঠী', articles)


# parse_llm_response_robust function moved inline for better flow
# This function is no longer needed as a separate entity since final selection uses text format

def calculate_phrase_frequency_in_articles(phrase: str, articles: List[Dict]) -> Dict[str, any]:
    """
    Calculate frequency of a phrase across articles and sources
    This function is called AFTER final phrase selection to determine frequency
    
    Args:
        phrase: The phrase to count frequency for
        articles: List of articles from the category
    
    Returns:
        Dictionary with frequency statistics
    """
    total_count = 0
    articles_with_phrase = 0
    sources_with_phrase = set()
    
    phrase_lower = phrase.lower().strip()
    
    for article in articles:
        article_text = ""
        # Combine title, heading, and other text fields for searching
        for field in ['title', 'heading', 'content', 'description']:
            if article.get(field):
                article_text += " " + str(article[field])
        
        article_text = article_text.lower()
        
        # Count occurrences in this article
        count_in_article = article_text.count(phrase_lower)
        if count_in_article > 0:
            total_count += count_in_article
            articles_with_phrase += 1
            
            # Track source
            source = article.get('source', 'unknown')
            sources_with_phrase.add(source)
    
    return {
        'total_count': total_count,
        'article_count': articles_with_phrase, 
        'source_count': len(sources_with_phrase),
        'sources': list(sources_with_phrase),
        'frequency': articles_with_phrase  # Main frequency metric
    }

# Final word selection will be handled in the main pipeline
# This function is kept for future use when implementing final selection logic


if __name__ == "__main__":
    # Test the analyzer
    test_articles = [
        {
            'title': 'এনবিআর কর্মকর্তাদের সঙ্গে বৃহস্পতিবার বৈঠকে বসছেন অর্থ উপদেষ্টা',
            'headings': ['অর্থনৈতিক', 'নতুন নীতি', 'কর ব্যবস্থা']
        }
    ]
    
    print("🧪 Testing Category LLM Analyzer...")
    words = get_অর্থনীতি_trending_words(test_articles)
    print(f"Test result: {words}")
