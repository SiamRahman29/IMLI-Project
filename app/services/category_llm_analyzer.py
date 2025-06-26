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
        """Prepare text content from articles for LLM analysis"""
        content_pieces = []
        
        for article in articles:
            # Extract title and headings
            title = article.get('title', '').strip()
            headings = article.get('headings', [])
            
            if title:
                content_pieces.append(f"শিরোনাম: {title}")
            
            if headings:
                # Take first few headings to avoid token limit
                for heading in headings[:5]:
                    if heading and heading.strip():
                        content_pieces.append(f"সংবাদ: {heading.strip()}")
        
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
            'প্রযুক্তি': 'তথ্যপ্রযুক্তি, নতুন প্রযুক্তি, উদ্ভাবন, গ্যাজেট, সফটওয়্যার'
        }
        
        category_context = category_instructions.get(category, 'সাধারণ সংবাদ ও তথ্য')
        # **ক্যাটাগরি প্রসঙ্গ:** {category_context}

        prompt = f"""
তুমি একজন বিশেষজ্ঞ বাংলাদেশি সংবাদ বিশ্লেষক। তোমার কাজ হল '{category}' ক্যাটাগরির সংবাদ থেকে বর্তমানে সবচেয়ে ট্রেন্ডিং ও গুরুত্বপূর্ণ Topic ta চিহ্নিত করা।Jeta niye manus ekhn beshi kotha bolche, eta trending topic.and emon words/phrase deo jeta shunle manus bujhte parbe je eta {category} er shathe related. jar ekta meaning thakbe,emon kichu diba nah jeta meaninful and context bujha jabe na eta shunle 

বিশ্লেষণের নিয়মাবলী:
1. **ক্যাটাগরি ফোকাস**: শুধুমাত্র '{category}' সম্পর্কিত ট্রেন্ডিং topic নিয়ে কাজ করো
2. **ট্রেন্ডিং অগ্রাধিকার**: যে topic ta বারবার আসছে এবং আলোচিত হচ্ছে
3. **সংক্ষিপ্ত ও স্পষ্ট**: ২-৪ শব্দের মধ্যে স্পষ্ট বাংলা শব্দ/বাক্যাংশ
4. **ব্যক্তিনাম নয়**: সাধারণত ব্যক্তির নাম এড়িয়ে বিষয়বস্তুর উপর ফোকাস করো
5. **Stop words এড়াও**: সাধারণ শব্দ (এর, সে, তার, ইত্যাদি) এড়িয়ে চলো

**{category} ক্যাটাগরির সংবাদ বিষয়বস্তু:**
{content_text}

**আউটপুট ফরম্যাট (শুধুমাত্র বাংলায়):**
{category} ট্রেন্ডিং শব্দ/বাক্যাংশ (৫টি):
১. [বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
২. [বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]  
৩. [বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
৪. [বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]
৫. [বাংলা ট্রেন্ডিং শব্দ/বাক্যাংশ]

**গুরুত্বপূর্ণ:** শুধুমাত্র উপরের নির্দিষ্ট ফরম্যাটে উত্তর দাও। অতিরিক্ত ব্যাখ্যা বা মন্তব্য যোগ করো না।
"""
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
                max_tokens=1000,
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
        """Parse trending words from LLM response"""
        trending_words = []
        
        try:
            lines = llm_response.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Look for numbered items (১., ২., 1., 2., etc.)
                if re.match(r'^[১২৩৪৫৬৭৮৯০1-9][\.\)]\s*', line):
                    # Extract the text after the number
                    word = re.sub(r'^[১২৩৪৫৬৭৮৯০1-9][\.\)]\s*', '', line).strip()
                    
                    # Clean up the word
                    word = word.replace('[', '').replace(']', '').strip()
                    
                    if word and len(word) > 1:
                        trending_words.append(word)
            
            print(f"🔍 Parsed {len(trending_words)} trending words from LLM response")
            for i, word in enumerate(trending_words, 1):
                print(f"   {i}. {word}")
                
        except Exception as e:
            print(f"❌ Error parsing trending words: {e}")
        
        return trending_words


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

def get_লাইফস্টাইল_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for লাইফস্টাইল category"""
    return get_category_trending_words('লাইফস্টাইল', articles)

def get_বিনোদন_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for বিনোদন category"""
    return get_category_trending_words('বিনোদন', articles)

def get_খেলাধুলা_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for খেলাধুলা category"""
    return get_category_trending_words('খেলাধুলা', articles)

def get_ধর্ম_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for ধর্ম category"""
    return get_category_trending_words('ধর্ম', articles)

def get_চাকরি_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for চাকরি category"""
    return get_category_trending_words('চাকরি', articles)

def get_শিক্ষা_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for শিক্ষা category"""
    return get_category_trending_words('শিক্ষা', articles)

def get_স্বাস্থ্য_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for স্বাস্থ্য category"""
    return get_category_trending_words('স্বাস্থ্য', articles)

def get_মতামত_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for মতামত category"""
    return get_category_trending_words('মতামত', articles)

def get_বিজ্ঞান_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for বিজ্ঞান category"""
    return get_category_trending_words('বিজ্ঞান', articles)

def get_প্রযুক্তি_trending_words(articles: List[Dict]) -> List[str]:
    """Get trending words for প্রযুক্তি category"""
    return get_category_trending_words('প্রযুক্তি', articles)


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
