import os
import re
import time
import random
import requests
from requests.exceptions import Timeout, ConnectionError
from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple, TYPE_CHECKING
from collections import Counter, defaultdict
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import feedparser
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from groq import Groq
import traceback

# Type checking imports
if TYPE_CHECKING:
    from app.services.advanced_bengali_nlp import TrendingBengaliAnalyzer

# Database and model imports
from sqlalchemy.orm import Session
from app.models.word import TrendingPhrase, Article
from app.services.text_preprocessing import get_google_trends_bangladesh, get_youtube_trending_bangladesh, get_serpapi_trending_bangladesh
from app.services.stopwords import STOP_WORDS


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

# Custom stopwords for newspaper article filtering
NEWSPAPER_STOPWORDS = {
    'ক্যাম্পাস', 'ক্যারিয়ার', 'বিনোদন', 'আন্তর্জাতিক', 'গণমাধ্যম', 'কলাম', 
    'আইন-আদালত', 'ধর্ম', 'প্রবাস', 'সারাদেশ', 'ফিচার', 'খেলাধুলা', 'ভিডিও',
    'আড্ডা', 'পরিবেশ', 'স্বাস্থ্য', 'প্রযুক্তি', 'শিক্ষা', 'ল–র–ব–য–হ', 
    'বিশ্লেষণ', 'নারী', 'মতামত', 'ছবি', 'চাকরি', 'জীবনধারা', 'অর্থনীতি', 
    'ইসলাম', 'বিশ্ব', 'ফ্যাক্টচেক', 'বিনোদন', 'রাজনীতি', 'জাতীয়'
}

