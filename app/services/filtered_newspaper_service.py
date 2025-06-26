#!/usr/bin/env python3
"""
Filtered Newspaper Scraper - শুধুমাত্র নির্দিষ্ট ক্যাটাগরির সংবাদ স্ক্র্যাপ করে
"""

import json
import time
from datetime import datetime, date
from typing import Dict, List, Optional, Set
import logging
from collections import Counter
import re

# Database imports - completely optional
Session = None
CategoryTrendingPhrase = None
get_db = None

try:
    from sqlalchemy.orm import Session
    from app.models.word import CategoryTrendingPhrase
    from app.db.database import get_db
    print("✅ Database imports successful")
except ImportError as e:
    print(f"⚠️ Database imports skipped: {e}")
    # Continue without database functionality

# Import your existing scraping functions
try:
    from app.routes.helpers import (
        scrape_prothom_alo, scrape_kaler_kantho, scrape_jugantor,
        scrape_samakal, scrape_janakantha, scrape_inqilab,
        scrape_manobkantha, scrape_ajker_patrika, scrape_protidiner_sangbad
    )
    from app.services.url_pattern_category_detector import URLPatternCategoryDetector
except ImportError as e:
    # For when running from within app/services
    try:
        from routes.helpers import (
            scrape_prothom_alo, scrape_kaler_kantho, scrape_jugantor,
            scrape_samakal, scrape_janakantha, scrape_inqilab,
            scrape_manobkantha, scrape_ajker_patrika, scrape_protidiner_sangbad
        )
        from app.services.url_pattern_category_detector import URLPatternCategoryDetector
    except ImportError:
        print(f"❌ Import error: {e}")
        print("Please ensure helpers.py and url_pattern_category_detector.py are accessible")
        exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FilteredNewspaperScraper:
    """নির্দিষ্ট ক্যাটাগরির সংবাদ স্ক্র্যাপ করার ক্লাস"""
    
    def __init__(self, target_categories: List[str]):
        """
        Initialize the filtered scraper
        
        Args:
            target_categories: List of categories to scrape (in Bengali)
        """
        self.target_categories = set(target_categories)
        self.scraped_articles = []
        self.categorized_articles = {}
        self.statistics = {
            'total_scraped': 0,
            'total_filtered': 0,
            'category_counts': {},
            'source_counts': {},
            'scraping_time': 0
        }
        # Initialize category detector
        self.url_pattern_detector = URLPatternCategoryDetector()
        
        # Initialize category counts
        for category in self.target_categories:
            self.categorized_articles[category] = []
            self.statistics['category_counts'][category] = 0
    
    def is_target_category(self, url: str) -> Optional[str]:
        """
        Check if URL belongs to target categories with flexible matching
        
        Args:
            url: The URL to check
            
        Returns:
            Category name if it's a target category, None otherwise
        """
        try:
            detected_category, _, _ = self.url_pattern_detector.detect_category_by_url_pattern(url)

            # Direct match first
            if detected_category in self.target_categories:
                return detected_category
            
            # Flexible category mapping for common variations
            category_mappings = {
                # Map detected categories to target categories
                'রাজনীতি': 'রাজনীতি',
                'জাতীয়': 'জাতীয়', 
                'National/Bangladesh': 'জাতীয়',
                'Politics': 'রাজনীতি',
                'Sports': 'খেলাধুলা',
                'খেলা': 'খেলাধুলা',
                'Business/Economy': 'অর্থনীতি',
                'Economy': 'অর্থনীতি',
                'Entertainment': 'বিনোদন',
                'Technology': 'প্রযুক্তি',
                'Health': 'স্বাস্থ্য',
                'Education': 'শিক্ষা',
                'Opinion/Editorial': 'মতামত',
                'Lifestyle': 'লাইফস্টাইল',
                'Religion': 'ধর্ম',
                'Science': 'বিজ্ঞান',
                'Jobs/Career': 'চাকরি',
                'প্রযুক্তি': 'প্রযুক্তি',
                'স্বাস্থ্য': 'স্বাস্থ্য',
                'শিক্ষা': 'শিক্ষা',
                'বিনোদন': 'বিনোদন',
                'অর্থনীতি': 'অর্থনীতি',
                'খেলাধুলা': 'খেলাধুলা',
                'লাইফস্টাইল': 'লাইফস্টাইল',
                'মতামত': 'মতামত',
                'ধর্ম': 'ধর্ম',
                'বিজ্ঞান': 'বিজ্ঞান',
                'চাকরি': 'চাকরি'
            }
            
            # Check if detected category can be mapped to a target category
            mapped_category = category_mappings.get(detected_category)
            if mapped_category and mapped_category in self.target_categories:
                return mapped_category
                
            return None
        except Exception as e:
            logger.warning(f"Error categorizing URL {url}: {e}")
            return None
    
    def scrape_newspaper(self, source_name: str, scraper_func) -> List[Dict]:
        """
        Scrape a single newspaper and filter by categories
        
        Args:
            source_name: Name of the newspaper source
            scraper_func: Function to scrape the newspaper
            
        Returns:
            List of filtered articles
        """
        logger.info(f"🔍 Scraping {source_name}...")
        
        try:
            # Scrape all articles from the source
            articles = scraper_func()
            logger.info(f"📰 {source_name}: {len(articles)} articles found")
            
            # Filter articles by target categories
            filtered_articles = []
            for article in articles:
                category = self.is_target_category(article['url'])
                if category:
                    article['category'] = category
                    filtered_articles.append(article)
                    
                    # Add to categorized list
                    self.categorized_articles[category].append(article)
                    self.statistics['category_counts'][category] += 1
            
            # Update source statistics
            self.statistics['source_counts'][source_name] = len(filtered_articles)
            logger.info(f"✅ {source_name}: {len(filtered_articles)} target articles found")
            
            return filtered_articles
            
        except Exception as e:
            logger.error(f"❌ Error scraping {source_name}: {e}")
            self.statistics['source_counts'][source_name] = 0
            return []
    
    def scrape_all_newspapers(self) -> Dict:
        """
        Scrape all newspapers and return filtered results
        
        Returns:
            Dictionary containing all scraped and categorized articles
        """
        start_time = time.time()
        logger.info("🚀 Starting filtered newspaper scraping...")
        logger.info(f"🎯 Target categories: {', '.join(self.target_categories)}")
        
        # Define newspaper scrapers
        scrapers = {
            'prothom_alo': scrape_prothom_alo,
            'kaler_kantho': scrape_kaler_kantho,
            'jugantor': scrape_jugantor,
            'samakal': scrape_samakal,
            'janakantha': scrape_janakantha,
            'inqilab': scrape_inqilab,
            'manobkantha': scrape_manobkantha,
            'ajker_patrika': scrape_ajker_patrika,
            'protidiner_sangbad': scrape_protidiner_sangbad
        }
        
        # Scrape each newspaper
        all_filtered_articles = []
        for source_name, scraper_func in scrapers.items():
            filtered_articles = self.scrape_newspaper(source_name, scraper_func)
            all_filtered_articles.extend(filtered_articles)
        
        # Update statistics
        self.statistics['total_scraped'] = len(all_filtered_articles)
        self.statistics['total_filtered'] = len(all_filtered_articles)  # Same since we only keep target categories
        self.statistics['scraping_time'] = time.time() - start_time
        
        self.scraped_articles = all_filtered_articles
        
        logger.info(f"✅ Scraping completed!")
        logger.info(f"📊 Total filtered articles: {self.statistics['total_filtered']}")
        logger.info(f"⏱️  Time taken: {self.statistics['scraping_time']:.2f} seconds")
        
        return self.get_results()
    
    def get_results(self) -> Dict:
        """
        Get formatted results with category-wise listings
        
        Returns:
            Dictionary containing all results and statistics
        """
        # Extract trending words for each category
        trending_words = self.extract_trending_words()
        
        return {
            'scraping_info': {
                'timestamp': datetime.now().isoformat(),
                'target_categories': list(self.target_categories),
                'total_articles': self.statistics['total_filtered'],
                'scraping_time_seconds': self.statistics['scraping_time']
            },
            'statistics': self.statistics,
            'category_wise_articles': self.categorized_articles,
            'category_trending_words': trending_words,
            'all_articles': self.scraped_articles
        }
    
    def print_category_summary(self):
        """Print a summary of articles by category"""
        print("\n" + "="*80)
        print("📊 CATEGORY-WISE ARTICLE SUMMARY")
        print("="*80)
        
        total_articles = sum(self.statistics['category_counts'].values())
        trending_words = self.extract_trending_words()
        
        for category in sorted(self.target_categories):
            count = self.statistics['category_counts'][category]
            percentage = (count / total_articles * 100) if total_articles > 0 else 0
            
            print(f"🏷️  {category:15}: {count:4d} articles ({percentage:5.1f}%)")
            
            # Show trending words for this category
            if trending_words.get(category):
                trend_str = ", ".join(trending_words[category][:5])  # Show top 5
                print(f"     🔥 Trending: {trend_str}")
            
            # Show first few article titles as examples
            if count > 0:
                for i, article in enumerate(self.categorized_articles[category][:3]):
                    title = article['title'][:60] + "..." if len(article['title']) > 60 else article['title']
                    print(f"     └─ {title}")
                if count > 3:
                    print(f"     └─ ... and {count - 3} more articles")
                print()
        
        print(f"📈 Total articles: {total_articles}")
        print(f"⏱️  Scraping time: {self.statistics['scraping_time']:.2f} seconds")
    
    def save_results(self, filename: Optional[str] = None) -> str:
        """
        Save results to JSON file
        
        Args:
            filename: Optional custom filename
            
        Returns:
            Path to the saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"filtered_newspaper_results_{timestamp}.json"
        
        results = self.get_results()
        
        # Convert any date objects to strings for JSON serialization
        def json_serializer(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=json_serializer)
        
        logger.info(f"💾 Results saved to: {filename}")
        return filename
    
    def extract_trending_words(self, min_frequency: int = 3, top_words: int = 10) -> Dict[str, List[str]]:
        """
        Extract trending words for each category
        
        Args:
            min_frequency: Minimum frequency for a word to be considered trending
            top_words: Number of top words to return per category
            
        Returns:
            Dictionary mapping category to list of trending words
        """
        category_trending = {}
        
        # Bengali stop words
        stop_words = {
            'এর', 'এই', 'ও', 'তার', 'সে', 'যে', 'কি', 'না', 'হয়', 'হয়েছে', 
            'করে', 'করা', 'করেছে', 'করেন', 'করবে', 'হবে', 'আছে', 'থেকে', 
            'জন্য', 'সঙ্গে', 'সাথে', 'আর', 'অর্থাৎ', 'কিন্তু', 'বলে', 'বলেন',
            'যা', 'যার', 'যেতে', 'দিয়ে', 'নিয়ে', 'পর', 'আগে', 'পরে', 'এবং',
            'বা', 'অথবা', 'কিংবা', 'তবে', 'তাই', 'অনুযায়ী', 'মতে', 'অনুসারে'
        }
        
        for category, articles in self.categorized_articles.items():
            if not articles:
                category_trending[category] = []
                continue
                
            # Collect all words from titles and headings in this category
            all_text = []
            for article in articles:
                title = article.get('title', '')
                heading = article.get('heading', '')
                all_text.append(title + ' ' + heading)
            
            # Extract Bengali words (keeping only Bengali characters and numbers)
            words = []
            for text in all_text:
                # Remove English words and keep only Bengali
                bengali_text = re.sub(r'[a-zA-Z0-9\s\-\(\)\[\]\{\}\.\,\;\:\!\?\"\'\`]+', ' ', text)
                # Split by whitespace and filter
                text_words = [word.strip() for word in bengali_text.split() if len(word.strip()) > 2]
                words.extend(text_words)
            
            # Remove stop words and count frequency
            filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
            word_counts = Counter(filtered_words)
            
            # Get trending words (words that appear at least min_frequency times)
            trending = [word for word, count in word_counts.most_common(top_words) 
                       if count >= min_frequency]
            
            category_trending[category] = trending
            
        return category_trending
    
    def save_trending_words_to_db(self, trending_words: Dict[str, List[str]], 
                                 db_session = None) -> int:
        """
        Save trending words to database
        
        Args:
            trending_words: Dictionary of category -> trending words
            db_session: Database session (optional)
            
        Returns:
            Number of phrases saved to database
        """
        if not CategoryTrendingPhrase or not db_session:
            logger.warning("Database not available, skipping database save")
            return 0
        
        saved_count = 0
        analysis_date = date.today()
        
        try:
            for category, words in trending_words.items():
                if not words:
                    continue
                
                for i, word in enumerate(words):
                    # Create a score based on ranking (higher rank = higher score)
                    score = len(words) - i
                    
                    category_phrase = CategoryTrendingPhrase(
                        date=analysis_date,
                        category=category,
                        phrase=word,
                        score=float(score),
                        frequency=score,  # Using score as proxy for frequency
                        phrase_type='unigram',
                        source='newspaper_scraping'
                    )
                    
                    db_session.add(category_phrase)
                    saved_count += 1
            
            db_session.commit()
            logger.info(f"✅ Saved {saved_count} trending words to database")
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"❌ Error saving trending words to database: {e}")
            raise
        
        return saved_count
    
    def save_llm_prompts_for_all_categories(self, output_filename: str = None):
        """
        Scrape newspapers, group articles by category, and save the LLM prompts for each category to a JSON file.
        Prompts are generated with the FULL content (no truncation), and the character count is included.
        """
        from app.services.category_llm_analyzer import CategoryLLMAnalyzer
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"llm_prompts_by_category_{timestamp}.json"

        # Use the same categories as the main pipeline
        TARGET_CATEGORIES = [
            'জাতীয়', 'আন্তর্জাতিক', 'অর্থনীতি', 'রাজনীতি', 'লাইফস্টাইল', 'বিনোদন',
            'খেলাধুলা', 'ধর্ম', 'চাকরি', 'শিক্ষা', 'স্বাস্থ্য', 'মতামত', 'বিজ্ঞান', 'প্রযুক্তি'
        ]
        
        # Scrape and group articles
        scraper = FilteredNewspaperScraper(TARGET_CATEGORIES)
        results = scraper.scrape_all_newspapers()
        category_articles = results['category_wise_articles']

        analyzer = CategoryLLMAnalyzer()
        prompts = {}
        for category in TARGET_CATEGORIES:
            articles = category_articles.get(category, [])
            if articles:
                # --- FULL content, NO truncation ---
                content_pieces = []
                for article in articles:
                    title = article.get('title', '').strip()
                    headings = article.get('headings', [])
                    if title:
                        content_pieces.append(f"শিরোনাম: {title}")
                    if headings:
                        for heading in headings:
                            if heading and heading.strip():
                                content_pieces.append(f"সংবাদ: {heading.strip()}")
                full_content_text = "\n".join(content_pieces)
                prompt = analyzer._create_category_prompt(category, full_content_text)
                prompts[category] = {
                    'prompt': prompt,
                    'prompt_length': len(prompt),
                    'content_length': len(full_content_text),
                    'num_articles': len(articles)
                }
            else:
                prompts[category] = {
                    'prompt': None,
                    'prompt_length': 0,
                    'content_length': 0,
                    'num_articles': 0
                }

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)
        print(f"✅ LLM prompts for all categories saved to: {output_filename}")


def main():
    """Main function to demonstrate filtered scraping"""
    
    # Your specified target categories
    TARGET_CATEGORIES = [
        'জাতীয়', 'আন্তর্জাতিক', 'অর্থনীতি', 'রাজনীতি', 'লাইফস্টাইল', 'বিনোদন', 
        'খেলাধুলা', 'ধর্ম', 'চাকরি', 'শিক্ষা', 'স্বাস্থ্য', 'মতামত', 'বিজ্ঞান', 'প্রযুক্তি'
    ]
    
    print("🎯 FILTERED NEWSPAPER SCRAPER")
    print("="*50)
    print("📋 Target Categories:")
    for i, category in enumerate(TARGET_CATEGORIES, 1):
        print(f"   {i:2d}. {category}")
    print()
    
    # Create and run the filtered scraper
    scraper = FilteredNewspaperScraper(TARGET_CATEGORIES)
    
    # Scrape all newspapers with filtering
    results = scraper.scrape_all_newspapers()
    
    # Print summary
    scraper.print_category_summary()
    
    # Save results
    filename = scraper.save_results()
    
    print("\n" + "="*80)
    print("✅ SCRAPING COMPLETED SUCCESSFULLY!")
    print("="*80)
    print(f"📁 Results saved to: {filename}")
    print(f"📊 Total target articles: {results['scraping_info']['total_articles']}")
    print(f"🏷️  Categories found: {len([c for c in TARGET_CATEGORIES if scraper.statistics['category_counts'][c] > 0])}")
    
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--save-llm-prompts":
        scraper = FilteredNewspaperScraper([
            'জাতীয়', 'আন্তর্জাতিক', 'অর্থনীতি', 'রাজনীতি', 'লাইফস্টাইল', 'বিনোদন',
            'খেলাধুলা', 'ধর্ম', 'চাকরি', 'শিক্ষা', 'স্বাস্থ্য', 'মতামত', 'বিজ্ঞান', 'প্রযুক্তি'
        ])
        scraper.save_llm_prompts_for_all_categories()
    else:
        results = main()