def clean_heading_text(text: str) -> str:
    """Clean and filter heading text by removing stopwords"""
    if not text:
        return text
    
    # Remove stopwords
    words = text.split()
    cleaned_words = [word for word in words if word not in NEWSPAPER_STOPWORDS]
    return ' '.join(cleaned_words)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class BengaliTextProcessor:
    def __init__(self):
        self.stop_words = STOP_WORDS

    def clean_text(self, text: str) -> str:
        """Clean and normalize Bengali text"""
        if not text:
            return ""
        # Remove HTML tags
        text = BeautifulSoup(text, 'html.parser').get_text()
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        # Remove special characters but keep Bengali characters
        text = re.sub(r'[^\u0980-\u09FF\s\u0964\u0965]', ' ', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def tokenize_sentences(self, text: str) -> List[str]:
        """Tokenize text into sentences"""
        sentences = re.split(r'[।!?]', text)
        sentences = [sent.strip() for sent in sentences if sent.strip()]
        return sentences

    def tokenize_words(self, text: str) -> List[str]:
        """Tokenize text into words"""
        words = re.findall(r'[\u0980-\u09FF]+', text)
        filtered_words = [word for word in words if len(word) > 1]  # Filter single characters
        return filtered_words

    def remove_stop_words(self, words: List[str]) -> List[str]:
        """Remove Bengali stop words"""
        filtered_words = [word for word in words if word not in self.stop_words]
        return filtered_words

    def generate_ngrams(self, words: List[str], n: int) -> List[str]:
        """Generate n-grams from word list"""
        if len(words) < n:
            return []
        ngrams = [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]
        return ngrams

class TrendingAnalyzer:
    def __init__(self):
        self.text_processor = BengaliTextProcessor()
        
    def filter_quality_phrases(self, phrases_dict: Dict[str, int], min_length=3, max_length=50) -> Dict[str, int]:
        """Filter phrases for better quality by removing duplicates and low-quality entries"""
        
        # Person name indicators to exclude
        person_indicators = [
            'মাননীয়', 'জনাব', 'মিসেস', 'মিস', 'ডঃ', 'প্রফেসর', 'শেখ', 'মোঃ', 'সৈয়দ',
            'সাহেব', 'সাহেবা', 'বেগম', 'খান', 'চৌধুরী', 'আহমেদ', 'হোসেন', 'উদ্দিন', 'রহমান',
            'মন্ত্রী', 'প্রধানমন্ত্রী', 'রাষ্ট্রপতি', 'সচিব'
        ]
        
        # Low-quality patterns to exclude
        exclude_phrases = [
            'বলেছেন', 'জানিয়েছেন', 'নিশ্চিত করেছেন', 'উল্লেখ করেছেন',
            'করা হয়েছে', 'হয়েছে বলে', 'বলা হয়েছে', 'জানা গেছে',
            'সংবাদদাতা', 'প্রতিবেদক', 'সংবাদ সম্মেলন'
        ]
        
        filtered_phrases = {}
        seen_topics = set()
        
        for phrase, freq in phrases_dict.items():
            phrase_clean = phrase.strip()
            
            # Length filtering
            if len(phrase_clean) < min_length or len(phrase_clean) > max_length:
                continue
                
            # Skip phrases with person indicators
            if any(indicator in phrase_clean for indicator in person_indicators):
                continue
                
            # Skip low-quality phrases
            if any(exclude in phrase_clean for exclude in exclude_phrases):
                continue
                
            # Skip if it's mostly numbers or contains too many English characters
            if re.search(r'[0-9]{3,}', phrase_clean) or re.search(r'[a-zA-Z]{5,}', phrase_clean):
                continue
                
            # Topic deduplication - avoid similar phrases
            phrase_lower = phrase_clean.lower()
            words = set(phrase_lower.split())
            
            is_duplicate = False
            for seen_topic in list(seen_topics):
                seen_words = set(seen_topic.split())
                
                # Check for significant word overlap
                if words and seen_words:
                    overlap = len(words.intersection(seen_words)) / min(len(words), len(seen_words))
                    if overlap > 0.75:  # 75% word overlap = duplicate
                        # Keep the one with higher frequency
                        existing_freq = filtered_phrases.get(seen_topic, 0)
                        if freq > existing_freq:
                            # Remove old entry
                            filtered_phrases.pop(seen_topic, None)
                            seen_topics.remove(seen_topic)
                        else:
                            is_duplicate = True
                        break
                        
                # Check for substring relationship
                if phrase_lower in seen_topic or seen_topic in phrase_lower:
                    # Keep the longer, more descriptive phrase
                    if len(phrase_clean) > len(seen_topic):
                        filtered_phrases.pop(seen_topic, None)
                        seen_topics.remove(seen_topic)
                    else:
                        is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_phrases[phrase_clean] = freq
                seen_topics.add(phrase_lower)
        
        return filtered_phrases
        
    def calculate_tfidf_scores(self, documents: List[str]) -> Dict[str, float]:
        """Calculate TF-IDF scores for terms in documents"""
        if not documents:
            return {}
            
        # Create TF-IDF vectorizer for Bengali text
        vectorizer = TfidfVectorizer(
            tokenizer=self.text_processor.tokenize_words,
            lowercase=False,
            ngram_range=(1, 3),
            max_features=1000,
            min_df=2,
            token_pattern=None  # Suppress warning when using custom tokenizer
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(documents)
            feature_names = vectorizer.get_feature_names_out()
            
            # Calculate average TF-IDF scores
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            
            return dict(zip(feature_names, mean_scores))
        except Exception as e:
            print(f"TF-IDF calculation error: {e}")
            return {}
    
    def calculate_frequency_scores(self, texts: List[str]) -> Dict[str, Dict]:
        """Calculate frequency-based scores for n-grams"""
        all_words = []
        all_bigrams = []
        all_trigrams = []
        
        for text in texts:
            clean_text = self.text_processor.clean_text(text)
            words = self.text_processor.tokenize_words(clean_text)
            words = self.text_processor.remove_stop_words(words)
            
            all_words.extend(words)
            all_bigrams.extend(self.text_processor.generate_ngrams(words, 2))
            all_trigrams.extend(self.text_processor.generate_ngrams(words, 3))
        
        # Count frequencies
        unigram_freq = Counter(all_words)
        bigram_freq = Counter(all_bigrams)
        trigram_freq = Counter(all_trigrams)
        
        return {
            'unigrams': dict(unigram_freq.most_common(50)),
            'bigrams': dict(bigram_freq.most_common(30)),
            'trigrams': dict(trigram_freq.most_common(20))
        }
    
    def calculate_trend_score(self, phrase: str, frequency: int, tfidf_score: float = 0.0, 
                             recency_weight: float = 1.0, source_weight: float = 1.0) -> float:
        """Calculate comprehensive trend score with multiple factors"""
        # Base score from frequency (logarithmic to prevent outliers)
        freq_score = np.log(frequency + 1) * 2
        
        # TF-IDF component (weighted heavily)
        tfidf_component = tfidf_score * 15
        
        # Length bonus (prefer meaningful phrases)
        words_in_phrase = len(phrase.split())
        if words_in_phrase == 1:
            length_bonus = 0.5  # Single words get less bonus
        elif words_in_phrase == 2:
            length_bonus = 1.0  # Bigrams get standard bonus
        elif words_in_phrase == 3:
            length_bonus = 1.5  # Trigrams get more bonus
        else:
            length_bonus = 0.2  # Very long phrases get penalized
        
        # Recency bonus (newer content gets higher score)
        recency_bonus = recency_weight * 0.5
        
        # Source reliability bonus
        source_bonus = source_weight * 0.3
        
        # Special category bonus for important terms
        category_bonus = self._get_category_bonus(phrase)
        
        # Final score calculation
        final_score = (freq_score + tfidf_component + length_bonus + 
                      recency_bonus + source_bonus + category_bonus)
        
        return max(0.0, final_score)  # Ensure non-negative score
    
    def _get_category_bonus(self, phrase: str) -> float:
        """Give bonus points for important categories"""
        phrase_lower = phrase.lower()
        
        # Political terms
        political_terms = {'সরকার', 'মন্ত্রী', 'প্রধানমন্ত্রী', 'নেতা', 'দল', 'রাজনীতি', 'নির্বাচন', 'ভোট'}
        if any(term in phrase_lower for term in political_terms):
            return 1.0
            
        # Economic terms  
        economic_terms = {'অর্থনীতি', 'টাকা', 'ব্যাংক', 'ব্যবসা', 'বাজার', 'মূল্য', 'দাম', 'বিনিয়োগ'}
        if any(term in phrase_lower for term in economic_terms):
            return 0.8
            
        # Social terms
        social_terms = {'সমাজ', 'শিক্ষা', 'স্বাস্থ্য', 'পরিবার', 'যুব', 'নারী', 'শিশু'}
        if any(term in phrase_lower for term in social_terms):
            return 0.6
            
        # Technology terms
        tech_terms = {'প্রযুক্তি', 'ইন্টারনেট', 'মোবাইল', 'কম্পিউটার', 'অ্যাপ', 'সফটওয়্যার'}
        if any(term in phrase_lower for term in tech_terms):
            return 0.7
            
        return 0.0  # No bonus

def get_trending_words(db: Session):
    """
    Comprehensive trending analysis from both news and social media sources.
    Implements N-gram Frequency Analysis with TF-IDF scoring.
    """
    print("Starting comprehensive trending words analysis...")
    # Fetch news articles
    print("Fetching news data...")
    news_articles = fetch_news()
    print(f"Fetched {len(news_articles)} news articles")
    # Fetch social media content (DISABLED)
    # print("Fetching social media content...")
    # try:
    #     social_media_posts = scrape_social_media_content()
    #     print(f"Fetched {len(social_media_posts)} social media posts")
    # except Exception as e:
    #     print(f"Error fetching social media content: {e}")
    #     social_media_posts = []
    social_media_posts = []
    # Combine all content
    all_content = news_articles + social_media_posts
    if not all_content:
        return []
    # Store articles and posts in database
    print("Storing content in the database...")
    store_news(db, news_articles)
    # if social_media_posts:
    #     store_social_media_content(db, social_media_posts)
    
    # Analyze trending phrases using advanced Bengali NLP
    print("Analyzing trending phrases with advanced Bengali NLP...")
    from app.services.advanced_bengali_nlp import TrendingBengaliAnalyzer
    
    today = date.today()
    # Clear existing data for today
    db.query(TrendingPhrase).filter(TrendingPhrase.date == today).delete()
    
    # Use advanced Bengali analyzer for main analysis
    advanced_analyzer = TrendingBengaliAnalyzer()
    
    # Analyze news content with advanced NLP
    if news_articles:
        print(f"\n🔍 Analyzing {len(news_articles)} news articles with advanced Bengali NLP...")
        analyze_trending_content_and_store(db, advanced_analyzer, news_articles, 'news', today)
    
    # Analyze social media content  
    if social_media_posts:
        print(f"\n📱 Analyzing {len(social_media_posts)} social media posts...")
        analyze_trending_content_and_store(db, advanced_analyzer, social_media_posts, 'social_media', today)
    
    db.commit()
    print("Comprehensive trending phrases analysis completed and stored!")
    
    # Aggregate weekly trending data
    print("Aggregating weekly trending data...")
    try:
        # weekly_count = aggregate_weekly_trending(db)
        # print(f"Weekly aggregation completed: {weekly_count} phrases")
        print("Weekly aggregation skipped (function not implemented)")
    except Exception as e:
        print(f"Error in weekly aggregation: {e}")
        import traceback
        traceback.print_exc()

def analyze_and_store_trends(db: Session, analyzer: TrendingAnalyzer, 
                           content: List[Dict], source: str, target_date: date):
    """Analyze trends for a specific content source and store in database"""
    # Prepare text data
    texts = []
    for item in content:
        # Use heading instead of description
        if item.get('heading'):
            texts.append(item['heading'])
        elif item.get('title'):
            texts.append(item['title'])
    if not texts:
        return
    
    # Use advanced Bengali analyzer for better quality filtering
    from app.services.advanced_bengali_nlp import TrendingBengaliAnalyzer
    advanced_analyzer = TrendingBengaliAnalyzer()
    
    # Calculate frequency scores using old method
    frequency_scores = analyzer.calculate_frequency_scores(texts)
    
    # Basic filtering first
    print(f"Before filtering - Unigrams: {len(frequency_scores['unigrams'])}, Bigrams: {len(frequency_scores['bigrams'])}, Trigrams: {len(frequency_scores['trigrams'])}")
    
    # Apply basic quality filtering to each n-gram type
    frequency_scores['unigrams'] = analyzer.filter_quality_phrases(frequency_scores['unigrams'])
    frequency_scores['bigrams'] = analyzer.filter_quality_phrases(frequency_scores['bigrams'])  
    frequency_scores['trigrams'] = analyzer.filter_quality_phrases(frequency_scores['trigrams'])
    
    # Apply advanced filtering to remove duplicates and person names
    # Convert frequency dict to list of tuples for advanced filtering
    unigrams_list = [(phrase, 1.0) for phrase in frequency_scores['unigrams'].keys()]
    bigrams_list = [(phrase, 1.0) for phrase in frequency_scores['bigrams'].keys()]
    trigrams_list = [(phrase, 1.0) for phrase in frequency_scores['trigrams'].keys()]
    
    # Apply advanced filtering
    filtered_unigrams = advanced_analyzer.filter_and_deduplicate_keywords(unigrams_list, max_results=50)
    filtered_bigrams = advanced_analyzer.filter_and_deduplicate_keywords(bigrams_list, max_results=30) 
    filtered_trigrams = advanced_analyzer.filter_and_deduplicate_keywords(trigrams_list, max_results=20)
    
    # Convert back to frequency dict format
    frequency_scores['unigrams'] = {phrase: frequency_scores['unigrams'][phrase] for phrase, _ in filtered_unigrams if phrase in frequency_scores['unigrams']}
    frequency_scores['bigrams'] = {phrase: frequency_scores['bigrams'][phrase] for phrase, _ in filtered_bigrams if phrase in frequency_scores['bigrams']}
    frequency_scores['trigrams'] = {phrase: frequency_scores['trigrams'][phrase] for phrase, _ in filtered_trigrams if phrase in frequency_scores['trigrams']}
    
    print(f"After advanced filtering - Unigrams: {len(frequency_scores['unigrams'])}, Bigrams: {len(frequency_scores['bigrams'])}, Trigrams: {len(frequency_scores['trigrams'])}")
    
    # Calculate TF-IDF scores
    tfidf_scores = analyzer.calculate_tfidf_scores(texts)
    
    # Determine source weight and recency weight
    source_weight = 1.0 if source == 'news' else 0.8  # News is slightly more reliable
    recency_weight = 1.0  # Current day content gets full weight
    
    # Store unigrams
    for phrase, freq in frequency_scores['unigrams'].items():
        if len(phrase) > 2 and freq >= 2:  # Filter very short words and very rare terms
            tfidf_score = tfidf_scores.get(phrase, 0.0)
            trend_score = analyzer.calculate_trend_score(
                phrase, freq, tfidf_score, recency_weight, source_weight
            )
            
            add_or_update_trending_phrase(
                db=db,
                date=target_date,
                phrase=phrase,
                score=trend_score,
                frequency=freq,
                phrase_type='unigram',
                source=source
            )
    
    # Store bigrams
    for phrase, freq in frequency_scores['bigrams'].items():
        if freq >= 2:  # At least 2 occurrences
            tfidf_score = tfidf_scores.get(phrase, 0.0)
            trend_score = analyzer.calculate_trend_score(
                phrase, freq, tfidf_score, recency_weight, source_weight
            )
            
            add_or_update_trending_phrase(
                db=db,
                date=target_date,
                phrase=phrase,
                score=trend_score,
                frequency=freq,
                phrase_type='bigram',
                source=source
            )
    
    # Store trigrams
    for phrase, freq in frequency_scores['trigrams'].items():
        if freq >= 2:  # At least 2 occurrences
            tfidf_score = tfidf_scores.get(phrase, 0.0)
            trend_score = analyzer.calculate_trend_score(
                phrase, freq, tfidf_score, recency_weight, source_weight
            )
            
            add_or_update_trending_phrase(
                db=db,
                date=target_date,
                phrase=phrase,
                score=trend_score,
                frequency=freq,
                phrase_type='trigram',
                source=source
            )

def store_social_media_content(db: Session, posts: List[Dict]):
    """Store social media content in database"""
    for post_data in posts:
        # For social media, we'll store in the articles table with a special source prefix
        article = Article(
            title=f"Social Media Post - {post_data.get('source', 'unknown')}",
            description=post_data.get('content', ''),
            url=post_data.get('url', ''),
            published_date=post_data.get('scraped_date', date.today()),
            source=f"social_media_{post_data.get('source', 'unknown')}"
        )
        db.add(article)
    
    db.commit()
    print(f"Stored {len(posts)} social media posts in database")

def fetch_news():
    """Fetch news from multiple Bengali sources"""
    articles = []
    
    # Scrape Bengali news websites
    scraped_articles = scrape_bengali_news()
    articles.extend(scraped_articles)
    
    return articles

# List of Bangladeshi newspaper homepages for modular scraping
BANGLA_NEWS_SITES = [
    ("Prothom Alo", "https://www.prothomalo.com/"),
    ("Kaler Kantho", "https://www.kalerkantho.com/"),
    ("Jugantor", "https://www.jugantor.com/"),
    ("Ittefaq", "https://www.ittefaq.com.bd/"),
    ("Bangladesh Pratidin", "https://www.bd-pratidin.com/"),
    ("Manab Zamin", "https://mzamin.com/"),
    ("Samakal", "https://samakal.com/"),
    ("Amader Shomoy", "https://www.dainikamadershomoy.com/"),
    ("Janakantha", "https://www.dailyjanakantha.com/"),
    ("Inqilab", "https://dailyinqilab.com/"),
    ("Sangbad", "https://sangbad.net.bd/"),
    ("Noya Diganta", "https://www.dailynayadiganta.com/"),
    ("Jai Jai Din", "https://www.jaijaidinbd.com/"),
    ("Manobkantha", "https://www.manobkantha.com.bd/"),
    ("Ajkaler Khobor", "https://www.ajkalerkhobor.net/"),
    ("Ajker Patrika", "https://www.ajkerpatrika.com/"),
    ("Protidiner Sangbad", "https://www.protidinersangbad.com/"),
    ("Bangladesher Khabor", "https://www.bangladesherkhabor.net/"),
    ("Bangladesh Journal", "https://www.bd-journal.com/")
]

# Modular news scraping functions for each site (add more as needed)
def scrape_prothom_alo():
    articles = []
    seen_urls = set()
    try:
        feed_url = "https://www.prothomalo.com/feed/"
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            url = entry.get('link', '')
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            try:
                res = robust_request(url)
                if not res:
                    continue
                res.encoding = 'utf-8'  # Fix encoding
                soup = BeautifulSoup(res.text, "html.parser")
                # Only use h1 tags for headings
                headings = [tag.text.strip() for tag in soup.find_all('h1') if tag.text.strip()]
                heading_text = ' '.join(headings)
                # Apply stopword filtering
                cleaned_heading = clean_heading_text(heading_text)
                articles.append({
                    'title': headings[0] if headings else entry.get('title', ''),
                    'heading': cleaned_heading,
                    'url': url,
                    'published_date': datetime.now().date(),
                    'source': 'prothom_alo'
                })
            except Exception as e:
                print(f"Error scraping Prothom Alo article: {e}")
    except Exception as e:
        print(f"Error scraping Prothom Alo: {e}")
    return articles


def robust_request(url, timeout=50):
    try:
        return requests.get(url, timeout=timeout)
    except (Timeout, ConnectionError) as e:
        print(f"Timeout/ConnectionError scraping {url}: {e}")
        return None

def scrape_jugantor():
    articles = []
    # Only use these category URLs for Jugantor
    category_urls = [
        "https://www.jugantor.com/national",
        "https://www.jugantor.com/economics",
        "https://www.jugantor.com/politics",
        "https://www.jugantor.com/lifestyle",
        "https://www.jugantor.com/entertainment",
        "https://www.jugantor.com/sports",
        "https://www.jugantor.com/islam-life",
        "https://www.jugantor.com/job-seek",
        "https://www.jugantor.com/campus",
        "https://www.jugantor.com/disease",
        "https://www.jugantor.com/tech",
        "https://www.jugantor.com/international",
    ]
    import re
    try:
        candidate_urls = set()
        for category_url in category_urls:
            res = robust_request(category_url)
            if not res:
                continue
            soup = BeautifulSoup(res.text, "html.parser")
            count = 0
            for link in soup.select("h2 a, h3 a, a[href]"):
                if count >= 8:
                    break
                url = link.get('href')
                if not url:
                    continue
                # Normalize URL
                if not url.startswith('http'):
                    url = "https://www.jugantor.com/".rstrip('/') + '/' + url.lstrip('/')
                # Only keep URLs that end with a numeric ID (real articles)
                if re.search(r'/[0-9]{4,}$', url):
                    if url not in candidate_urls:
                        candidate_urls.add(url)
                        count += 1
        # Deduplicate and scrape articles
        for url in candidate_urls:
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                # Only use h1 tags for headings, remove duplicates
                headings = []
                seen = set()
                for tag in article_soup.find_all('h1'):
                    text = tag.text.strip()
                    if text and text not in seen:
                        headings.append(text)
                        seen.add(text)
                heading_text = ' '.join(headings)
                print(f"[scrape_jugantor] url: {url}\n  headings: {headings}")
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "jugantor"
                })
            except Exception as e:
                print(f"Error scraping Jugantor article: {e}")
    except Exception as e:
        print(f"Error scraping Jugantor category pages: {e}")
    return articles

def scrape_kaler_kantho():
    articles = []
    try:
        homepage = "https://www.kalerkantho.com/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        seen_urls = set()
        for link in soup.select("a[href*='/online/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                # Only use h1 tags for headings
                headings = [tag.text.strip() for tag in article_soup.find_all('h1') if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_kaler_kantho] url: {url}\n  headings: {headings}")
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "kaler_kantho"
                })
            except Exception as e:
                print(f"Error scraping Kaler Kantho article: {e}")
    except Exception as e:
        print(f"Error scraping Kaler Kantho homepage: {e}")
    return articles

def scrape_ittefaq():
    articles = []
    try:
        homepage = "https://www.ittefaq.com.bd/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        seen_urls = set()
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                # Only use h1 tags for headings
                headings = [tag.text.strip() for tag in article_soup.find_all('h1') if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_ittefaq] url: {url}\n  headings: {headings}")
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "ittefaq"
                })
            except Exception as e:
                print(f"Error scraping Ittefaq article: {e}")
    except Exception as e:
        print(f"Error scraping Ittefaq homepage: {e}")
    return articles

def scrape_bd_pratidin():
    articles = []
    try:
        homepage = "https://www.bd-pratidin.com/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        seen_urls = set()
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                # Only use h1 tags for headings
                headings = [tag.text.strip() for tag in article_soup.find_all('h1') if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_bd_pratidin] url: {url}\n  headings: {headings}")
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "bd_pratidin"
                })
            except Exception as e:
                print(f"Error scraping BD Pratidin article: {e}")
    except Exception as e:
        print(f"Error scraping BD Pratidin homepage: {e}")
    return articles

def scrape_manab_zamin():
    articles = []
    try:
        homepage = "https://mzamin.com/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        seen_urls = set()
        for link in soup.select("h3 a, h2 a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                # Only use h1 tags for headings
                headings = [tag.text.strip() for tag in article_soup.find_all('h1') if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_manab_zamin] url: {url}\n  headings: {headings}")
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "manab_zamin"
                })
            except Exception as e:
                print(f"Error scraping Manab Zamin article: {e}")
    except Exception as e:
        print(f"Error scraping Manab Zamin homepage: {e}")
    return articles

def scrape_samakal():
    articles = []
    try:
        homepage = "https://samakal.com/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        seen_urls = set()
        for link in soup.select("a[href*='samakal.com/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                # Only use h1 tags for headings
                headings = [tag.text.strip() for tag in article_soup.find_all('h1') if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_samakal] url: {url}\n  headings: {headings}")
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "samakal"
                })
            except Exception as e:
                print(f"Error scraping Samakal article: {e}")
    except Exception as e:
        print(f"Error scraping Samakal homepage: {e}")
    return articles

def scrape_amader_shomoy():
    articles = []
    try:
        homepage = "https://www.dainikamadershomoy.com/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        for link in soup.select("h2 a, h3 a, a[href*='/news/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                # Only use h1 tags for headings
                headings = [tag.text.strip() for tag in article_soup.find_all('h1') if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_amader_shomoy] url: {url}\n  headings: {headings}")
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "amader_shomoy"
                })
            except Exception as e:
                print(f"Error scraping Amader Shomoy article: {e}")
    except Exception as e:
        print(f"Error scraping Amader Shomoy homepage: {e}")
    return articles

def scrape_janakantha():
    articles = []
    try:
        homepage = "https://www.dailyjanakantha.com/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        for link in soup.select("a[href*='/news/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                # Only use h1 tags for headings
                headings = [tag.text.strip() for tag in article_soup.find_all('h1') if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_janakantha] url: {url}\n  headings: {headings}")
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "janakantha"
                })
            except Exception as e:
                print(f"Error scraping Janakantha article: {e}")
    except Exception as e:
        print(f"Error scraping Janakantha homepage: {e}")
    return articles

def scrape_inqilab():
    articles = []
    try:
        homepage = "https://dailyinqilab.com/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        seen_urls = set()
        for link in soup.select("h2 a, h3 a, a[href*='/news/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_inqilab] url: {url}\n  headings: {headings}")
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "inqilab"
                })
            except Exception as e:
                print(f"Error scraping Inqilab article: {e}")
    except Exception as e:
        print(f"Error scraping Inqilab homepage: {e}")
    return articles

def scrape_sangbad():
    articles = []
    section_urls = [
        "https://sangbad.net.bd/news/national/",
        "https://sangbad.net.bd/news/bangladesh/",
        "https://sangbad.net.bd/news/sports/",
        "https://sangbad.net.bd/news/entertainment/",
        "https://sangbad.net.bd/news/it/",
        "https://sangbad.net.bd/news/education/",
        "https://sangbad.net.bd/news/politics/",
        "https://sangbad.net.bd/news/campus/",
        "https://sangbad.net.bd/opinion/open-discussion/",
        "https://sangbad.net.bd/news/international/",
        
    ]
    seen_urls = set()
    for section_url in section_urls:
        res = robust_request(section_url)
        if not res:
            print(f"[scrape_sangbad] Failed to fetch section: {section_url}")
            continue
        soup = BeautifulSoup(res.text, "html.parser")
        section_candidate_urls = set()
        for link in soup.select("a[href*='/news/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = "https://sangbad.net.bd" + url
            if url and url not in seen_urls and '/news/' in url:
                section_candidate_urls.add(url)
                seen_urls.add(url)
            if len(section_candidate_urls) >= 15:
                break
        print(f"[scrape_sangbad] {section_url} -> {len(section_candidate_urls)} candidate article URLs for this section.")
        for url in list(section_candidate_urls):
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                heading_tag = article_soup.find('h2')
                heading = heading_tag.text.strip() if heading_tag and heading_tag.text.strip() else ""
                print(f"[scrape_sangbad] url: {url}\n  heading: {heading}")
                articles.append({
                    "title": heading,
                    "heading": heading,
                    "url": url,
                    "published_date": datetime.now().date().isoformat(),
                    "source": "sangbad"
                })
            except Exception as e:
                print(f"Error scraping Sangbad article: {e}")
    print(f"[scrape_sangbad] Scraped {len(articles)} articles.")
    return articles

def scrape_noya_diganta():
    articles = []
    seen_urls = set()
    try:
        homepage = "https://www.dailynayadiganta.com/"
        res = robust_request(homepage)
        if not res:
            return articles
        
        # Fix encoding issue - explicitly set UTF-8
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, "html.parser")
        
        for link in soup.select("h2 a, h3 a, a[href*='/news/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                # Fix encoding for article page too
                article_res.encoding = 'utf-8'
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                
                # Extract headings from h1, h2, h3 tags
                headings = []
                for tag in article_soup.find_all(['h1', 'h2', 'h3']):
                    if tag.text.strip():
                        headings.append(tag.text.strip())
                
                if headings:
                    heading_text = ' '.join(headings)
                    # Apply stopword filtering
                    cleaned_heading = clean_heading_text(heading_text)
                    
                    print(f"[scrape_noya_diganta] url: {url}\n  headings: {headings[:2]}")
                    articles.append({
                        "title": headings[0],
                        "heading": cleaned_heading,
                        "url": url,
                        "published_date": datetime.now().date(),
                        "source": "noya_diganta"
                    })
            except Exception as e:
                print(f"Error scraping Noya Diganta article: {e}")
    except Exception as e:
        print(f"Error scraping Noya Diganta homepage: {e}")
    return articles

def scrape_jai_jai_din():
    articles = []
    try:
        homepage = "https://www.jaijaidinbd.com/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        for link in soup.select("h2 a, h3 a, a[href*='/news/'], a[href*='/details/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                # Only use h1 tags for headings
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1','h2']) if tag.text.strip()]
                heading_text = ' '.join(headings)
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "jai_jai_din"
                })
            except Exception as e:
                print(f"Error scraping Jai Jai Din article: {e}")
    except Exception as e:
        print(f"Error scraping Jai Jai Din homepage: {e}")
    return articles

def scrape_manobkantha():
    articles = []
    try:
        homepage = "https://www.manobkantha.com.bd/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        seen_urls = set()
        for link in soup.select("h2 a, h3 a, a[href*='/news/'], a[href*='/details/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            # Deduplicate by URL before scraping
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                # Only use h1 and h2 tags for headings
                headings = [tag.text.strip() for tag in article_soup.find_all('h1') if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_manobkantha] url: {url}\n  headings: {headings}")
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "manobkantha"
                })
            except Exception as e:
                print(f"Error scraping Manobkantha article: {e}")
    except Exception as e:
        print(f"Error scraping Manobkantha homepage: {e}")
    return articles

def scrape_ajkaler_khobor():
    articles = []
    try:
        homepage = "https://www.ajkalerkhobor.net/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                # Only use h1 and h2 tags for headings
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_ajkaler_khobor] url: {url}\n  headings: {headings}")
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "ajkaler_khobor"
                })
            except Exception as e:
                print(f"Error scraping Ajkaler Khobor article: {e}")
    except Exception as e:
        print(f"Error scraping Ajkaler Khobor homepage: {e}")
    return articles

def scrape_ajker_patrika():
    """
    Improved Ajker Patrika scraper that:
    1. Extracts category URLs from homepage
    2. Visits each category page to find actual article links
    3. Scrapes actual articles from those links
    """
    articles = []
    seen_urls = set()
    
    print("[scrape_ajker_patrika] Starting improved Ajker Patrika scraper...")
    
    try:
        homepage = "https://www.ajkerpatrika.com/"
        print(f"[scrape_ajker_patrika] Step 1: Fetching homepage: {homepage}")
        
        res = robust_request(homepage, timeout=15)
        if not res:
            print("[scrape_ajker_patrika] Failed to fetch homepage")
            return articles
            
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Define category URLs to explore (based on previous test results)
        category_urls = [
            "https://www.ajkerpatrika.com/bangladesh",     # সারা দেশ
            "https://www.ajkerpatrika.com/international",  # বিশ্ব  
            "https://www.ajkerpatrika.com/business",       # অর্থনীতি
            "https://www.ajkerpatrika.com/sports",         # খেলা
            "https://www.ajkerpatrika.com/entertainment",  # বিনোদন
            "https://www.ajkerpatrika.com/lifestyle",      # জীবনধারা
            "https://www.ajkerpatrika.com/technology",     # প্রযুক্তি
            "https://www.ajkerpatrika.com/health",         # স্বাস্থ্য
            "https://www.ajkerpatrika.com/education"       # শিক্ষা
        ]
        
        article_links = []
        
        print(f"[scrape_ajker_patrika] Step 2: Exploring {len(category_urls)} category pages for article links...")
        
        # Explore each category page to find article links
        for i, category_url in enumerate(category_urls):
            if len(article_links) >= 50:  # Limit total articles to prevent overload
                break
                
            print(f"[scrape_ajker_patrika] [{i+1}/{len(category_urls)}] Exploring category: {category_url}")
            
            cat_res = robust_request(category_url, timeout=10)
            if not cat_res:
                print(f"[scrape_ajker_patrika] Failed to fetch category: {category_url}")
                continue
                
            cat_res.encoding = 'utf-8'
            cat_soup = BeautifulSoup(cat_res.text, "html.parser")
            
            # Look for article links using various selectors
            article_selectors = [
                'h1 a[href]', 'h2 a[href]', 'h3 a[href]',  # Headlines with links
                'a[href*="details"]', 'a[href*="news"]', 'a[href*="story"]',  # Article URL patterns
                '.headline a', '.title a', '.news-title a',  # Common CSS classes
                '.article-title a', '.content a[href*="/"]',  # More patterns
                'article a[href]', '.post a[href]'  # Article containers
            ]
            
            category_articles = 0
            for selector in article_selectors:
                try:
                    links = cat_soup.select(selector)
                    for link in links:
                        href = link.get('href', '')
                        if not href:
                            continue
                            
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            full_url = "https://www.ajkerpatrika.com" + href
                        elif href.startswith('https://www.ajkerpatrika.com'):
                            full_url = href
                        else:
                            continue
                        
                        # Skip non-article URLs
                        if any(skip in full_url.lower() for skip in [
                            'javascript:', 'mailto:', '#', 'facebook.com', 'twitter.com',
                            'youtube.com', 'instagram.com', '.jpg', '.png', '.pdf',
                            '/topic/', '/tag/', '/author/', '/page/', '/search/'
                        ]):
                            continue
                        
                        # Skip if it's just a category URL (no additional path segments)
                        url_parts = full_url.replace('https://www.ajkerpatrika.com', '').strip('/')
                        if not url_parts or url_parts in ['bangladesh', 'international', 'business', 'sports', 'entertainment', 'lifestyle', 'technology', 'health', 'education']:
                            continue
                        
                        # Add unique article URLs
                        if full_url not in seen_urls:
                            article_links.append(full_url)
                            seen_urls.add(full_url)
                            category_articles += 1
                            
                        if category_articles >= 10:  # Limit per category
                            break
                    
                    if category_articles >= 10:
                        break
                        
                except Exception as e:
                    print(f"[scrape_ajker_patrika] Error with selector '{selector}': {e}")
                    continue
            
            print(f"[scrape_ajker_patrika] Found {category_articles} article links in this category")
        
        print(f"[scrape_ajker_patrika] Step 3: Found {len(article_links)} total article URLs. Starting article scraping...")
        
        # Now scrape the actual articles
        for i, article_url in enumerate(article_links[:30]):  # Limit to 30 articles
            print(f"[scrape_ajker_patrika] [{i+1}/{min(30, len(article_links))}] Scraping article: {article_url}")
            
            article_res = robust_request(article_url, timeout=8)
            if not article_res:
                print(f"[scrape_ajker_patrika] Failed to fetch article: {article_url}")
                continue
                
            try:
                article_res.encoding = 'utf-8'
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                
                # Extract article title using multiple strategies
                title = None
                title_selectors = [
                    'h1.headline', 'h1.title', 'h1.article-title',  # Specific classes
                    'h1', 'h2',  # Generic headers
                    '.headline', '.title', '.article-title',  # Class-based
                    'title'  # Fallback to page title
                ]
                
                for selector in title_selectors:
                    try:
                        elements = article_soup.select(selector)
                        if elements:
                            candidate_title = elements[0].get_text(strip=True)
                            
                            # Clean up title
                            for cleanup in ['আজকের পত্রিকা', 'Ajker Patrika', '|', '-', 'Ajker Patrika -']:
                                candidate_title = candidate_title.replace(cleanup, '').strip()
                            
                            # Accept if it's a reasonable length and not just category names
                            if (candidate_title and len(candidate_title) > 10 and 
                                candidate_title not in ['সারা দেশ', 'বিশ্ব', 'অর্থনীতি', 'খেলা', 'বিনোদন', 'জীবনধারা', 'প্রযুক্তি']):
                                title = candidate_title
                                break
                    except:
                        continue
                
                if title and len(title) > 10:
                    # Apply stopword filtering
                    cleaned_heading = clean_heading_text(title)
                    
                    if cleaned_heading and len(cleaned_heading.strip()) > 5:
                        print(f"[scrape_ajker_patrika] ✅ Article found: {title[:60]}...")
                        
                        articles.append({
                            "title": title,
                            "heading": cleaned_heading,
                            "url": article_url,
                            "published_date": datetime.now().date(),
                            "source": "ajker_patrika"
                        })
                    else:
                        print(f"[scrape_ajker_patrika] ❌ Filtered out (stopwords): {title[:40]}...")
                else:
                    print(f"[scrape_ajker_patrika] ❌ No valid title found for: {article_url}")
                    
            except Exception as e:
                print(f"[scrape_ajker_patrika] Error processing article {article_url}: {e}")
        
        print(f"[scrape_ajker_patrika] ✅ Scraping completed! Found {len(articles)} valid articles")
        
    except Exception as e:
        print(f"[scrape_ajker_patrika] Main error: {e}")
        import traceback
        traceback.print_exc()
        
    return articles

def scrape_protidiner_sangbad():
    articles = []
    try:
        homepage = "https://www.protidinersangbad.com/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        seen_urls = set()
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                # Only use h1 tags for headings
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1','h2']) if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_protidiner_sangbad] url: {url}\n  headings: {headings}")
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "protidiner_sangbad"
                })
            except Exception as e:
                print(f"Error scraping Protidiner Sangbad article: {e}")
    except Exception as e:
        print(f"Error scraping Protidiner Sangbad homepage: {e}")
    return articles

def scrape_bangladesher_khabor():
    articles = []
    try:
        homepage = "https://www.bangladesherkhabor.net/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        for link in soup.select("h2 a, h3 a, a[href*='/news/'], a[href*='/details/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                # Only use h1 tags for headings
                headings = [tag.text.strip() for tag in article_soup.find_all('h1') if tag.text.strip()]
                heading_text = ' '.join(headings)
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "bangladesher_khabor"
                })
            except Exception as e:
                print(f"Error scraping Bangladesher Khabor article: {e}")
    except Exception as e:
        print(f"Error scraping Bangladesher Khabor homepage: {e}")
    return articles

def scrape_bangladesh_journal():
    articles = []
    try:
        homepage = "https://www.bd-journal.com/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        for link in soup.select("h2 a, h3 a, a[href*='/news/'], a[href*='/details/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                # Only use h1 tags for headings
                headings = [tag.text.strip() for tag in article_soup.find_all('h1') if tag.text.strip()]
                heading_text = ' '.join(headings)
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "bangladesh_journal"
                })
            except Exception as e:
                print(f"Error scraping Bangladesh Journal article: {e}")
    except Exception as e:
        print(f"Error scraping Bangladesh Journal homepage: {e}")
    return articles

# Update scrape_bengali_news to call all scrapers
def scrape_bengali_news() -> List[Dict]:
    """Scrape Bengali news from multiple sources (modular, only user-supplied sites)"""
    articles = []
    source_counts = {}
    all_sources = [
        ("prothom_alo", scrape_prothom_alo),
        ("kaler_kantho", scrape_kaler_kantho),
        ("jugantor", scrape_jugantor),
            # ("ittefaq", scrape_ittefaq),
            # ("bd_pratidin", scrape_bd_pratidin),
            # ("manab_zamin", scrape_manab_zamin),
        ("samakal", scrape_samakal),
        # ("amader_shomoy", scrape_amader_shomoy),
        ("janakantha", scrape_janakantha),
        ("inqilab", scrape_inqilab),
        ("sangbad", scrape_sangbad),
        ("noya_diganta", scrape_noya_diganta),
        # ("jai_jai_din", scrape_jai_jai_dিন),
        ("manobkantha", scrape_manobkantha),
            # ("ajkaler_khobor", scrape_ajkaler_khobor),
        # ("ajker_patrika", scrape_ajker_patrika),
        ("protidiner_sangbad", scrape_protidiner_sangbad),
        # New category scrapers
        ("sahitya_sanskriti", scrape_sahitya_sanskriti),
        ("ethnic_minorities", scrape_ethnic_minorities),
        # ("bangladesher_khabor", scrape_bangladesher_khabor),
        # ("bangladesh_journal", scrape_bangladesh_journal)
    ]
    print("\n[Scraping: Starting all newspaper scrapers]")
    for source, func in all_sources:
        print(f" Calling {func.__name__}() for {source}...")
        src_articles = func()
        print(f" {func.__name__}() returned {len(src_articles)} articles.")
        if src_articles:
            for art in src_articles[:3]:
                print(f"    url: {art.get('url', '')} | heading: {art.get('heading', '')[:60]}")
        source_counts[source] = len(src_articles)
        articles.extend(src_articles)
    # Deduplicate by URL
    seen_urls = set()
    deduped_articles = []
    for art in articles:
        url = art.get('url')
        if url and url not in seen_urls:
            deduped_articles.append(art)
            seen_urls.add(url)
    print("\n[Scraping Summary]")
    for source, count in source_counts.items():
        print(f"  {source}: {count} articles scraped")
    print(f"  Total (after deduplication): {len(deduped_articles)} unique articles")
    return deduped_articles

def store_news(db: Session, articles: List[Dict]):
    """Store news articles in database"""
    for article_data in articles:
        # Use heading as description if description is not available
        description = article_data.get('description') or article_data.get('heading') or ''
        
        article = Article(
            title=article_data.get('title', ''),
            description=description,  # Use heading if description is not available
            url=article_data.get('url', ''),
            published_date=article_data.get('published_date'),
            source=article_data.get('source', 'unknown')
        )
        db.add(article)
    
    db.commit()
    print(f"Stored {len(articles)} articles in database")

def fetch_social_media_posts():
    # try:
    #     posts = scrape_social_media_content()
    #     print(f"Fetched {len(posts)} social media posts")
    #     return posts
    # except Exception as e:
    #     print(f"Error fetching social media posts: {e}")
    #     return []
    return []

def parse_news(articles: List[Dict]) -> str:
    """Parse articles into combined text"""
    combined_texts = []
    for article in articles:
        title = article.get('title', '')
        description = article.get('description', '')
        combined_texts.append(f"{title}। {description}")
    
    return "\n".join(combined_texts)

# --- STUB: optimize_text_for_ai_analysis_with_categories ---
def optimize_text_for_ai_analysis_with_categories(articles_with_metadata, analyzer, max_chars=12000, max_articles=150, enable_categories=True):
    """
    Use all available newspaper article headings/titles for category-wise LLM analysis, with NO truncation or article limit.
    This implementation ignores max_chars and max_articles for newspaper content.
    Only uses 'heading' or 'title' fields, never 'content'.
    """
    combined_texts = []
    for article in articles_with_metadata:
        # Use heading if available, else title
        text = article.get('heading') or article.get('title')
        if text:
            combined_texts.append(text.strip())
    return "\n".join(combined_texts)

# --- STUB: process_mixed_content_for_llm ---
def process_mixed_content_for_llm(articles_with_metadata, social_media_content, analyzer, max_chars=12000):
    """Stub for process_mixed_content_for_llm. Implement as needed."""
    raise NotImplementedError("process_mixed_content_for_llm is not yet implemented. Please implement this function.")

# --- STUB: optimize_text_for_ai_analysis ---
def optimize_text_for_ai_analysis(all_texts, analyzer, max_chars=12000, max_articles=150):
    """Stub for optimize_text_for_ai_analysis. Implement as needed."""
    raise NotImplementedError("optimize_text_for_ai_analysis is not yet implemented. Please implement this function.")

# --- STUB: create_mixed_content_llm_prompt ---
def create_mixed_content_llm_prompt(combined_text, limit):
    """Stub for create_mixed_content_llm_prompt. Implement as needed."""
    raise NotImplementedError("create_mixed_content_llm_prompt is not yet implemented. Please implement this function.")

# --- IMPLEMENTATION: analyze_trending_content_and_store ---
def analyze_trending_content_and_store(db: Session, analyzer, content: list, source: str, target_date: date):
    """
    Analyze a list of articles/posts for trending words/phrases and store results in the TrendingPhrase table.
    - db: SQLAlchemy session
    - analyzer: TrendingAnalyzer or compatible
    - content: list of dicts (articles or posts)
    - source: 'news' or 'social_media'
    - target_date: date for which to store results
    """
    # Prepare text data (use heading or title)
    texts = []
    for item in content:
        if item.get('heading'):
            texts.append(item['heading'])
        elif item.get('title'):
            texts.append(item['title'])
    if not texts:
        return
    # Calculate frequency scores
    frequency_scores = analyzer.calculate_frequency_scores(texts)
    # Apply quality filtering
    frequency_scores['unigrams'] = analyzer.filter_quality_phrases(frequency_scores['unigrams'])
    frequency_scores['bigrams'] = analyzer.filter_quality_phrases(frequency_scores['bigrams'])
    frequency_scores['trigrams'] = analyzer.filter_quality_phrases(frequency_scores['trigrams'])
    # Calculate TF-IDF scores
    tfidf_scores = analyzer.calculate_tfidf_scores(texts)
    # Set weights
    source_weight = 1.0 if source == 'news' else 0.8
    recency_weight = 1.0
    # Store unigrams
    for phrase, freq in frequency_scores['unigrams'].items():
        if len(phrase) > 2 and freq >= 2:
            tfidf_score = tfidf_scores.get(phrase, 0.0)
            trend_score = analyzer.calculate_trend_score(
                phrase, freq, tfidf_score, recency_weight, source_weight
            )
            add_or_update_trending_phrase(
                db=db,
                date=target_date,
                phrase=phrase,
                score=trend_score,
                frequency=freq,
                phrase_type='unigram',
                source=source
            )
    # Store bigrams
    for phrase, freq in frequency_scores['bigrams'].items():
        if freq >= 2:
            tfidf_score = tfidf_scores.get(phrase, 0.0)
            trend_score = analyzer.calculate_trend_score(
                phrase, freq, tfidf_score, recency_weight, source_weight
            )
            add_or_update_trending_phrase(
                db=db,
                date=target_date,
                phrase=phrase,
                score=trend_score,
                frequency=freq,
                phrase_type='bigram',
                source=source
            )
    # Store trigrams
    for phrase, freq in frequency_scores['trigrams'].items():
        if freq >= 2:
            tfidf_score = tfidf_scores.get(phrase, 0.0)
            trend_score = analyzer.calculate_trend_score(
                phrase, freq, tfidf_score, recency_weight, source_weight
            )
            add_or_update_trending_phrase(
                db=db,
                date=target_date,
                phrase=phrase,
                score=trend_score,
                frequency=freq,
                phrase_type='trigram',
                source=source
            )

def add_or_update_trending_phrase(db: Session, date, phrase, score, frequency, phrase_type, source):
    """
    Add a new trending phrase or update existing one with proper frequency management
    """
    from sqlalchemy.exc import IntegrityError
    
    try:
        # Try to insert new phrase
        trending_phrase = TrendingPhrase(
            date=date,
            phrase=phrase,
            score=score,
            frequency=frequency,
            phrase_type=phrase_type,
            source=source
        )
        db.add(trending_phrase)
        db.flush()  # Force the insert to check constraint
        return trending_phrase
        
    except IntegrityError:
        # Phrase already exists, update it
        db.rollback()
        
        existing_phrase = db.query(TrendingPhrase).filter(
            TrendingPhrase.date == date,
            TrendingPhrase.phrase == phrase,
            TrendingPhrase.phrase_type == phrase_type,
            TrendingPhrase.source == source
        ).first()
        
        if existing_phrase:
            # Update frequency and recalculate score
            existing_phrase.frequency += frequency
            # Take the higher score between existing and new
            existing_phrase.score = max(existing_phrase.score, score)
            return existing_phrase
            
        # If we get here, something went wrong
        return None

def scrape_sahitya_sanskriti():
    """Scrape সাহিত্য-সংস্কৃতি (Literature & Culture) news from multiple sources"""
    articles = []
    seen_urls = set()
    
    # URLs provided for সাহিত্য-সংস্কৃতি category
    category_urls = [
        "https://www.prothomalo.com/topic/%E0%A6%B8%E0%A6%BE%E0%A6%B9%E0%A6%BF%E0%A6%A4%E0%A7%8D%E0%A6%AF",
        "https://campustimes.press/catcn/literature",
        "https://dainiksylhet.com/newscat/literature",
        "https://www.jagonews24.com/literature",
        "https://www.shomoynews.net/topic/literature",
        "https://deshbarta24.com/category/literature",
        "https://www.seshbarta.com/category/%E0%A6%B8%E0%A6%BE%E0%A6%B9%E0%A6%BF%E0%A6%A4%E0%A7%8D%E0%A6%AF/",
        "https://ekush.info/category/%E0%A6%B8%E0%A6%BE%E0%A6%B9%E0%A6%BF%E0%A6%A4%E0%A7%8D%E0%A6%AF/",
        "https://www.bbc.com/bengali/topics/cjgn72njz4zt",
        "https://bangla.bdnews24.com/arts/",
        "https://www.ntvbd.com/arts-and-literature",
        "https://www.banglatribune.com/literature",
        "https://bangla.thedailystar.net/literature",
        "https://shamolbangla24.com/category/%e0%a6%b8%e0%a6%be%e0%a6%b9%e0%a6%bf%e0%a6%a4%e0%a7%8d%e0%a6%af/",
        "https://banglamailnews.com/category/%e0%a6%b8%e0%a6%be%e0%a6%b9%e0%a6%bf%e0%a6%a4%e0%a7%8d%e0%a6%af/",
        "https://www.ekusheysangbad.com/literature",
        "https://deeptonews.com/category/%E0%A6%B8%E0%A6%BE%E0%A6%B9%E0%A6%BF%E0%A6%A4%E0%A7%8D%E0%A6%AF/",
        "https://www.channel24bd.tv/art-literature",
        "https://www.kalerkantho.com/online/sahitya",
        "https://dainikazadi.net/category/feature/literary-weekly/",
        "https://bangla.thedailystar.net/literature",
        "https://samakal.com/sahitto-o-sangskriti",
        "https://www.somoynews.tv/categories/%E0%A6%B8%E0%A6%BE%E0%A6%B9%E0%A6%BF%E0%A6%A4%E0%A7%8D%E0%A6%AF-%E0%A6%93-%E0%A6%B8%E0%A6%82%E0%A6%B8%E0%A7%8D%E0%A6%95%E0%A7%83%E0%A6%A4%E0%A6%BF",
        "https://www.janomot.com/news-category/13/%E0%A6%B8%E0%A6%BE%E0%A6%B9%E0%A6%BF%E0%A6%A4%E0%A7%8D%E0%A6%AF-%E0%A6%B8%E0%A6%82%E0%A6%B8%E0%A7%8D%E0%A6%95%E0%A7%83%E0%A6%A4%E0%A6%BF",
        "https://www.eibela.com/category/12/%E0%A6%B8%E0%A6%BE%E0%A6%B9%E0%A6%BF%E0%A6%A4%E0%A7%8D%E0%A6%AF-%E0%A6%B8%E0%A6%82%E0%A6%B8%E0%A7%8D%E0%A6%95%E0%A7%83%E0%A6%A4%E0%A6%BF",
        "https://www.dhakatoday.com/%E0%A6%B8%E0%A6%BE%E0%A6%B9%E0%A6%BF%E0%A6%A4%E0%A7%8D%E0%A6%AF-%E0%A6%B8%E0%A6%82%E0%A6%B8%E0%A7%8D%E0%A6%95%E0%A7%83%E0%A6%A4%E0%A6%BF"
    ]
    
    print(f"[scrape_sahitya_sanskriti] Starting with {len(category_urls)} URLs")
    
    for url in category_urls:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        try:
            print(f"[scrape_sahitya_sanskriti] Scraping: {url}")
            res = robust_request(url)
            if not res:
                print(f"[scrape_sahitya_sanskriti] Failed to fetch: {url}")
                continue
            
            # Set encoding explicitly to handle Bengali text properly
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Extract article links from common selectors
            article_links = soup.select("h2 a, h3 a, h4 a, .title a, .headline a, a[href*='/news/'], a[href*='/article/'], a[href*='/story/']")
            
            for link in article_links[:5]:  # Limit to 5 articles per source
                article_url = link.get('href')
                if not article_url:
                    continue
                    
                # Convert relative URLs to absolute
                if not article_url.startswith('http'):
                    base_url = '/'.join(url.split('/')[:3])
                    article_url = base_url + '/' + article_url.lstrip('/')
                
                if article_url in seen_urls:
                    continue
                seen_urls.add(article_url)
                
                # Scrape individual article
                article_res = robust_request(article_url)
                if not article_res:
                    continue
                
                try:
                    article_res.encoding = 'utf-8'
                    article_soup = BeautifulSoup(article_res.text, "html.parser")
                    
                    # Extract headings
                    headings = []
                    for tag in article_soup.find_all(['h1', 'h2', 'h3']):
                        if tag.text.strip():
                            headings.append(tag.text.strip())
                    
                    if headings:
                        heading_text = ' '.join(headings)
                        # Apply stopword filtering
                        cleaned_heading = clean_heading_text(heading_text)
                        
                        articles.append({
                            "title": headings[0],
                            "heading": cleaned_heading,
                            "url": article_url,
                            "published_date": datetime.now().date(),
                            "source": "sahitya_sanskriti",
                            "category": "সাহিত্য-সংস্কৃতি"
                        })
                        print(f"[scrape_sahitya_sanskriti] Added article: {headings[0][:50]}...")
                
                except Exception as e:
                    print(f"[scrape_sahitya_sanskriti] Error scraping article {article_url}: {e}")
                    
        except Exception as e:
            print(f"[scrape_sahitya_sanskriti] Error scraping {url}: {e}")
    
    print(f"[scrape_sahitya_sanskriti] Total articles scraped: {len(articles)}")
    return articles

def scrape_ethnic_minorities():
    """Scrape ক্ষুদ্র নৃগোষ্ঠী (Ethnic Minorities) news from multiple sources"""
    articles = []
    seen_urls = set()
    
    # URLs provided for ক্ষুদ্র নৃগোষ্ঠী category
    category_urls = [
        "https://bangla.bdnews24.com/topic/%E0%A6%95%E0%A7%8D%E0%A6%B7%E0%A7%81%E0%A6%A6%E0%A7%8D%E0%A6%B0%20%E0%A6%A8%E0%A7%83%E0%A6%97%E0%A7%8B%E0%A6%B7%E0%A7%8D%E0%A6%A0%E0%A7%80",
        "https://www.parbattanews.com/tag/%E0%A6%95%E0%A7%8D%E0%A6%B7%E0%A7%81%E0%A6%A6%E0%A7%8D%E0%A6%B0-%E0%A6%A8%E0%A7%83%E0%A6%97%E0%A7%8B%E0%A6%B7%E0%A7%8D%E0%A6%A0%E0%A7%80/",
        "https://www.khaborerkagoj.com/topic/3942",
        "https://www.ajkerpatrika.com/topic/%E0%A6%95%E0%A7%8D%E0%A6%B7%E0%A7%81%E0%A6%A6%E0%A7%8D%E0%A6%B0%20%E0%A6%A8%E0%A7%83-%E0%A6%97%E0%A7%8B%E0%A6%B7%E0%A7%8D%E0%A6%A0%E0%A7%80",
        "https://www.prothomalo.com/topic/%E0%A6%95%E0%A7%8D%E0%A6%B7%E0%A7%81%E0%A6%A6%E0%A7%8D%E0%A6%B0-%E0%A6%9C%E0%A6%BE%E0%A6%A4%E0%A6%BF%E0%A6%97%E0%A7%8B%E0%A6%B7%E0%A7%8D%E0%A6%A0%E0%A7%80",
        "https://www.prothomalo.com/topic/%E0%A6%86%E0%A6%A6%E0%A6%BF%E0%A6%AC%E0%A6%BE%E0%A6%B8%E0%A7%80",
        "https://www.rajneete.com/topic/%E0%A6%95%E0%A7%8D%E0%A6%B7%E0%A7%81%E0%A6%A6%E0%A7%8D%E0%A6%B0-%E0%A6%A8%E0%A7%83-%E0%A6%97%E0%A7%8B%E0%A6%B7%E0%A7%8D%E0%A6%A0%E0%A7%80",
        "https://paharerkhabor.com/news/category/%E0%A6%95%E0%A7%8D%E0%A6%B7%E0%A7%81%E0%A6%A6%E0%A7%8D%E0%A6%B0-%E0%A6%A8%E0%A7%83-%E0%A6%97%E0%A7%8B%E0%A6%B7%E0%A7%8D%E0%A6%A0%E0%A7%80",
        "https://www.risingbd.com/tags/tribe",
        "https://samakal.com/topic/%E0%A6%86%E0%A6%A6%E0%A6%BF%E0%A6%AC%E0%A6%BE%E0%A6%B8%E0%A7%80",
        "https://www.desh.tv/topic/%E0%A6%86%E0%A6%A6%E0%A6%BF%E0%A6%AC%E0%A6%BE%E0%A6%B8%E0%A7%80",
        "https://www.tbsnews.net/bangla/tags/%E0%A6%86%E0%A6%A6%E0%A6%BF%E0%A6%AC%E0%A6%BE%E0%A6%B8%E0%A7%80",
        "https://nagorik.prothomalo.com/topic/%E0%A6%86%E0%A6%A6%E0%A6%BF%E0%A6%AC%E0%A6%BE%E0%A6%B8%E0%A7%80",
        "https://www.somoynews.tv/topic/%E0%A6%86%E0%A6%A6%E0%A6%BF%E0%A6%AC%E0%A6%BE%E0%A6%B8%E0%A7%80",
        "https://www.ittefaq.com.bd/topic/%E0%A6%86%E0%A6%A6%E0%A6%BF%E0%A6%AC%E0%A6%BE%E0%A6%B8%E0%A7%80"
    ]
    
    print(f"[scrape_ethnic_minorities] Starting with {len(category_urls)} URLs")
    
    for url in category_urls:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        try:
            print(f"[scrape_ethnic_minorities] Scraping: {url}")
            res = robust_request(url)
            if not res:
                print(f"[scrape_ethnic_minorities] Failed to fetch: {url}")
                continue
            
            # Set encoding explicitly to handle Bengali text properly
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Extract article links from common selectors
            article_links = soup.select("h2 a, h3 a, h4 a, .title a, .headline a, a[href*='/news/'], a[href*='/article/'], a[href*='/story/']")
            
            for link in article_links[:5]:  # Limit to 5 articles per source
                article_url = link.get('href')
                if not article_url:
                    continue
                    
                # Convert relative URLs to absolute
                if not article_url.startswith('http'):
                    base_url = '/'.join(url.split('/')[:3])
                    article_url = base_url + '/' + article_url.lstrip('/')
                
                if article_url in seen_urls:
                    continue
                seen_urls.add(article_url)
                
                # Scrape individual article
                article_res = robust_request(article_url)
                if not article_res:
                    continue
                
                try:
                    article_res.encoding = 'utf-8'
                    article_soup = BeautifulSoup(article_res.text, "html.parser")
                    
                    # Extract headings
                    headings = []
                    for tag in article_soup.find_all(['h1', 'h2', 'h3']):
                        if tag.text.strip():
                            headings.append(tag.text.strip())
                    
                    if headings:
                        heading_text = ' '.join(headings)
                        # Apply stopword filtering
                        cleaned_heading = clean_heading_text(heading_text)
                        
                        articles.append({
                            "title": headings[0],
                            "heading": cleaned_heading,
                            "url": article_url,
                            "published_date": datetime.now().date(),
                            "source": "ethnic_minorities",
                            "category": "ক্ষুদ্র নৃগোষ্ঠী"
                        })
                        print(f"[scrape_ethnic_minorities] Added article: {headings[0][:50]}...")
                
                except Exception as e:
                    print(f"[scrape_ethnic_minorities] Error scraping article {article_url}: {e}")
                    
        except Exception as e:
            print(f"[scrape_ethnic_minorities] Error scraping {url}: {e}")
    
    print(f"[scrape_ethnic_minorities] Total articles scraped: {len(articles)}")
    return articles
