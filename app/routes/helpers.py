import os
import re
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
            
            trending_phrase = TrendingPhrase(
                date=target_date,
                phrase=phrase,
                score=trend_score,
                frequency=freq,
                phrase_type='unigram',
                source=source
            )
            db.add(trending_phrase)
    
    # Store bigrams
    for phrase, freq in frequency_scores['bigrams'].items():
        if freq >= 2:  # At least 2 occurrences
            tfidf_score = tfidf_scores.get(phrase, 0.0)
            trend_score = analyzer.calculate_trend_score(
                phrase, freq, tfidf_score, recency_weight, source_weight
            )
            
            trending_phrase = TrendingPhrase(
                date=target_date,
                phrase=phrase,
                score=trend_score,
                frequency=freq,
                phrase_type='bigram',
                source=source
            )
            db.add(trending_phrase)
    
    # Store trigrams
    for phrase, freq in frequency_scores['trigrams'].items():
        if freq >= 2:  # At least 2 occurrences
            tfidf_score = tfidf_scores.get(phrase, 0.0)
            trend_score = analyzer.calculate_trend_score(
                phrase, freq, tfidf_score, recency_weight, source_weight
            )
            
            trending_phrase = TrendingPhrase(
                date=target_date,
                phrase=phrase,
                score=trend_score,
                frequency=freq,
                phrase_type='trigram',
                source=source
            )
            db.add(trending_phrase)

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
    try:
        feed_url = "https://www.prothomalo.com/feed/"
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:10]:
            url = entry.get('link', '')
            try:
                res = robust_request(url)
                if not res:
                    continue
                soup = BeautifulSoup(res.text, "html.parser")
                headings = []
                for tag in soup.find_all(['h1', 'h2']):
                    if tag.text.strip():
                        headings.append(tag.text.strip())
                heading_text = ' '.join(headings)
                articles.append({
                    'title': headings[0] if headings else entry.get('title', ''),
                    'heading': heading_text,
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
    try:
        homepage = "https://www.jugantor.com/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        for link in soup.select("h2 a, h3 a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
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
        print(f"Error scraping Jugantor homepage: {e}")
    return articles

def scrape_kaler_kantho():
    articles = []
    try:
        homepage = "https://www.kalerkantho.com/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        for link in soup.select("a[href*='/online/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
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
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
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
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
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
        for link in soup.select("h3 a, h2 a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
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
        for link in soup.select("a[href*='samakal.com/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
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
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
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
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
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
        for link in soup.select("h2 a, h3 a, a[href*='/news/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
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
    try:
        homepage = "https://sangbad.net.bd/"
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
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_sangbad] url: {url}\n  headings: {headings}")
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "sangbad"
                })
            except Exception as e:
                print(f"Error scraping Sangbad article: {e}")
    except Exception as e:
        print(f"Error scraping Sangbad homepage: {e}")
    return articles

def scrape_noya_diganta():
    articles = []
    try:
        homepage = "https://www.dailynayadiganta.com/"
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
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_noya_diganta] url: {url}\n  headings: {headings}")
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
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
                # Collect all h1 and h2 headings as a single string
                headings = []
                for tag in article_soup.find_all(['h1', 'h2']):
                    if tag.text.strip():
                        headings.append(tag.text.strip())
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
        for link in soup.select("h2 a, h3 a, a[href*='/news/'], a[href*='/details/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
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
    articles = []
    try:
        homepage = "https://www.ajkerpatrika.com/"
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
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_ajker_patrika] url: {url}\n  headings: {headings}")
                articles.append({
                    "title": headings[0] if headings else "",
                    "heading": heading_text,
                    "url": url,
                    "published_date": datetime.now().date(),
                    "source": "ajker_patrika"
                })
            except Exception as e:
                print(f"Error scraping Ajker Patrika article: {e}")
    except Exception as e:
        print(f"Error scraping Ajker Patrika homepage: {e}")
    return articles

def scrape_protidiner_sangbad():
    articles = []
    try:
        homepage = "https://www.protidinersangbad.com/"
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
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
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
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_bangladesher_khabor] url: {url}\n  headings: {headings}")
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
                headings = [tag.text.strip() for tag in article_soup.find_all(['h1', 'h2']) if tag.text.strip()]
                heading_text = ' '.join(headings)
                print(f"[scrape_bangladesh_journal] url: {url}\n  headings: {headings}")
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
        # ("sangbad", scrape_sangbad),
             # ("noya_diganta", scrape_noya_diganta),
             # ("jai_jai_din", scrape_jai_jai_din),
        ("manobkantha", scrape_manobkantha),
            # ("ajkaler_khobor", scrape_ajkaler_khobor),
        ("ajker_patrika", scrape_ajker_patrika),
        ("protidiner_sangbad", scrape_protidiner_sangbad),
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



def generate_trending_word_candidates_realtime_with_save(db: Session, limit: int = 15) -> str:
    """Generate trending word candidates using REAL-TIME analysis with newspaper + social media integration and save top 15 LLM words to database"""
    print("Starting real-time trending analysis with newspaper + social media integration...")
    print("=" * 60)
    
    from datetime import date
    today = date.today()
    
    # Fetch news articles (existing)
    articles = fetch_news() or []
    # Use only heading for content (as requested)
    texts = []
    for a in articles:
        heading = a.get('heading', '').strip() 
        if heading:
            texts.append(heading)
    
    print(f"📰 Extracted {len(texts)} text segments from {len(articles)} scraped articles")
    
    # Fetch social media content (NEW: Reddit integration)
    social_media_content = []
    try:
        print("📱 Fetching social media content (Reddit)...")
        from app.services.social_media_scraper import scrape_social_media_content
        social_media_content = scrape_social_media_content()
        print(f"📱 Retrieved {len(social_media_content)} social media items")
    except Exception as e:
        print(f"⚠️ Social media scraping failed: {e}")
        social_media_content = []
    
    # Fetch Google Trends
    google_trends = get_google_trends_bangladesh()
    # Fetch YouTube trending
    youtube_trends = get_youtube_trending_bangladesh()
    # Fetch SerpApi Google Trends
    serpapi_trends = get_serpapi_trending_bangladesh()
    
    # print("[SerpApi] Final trending phrases (Bangladesh):")
    for idx, trend in enumerate(serpapi_trends, 1):
        print(f"  {idx}. {' '.join(trend) if isinstance(trend, list) else trend}")
    
    # Combine all sources for AI with better text cleaning
    from app.services.stopwords import STOP_WORDS
    
    # Clean and filter texts before combining (KEEP COMPLETE HEADINGS)
    cleaned_texts = []
    for text in texts:
        if text and len(text.strip()) > 10:  # Only meaningful texts
            # Light cleaning but KEEP COMPLETE HEADING
            cleaned = text.strip()
            # Only remove extreme patterns, keep most content
            cleaned = re.sub(r'(পর|হামলার পর|ছুড়ল|সোপর্দ|বিয়ে)', '', cleaned)  # Remove common patterns
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()  # Clean extra spaces
            
            # Light stop words filtering but KEEP MOST CONTENT
            words = cleaned.split()
            # Only remove very common stop words, keep context
            filtered_words = [w for w in words if w not in ['এর', 'যে', 'করে', 'হয়', 'দিয়ে', 'থেকে', 'জন্য', 'সাথে', 'এই', 'সেই', 'তার', 'তাদের']]
            
            if len(filtered_words) >= 2:  # Only keep if has meaningful content
                # Join the complete filtered heading and add comma separator
                complete_heading = ' '.join(filtered_words)
                cleaned_texts.append(complete_heading)
    
    texts.extend([' '.join(words) for words in google_trends if words])
    texts.extend([' '.join(words) for words in youtube_trends if words])
    texts.extend([' '.join(trend) for trend in serpapi_trends if trend])
    
    # Add social media content to texts
    social_media_texts = []
    if social_media_content:
        print(f"🔄 Processing {len(social_media_content)} social media items...")
        for item in social_media_content:
            content_text = item.get('content', '').strip()
            if content_text and len(content_text) > 10:
                # Clean social media text similar to news
                cleaned_social = re.sub(r'http\S+|www\S+|https\S+', '', content_text)  # Remove URLs
                cleaned_social = re.sub(r'@\w+|#\w+', '', cleaned_social)  # Remove mentions/hashtags
                cleaned_social = re.sub(r'\s+', ' ', cleaned_social).strip()
                
                if len(cleaned_social) > 5:
                    social_media_texts.append(cleaned_social)
        
        print(f"📱 Processed {len(social_media_texts)} social media texts")
    
    # Use cleaned texts for further processing
    all_texts = cleaned_texts + social_media_texts + [' '.join(words) for words in google_trends if words] + [' '.join(words) for words in youtube_trends if words] + [' '.join(trend) for trend in serpapi_trends if trend]
    
    if not all_texts:
        msg = "No articles, social media, or trends available for analysis"
        print(msg)
        return msg
    
    # --- Mixed Content Processing for LLM ---
    from app.services.advanced_bengali_nlp import TrendingBengaliAnalyzer
    analyzer = TrendingBengaliAnalyzer()
    
    print(f"🔧 Processing mixed content: {len(articles)} newspaper articles + {len(social_media_content)} social media items...")
    
    # Prepare articles with metadata for category detection
    articles_with_metadata = []
    for article in articles:
        articles_with_metadata.append({
            'url': article.get('url', ''),
            'title': article.get('title', ''),
            'content': article.get('heading', ''),  # Using heading as content
            'source': article.get('source', 'unknown')
        })
    
    # Use mixed content processing if we have both types
    if articles_with_metadata and social_media_content:
        print("🔀 Using mixed content processing for newspaper + social media...")
        processed_content = process_mixed_content_for_llm(
            articles_with_metadata, 
            social_media_content, 
            analyzer, 
            max_chars=12000
        )
        combined_text = processed_content['combined_text']
        
        print(f"📊 Mixed Content Statistics:")
        print(f"   📰 Newspaper: {processed_content['source_stats']['newspaper_count']} articles")
        print(f"   📱 Social Media: {processed_content['source_stats']['social_media_count']} items")
        print(f"   🔗 Combined Text: {len(combined_text)} chars")
    
    elif articles_with_metadata:
        print("📰 Using newspaper-only processing...")
        # Fallback to newspaper-only category processing
        combined_text = optimize_text_for_ai_analysis_with_categories(
            articles_with_metadata, 
            analyzer, 
            max_chars=12000,
            max_articles=150,
            enable_categories=True
        )
    
    else:
        print("⚠️ No newspaper articles available, using basic text optimization...")
        # Fallback to basic processing
        combined_text = optimize_text_for_ai_analysis(
            all_texts,
            analyzer,
            max_chars=12000,
            max_articles=150
        )
    
    # Add trend data as simple text fallback
    for trend_text in all_texts[len(articles):]:  # Trends after articles
        articles_with_metadata.append({
            'url': '',
            'title': trend_text,
            'content': trend_text,
            'source': 'trends'
        })
    
    # Use category-aware optimization with INCREASED limits for 5000 token capacity  
    combined_text = optimize_text_for_ai_analysis_with_categories(
        articles_with_metadata, 
        analyzer, 
        max_chars=12000,  # Increased from 2000 to 12000 for 5000 token capacity (12000 chars ≈ 4800 tokens)
        max_articles=150,  # Increased from 60 to 150 for more articles
        enable_categories=True
    )
    
    print(f"📊 Category-optimized Combined Text Size: {len(combined_text)} characters")
    print(f"📊 Successfully optimized from {len(all_texts)} original texts with categories")
    ai_response = None
    print(f"Combined Text Preview (first 150 chars): {combined_text[:150]}...")
    
    # Store the original combined_text for display purposes before any modifications
    original_combined_text = combined_text
    print(f"🔍 STORED original_combined_text: {len(original_combined_text)} chars")
    print(f"🔍 PREVIEW original_combined_text: {original_combined_text[:100]}...")
    
    # ===== TERMINAL DEBUG: SHOW FULL COMBINED TEXT =====
    print(f"\n{'='*80}")
    print(f"🔍 FULL COMBINED TEXT SENT TO LLM ({len(combined_text)} chars):")
    print(f"{'='*80}")
    print(combined_text)
    print(f"{'='*80}")
    print(f"🔍 END OF COMBINED TEXT")
    print(f"{'='*80}\n")
    
    # Token estimation for Groq limits (Enhanced for 5000 token capacity)
    estimated_tokens = len(combined_text) // 2.5  # More realistic for Bengali with bullet separation
    print(f"🎯 Estimated tokens: ~{estimated_tokens:.0f} (Target: <2500 for 5000 token capacity)")
    
    if estimated_tokens > 2500:  # Increased from 800 to 2500 for 5000 token capacity
        print("⚠️  Text still too long for token limits, emergency reducing...")
        # Emergency truncation for rate limits
        safe_chars = int(2500 * 2.5)  # Conservative for 2500 tokens (leaves buffer for 5000 capacity)
        if len(combined_text) > safe_chars:
            combined_text = combined_text[:safe_chars-3] + "..."
            print(f"🔧 Emergency truncated to {len(combined_text)} characters")
            print(f"🔍 AFTER TRUNCATION combined_text: {combined_text[:100]}...")
    
    # Final debug check before API call
    print(f"🔍 FINAL combined_text before API: {len(combined_text)} chars")
    print(f"🔍 FINAL preview: {combined_text[:100]}...")

    try:
        from groq import Groq
        import os
        import time
        
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in environment.")
        
        print(f"🔑 Using Groq API Key: {api_key[:15]}...")
        
        # Initialize client with connection settings
        try:
            client = Groq(
                api_key=api_key,
                timeout=120.0  # 120 second timeout for client
            )
        except Exception as client_error:
            print(f"❌ Failed to initialize Groq client: {client_error}")
            raise client_error
        
        # Create conditional prompt based on content type
        has_social_media = social_media_content and len(social_media_content) > 0
        has_newspapers = articles and len(articles) > 0
        
        if has_newspapers and has_social_media:
            # Mixed content prompt
            prompt = create_mixed_content_llm_prompt(combined_text, limit)
            print("🔀 Using mixed content prompt for newspaper + social media analysis")
        elif has_newspapers:
            # Newspaper-only prompt  
            prompt = f"""
                    নিচের বাংলা সংবাদ টেক্সট থেকে আজকের জন্য সবচেয়ে গুরুত্বপূর্ণ এবং ট্রেন্ডিং {limit}টি শব্দ বা বাক্যাংশ খুঁজে বের করো। শব্দ/বাক্যাংশগুলো অবশ্যই বিশেষ্য (noun) এবং/অথবা বিশেষণ (adjective) প্রকৃতির হতে হবে এবং অর্থবহ, জনপ্রিয় ও আলোচিত বিষয়ের প্রতিনিধিত্ব করবে।
                    📋 সংবাদ টেক্সট ফরম্যাট বোঝার নির্দেশনা:
                    - টেক্সটটি category-wise সাজানো (রাজনীতি: content | অর্থনীতি: content)
                    - প্রতিটি category তে একাধিক article bullet point (•) দিয়ে আলাদা করা
                    - সব category থেকে সমানভাবে গুরুত্বপূর্ণ শব্দ নির্বাচন করো
                    - রাজনীতি ও অর্থনীতি category কে বেশি প্রাধান্য দাও
                    অবশ্যই অনুসরণীয় নিয়মাবলী:
                    1.শুধুমাত্র বিশেষ্য (noun) এবং বিশেষণ (adjective) ভিত্তিক শব্দ/বাক্যাংশ দাও
                    2.ট্রেন্ডিং বিষয়/থিম খুঁজে বের করো - যা বর্তমানে সংবাদে সবচেয়ে আলোচিত এবং প্রাসঙ্গিক।
                    3.প্রতিটি টপিকের জন্য শুধুমাত্র একটি প্রতিনিধিত্বকারী শব্দ/বাক্যাংশ দাও - একই বিষয়ের একাধিক রূপ এড়িয়ে চলো।
                    4.কোনো ব্যক্তির নাম বা ব্যক্তি-নির্দিষ্ট উল্লেখ বাদ দাও (যেমন: ট্রাম্প, হাসিনা, মোদি)।
                    5.সংক্ষিপ্ত ও স্পষ্ট বাক্যাংশ দাও - সর্বোচ্চ ২-৪ শব্দ, দীর্ঘ বাক্য এড়িয়ে চলো।
                    6.সাধারণ stop words এবং ক্রিয়া (verb) বাদ দাও (যেমন: এই, সেই, করা, হওয়া, বলা, দেওয়া)।
                    7.শুধুমাত্র বিষয়বস্তু/থিম-ভিত্তিক concrete noun বা adjective দাও - যা কোনো অর্থ বহন করে
                    8.প্রতিটি শব্দ/বাক্যাংশ সংখ্যা দিয়ে আলাদা লাইনে লেখো (১., ২., ৩. ... {limit}. ইত্যাদি)।
                    9.শুধুমাত্র বাংলা শব্দ/বাক্যাংশ ব্যবহার করো - ইংরেজি বা অন্য ভাষার শব্দ এড়িয়ে চলো।
                    10.সংবাদের গুরুত্ব ও প্রাসঙ্গিকতা বিবেচনা করো - সাম্প্রতিক ঘটনা ও জাতীয় গুরুত্বের বিষয়গুলোকে প্রাধান্য দাও।
                    11.অপ্রাসঙ্গিক বা সাধারণ শব্দ এড়িয়ে চলো - যেমন, সময়, জিনিস, বিষয়, যা নির্দিষ্ট কোনো ট্রেন্ড বা থিম প্রকাশ করে না।
                    সংবাদ টেক্সট:
                    {combined_text}

                    আউটপুট ফরম্যাট:
                    ট্রেন্ডিং শব্দ/বাক্যাংশ ({limit}টি):
                    ১. [শব্দ/বাক্যাংশ]
                    ২. [শব্দ/বাক্যাংশ]
                    ৩. [শব্দ/বাক্যাংশ]
                    ...
                    {limit}. [শব্দ/বাক্যাংশ]
                    """
            print("📰 Using newspaper-only prompt")
        else:
            # Fallback prompt for other content
            prompt = f"""
                    নিচের বাংলা টেক্সট থেকে আজকের জন্য সবচেয়ে গুরুত্বপূর্ণ এবং ট্রেন্ডিং {limit}টি শব্দ বা বাক্যাংশ খুঁজে বের করো। শব্দ/বাক্যাংশগুলো অবশ্যই বিশেষ্য (noun) এবং/অথবা বিশেষণ (adjective) প্রকৃতির হতে হবে এবং অর্থবহ, জনপ্রিয় ও আলোচিত বিষয়ের প্রতিনিধিত্ব করবে।
                    অবশ্যই অনুসরণীয় নিয়মাবলী:
                    1.শুধুমাত্র বিশেষ্য (noun) এবং বিশেষণ (adjective) ভিত্তিক শব্দ/বাক্যাংশ দাও
                    2.ট্রেন্ডিং বিষয়/থিম খুঁজে বের করো - যা বর্তমানে আলোচিত এবং প্রাসঙ্গিক।
                    3.প্রতিটি টপিকের জন্য শুধুমাত্র একটি প্রতিনিধিত্বকারী শব্দ/বাক্যাংশ দাও - একই বিষয়ের একাধিক রূপ এড়িয়ে চলো।
                    4.কোনো ব্যক্তির নাম বা ব্যক্তি-নির্দিষ্ট উল্লেখ বাদ দাও।
                    5.সংক্ষিপ্ত ও স্পষ্ট বাক্যাংশ দাও - সর্বোচ্চ ২-৪ শব্দ।
                    6.সাধারণ stop words এবং ক্রিয়া (verb) বাদ দাও।
                    7.শুধুমাত্র বিষয়বস্তু/থিম-ভিত্তিক concrete noun বা adjective দাও।
                    8.প্রতিটি শব্দ/বাক্যাংশ সংখ্যা দিয়ে আলাদা লাইনে লেখো (১., ২., ৩. ... {limit}. ইত্যাদি)।
                    9.শুধুমাত্র বাংলা শব্দ/বাক্যাংশ ব্যবহার করো।
                    টেক্সট:
                    {combined_text}

                    আউটপুট ফরম্যাট:
                    ট্রেন্ডিং শব্দ/বাক্যাংশ ({limit}টি):
                    ১. [শব্দ/বাক্যাংশ]
                    ২. [শব্দ/বাক্যাংশ]
                    ৩. [শব্দ/বাক্যাংশ]
                    ...
                    {limit}. [শব্দ/বাক্যাংশ]
                    """
            print("🔧 Using fallback prompt")
        print(f"📤 Sending request to Groq API...")
        print(f"📊 Prompt length: {len(prompt)} characters")
        
        # Retry logic for Groq API connection issues with LONGER delays for rate limiting
        max_retries = 3
        retry_delay = 3  # Reduced from 5 to 3 seconds 
        response = None
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 Attempt {attempt + 1}/{max_retries}")
                
                # Use llama-3.3-70b-versatile for larger context window
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",  # Using model with larger context window
                    stream=False,
                    temperature=0.7,
                    max_tokens=1000,  # Increased from 800 to 1000 for more detailed output
                    timeout=45.0  # Increased from 30 to 45 second timeout
                )
                print(f"✅ API call successful on attempt {attempt + 1}")
                break
                
            except Exception as api_error:
                print(f"❌ API attempt {attempt + 1} failed: {str(api_error)}")
                
                # Check for rate limit specifically
                error_str = str(api_error).lower()
                if "rate limit" in error_str:
                    wait_time = retry_delay * (attempt + 1) * 2  # Longer wait for rate limits
                    print(f"🚫 Rate limit detected - waiting {wait_time} seconds...")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(wait_time)
                    else:
                        print(f"🚫 Rate limit exceeded after all retries")
                        raise api_error
                else:
                    if attempt < max_retries - 1:
                        print(f"⏳ Waiting {retry_delay} seconds before retry...")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        print(f"🚫 All {max_retries} attempts failed")
                        raise api_error
        
        print(f"📥 Received response from Groq API")
        print(f"🔍 Response object: {response}")
        
        if not response or not response.choices:
            raise ValueError("Empty response from Groq API")
            
        ai_response = response.choices[0].message.content
        print(f"✅ Raw AI Response length: {len(ai_response) if ai_response else 0}")
        print(f"📝 Raw AI Response preview: {ai_response[:200] if ai_response else 'None'}...")
        
        # Clean markdown formatting from AI response
        def clean_markdown_text(text):
            if not text:
                return text
            import re
            
            # Remove markdown bold, italic, code formatting
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
            text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
            text = re.sub(r'`([^`]+)`', r'\1', text)        # `code`
            
            # Split into lines and filter
            lines = text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip introductory and concluding messages
                if any(phrase in line for phrase in [
                    'বাংলা সংবাদ থেকে গুগল ট্রেন্ডস',
                    'গুরুত্বপূর্ণ এবং trending',
                    'নিচে রয়েছে',
                    'এই সবগুলোই গুরুত্বপূর্ণ বিষয়',
                    'এখনকার সময়ে সবচেয়ে আলোচিত',
                    'trending শব্দ/বাক্যাংশ'
                ]):
                    continue
                
                # Keep only numbered items
                if re.match(r'^\d+\.|^[\u09E6-\u09EF]+\.', line):
                    # Remove quotes around entire phrases
                    line = re.sub(r'^["\'](.+)["\']$', r'\1', line)
                    cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines)
        
        
        ai_response = clean_markdown_text(ai_response)
        print(f"🤖 Groq AI Response (cleaned): {ai_response}")
        
        # Save top 15 LLM trending words to database
        save_llm_trending_words_to_db(db, ai_response, today, limit=15)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Error generating trending words with Groq:")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {str(e)}")
        print(f"   Full Traceback:\n{error_details}")
        
        # Check for common Groq API issues
        error_str = str(e).lower()
        if "rate limit" in error_str:
            print("🚫 Rate limit exceeded - need to wait before retrying")
        elif "billing" in error_str:
            print("💳 Billing issue - check Groq account")
        elif "api key" in error_str:
            print("🔑 API key issue - check GROQ_API_KEY")
        elif "timeout" in error_str:
            print("⏱️ Request timeout - server might be slow")
        elif "connection" in error_str or "remote protocol" in error_str:
            print("🌐 Network connection issue - check internet connectivity or try again later")
        elif "peer closed" in error_str:
            print("🔌 Server disconnected during request - this is usually temporary")
        else:
            print("🔧 Unknown API error - check logs above for details")
        
        ai_response = f"❌ Error generating trending words: Network connection issue. Please try again later."
    
    # Skip NLP analysis - only use LLM response for trending words
    print(f"\n🤖 Using LLM-only approach for trending words generation")
    
    # Clean summary without NLP analysis - just show the AI response
    summary = []
    
    # Main AI response section
    summary.append(f"🤖 AI Generated Trending Words:\n{ai_response}")
    summary.append(f"\n💾 Database Status: Top 15 LLM trending words saved for trending analysis section")
    
    # Create clean output for frontend
    final_output = "🤖 AI Generated Trending Words থেকে আজকের শব্দ নির্বাচন করুন\n\n" + '\n'.join(summary)
    
    print(f"[Summary] Real-time analysis completed with database save for LLM words")
    return final_output

def analyze_trending_content_and_store(db: Session, analyzer, content: List[Dict], source: str, target_date: date):
    """Analyze trending content using advanced Bengali NLP and store results in database"""
    try:
        print(f"🔍 Analyzing {len(content)} items from {source} for {target_date}")
        
        # Count unique newspaper sources
        newspaper_sources = set()
        for item in content:
            item_source = item.get('source', 'unknown')
            if item_source != 'unknown':
                newspaper_sources.add(item_source)
        
        newspaper_count = len(newspaper_sources)
        print(f"📰 Analyzing content from {newspaper_count} newspaper sources:")
        for i, newspaper in enumerate(sorted(newspaper_sources), 1):
            articles_from_source = len([item for item in content if item.get('source') == newspaper])
            print(f"   {i}. {newspaper:<20} - {articles_from_source:2d} articles")
        
        # Analyze content using advanced Bengali analyzer
        analysis_result = analyzer.analyze_trending_content(content, source_type=source)
        
        if not analysis_result or 'trending_keywords' not in analysis_result:
            print(f"No analysis results for {source}")
            return
        
        trending_keywords = analysis_result.get('trending_keywords', [])
        print(f"📊 Found {len(trending_keywords)} trending keywords from {source}")
        
        # Track which newspapers contain each phrase
        phrase_newspaper_counts = {}
        for keyword, score in trending_keywords[:50]:
            keyword_clean = keyword.strip()
            if len(keyword_clean) <= 1:
                continue
                
            # Count how many newspapers contain this phrase
            newspapers_with_phrase = set()
            for item in content:
                title = item.get('title', '').lower()
                heading = item.get('heading', '').lower()
                combined_text = f"{title} {heading}".lower()
                
                if keyword_clean.lower() in combined_text:
                    item_source = item.get('source', 'unknown')
                    if item_source != 'unknown':
                        newspapers_with_phrase.add(item_source)
            
            phrase_newspaper_counts[keyword_clean] = len(newspapers_with_phrase)
        
        print(f"\n💾 Storing trending phrases in database:")
        stored_count = 0
        
        # Store trending phrases in database with newspaper counts
        for keyword, score in trending_keywords[:50]:  # Store top 50
            keyword_clean = keyword.strip()
            if len(keyword_clean) > 1:  # Skip very short words
                # Determine phrase type based on word count
                word_count = len(keyword_clean.split())
                if word_count == 1:
                    phrase_type = 'unigram'
                elif word_count == 2:
                    phrase_type = 'bigram'
                else:
                    phrase_type = 'trigram'
                
                # Get newspaper count for this phrase
                phrase_newspapers = phrase_newspaper_counts.get(keyword_clean, 0)
                
                # Enhanced scoring with newspaper boost
                newspaper_boost = min(phrase_newspapers / max(newspaper_count, 1), 1.0) * 0.3
                enhanced_score = float(score) + newspaper_boost
                
                trending_phrase = TrendingPhrase(
                    date=target_date,
                    phrase=enhanced_score,
                    score=enhanced_score,
                    frequency=phrase_newspapers,  # Store newspaper count as frequency
                    phrase_type=phrase_type,
                    source=source
                )
                db.add(trending_phrase)
                stored_count += 1
                
                # Print progress for top 15 phrases
                if stored_count <= 15:
                    print(f"   {stored_count:2d}. {keyword_clean:<30} | Score: {enhanced_score:.3f} | Newspapers: {phrase_newspapers:2d}/{newspaper_count}")
        
        print(f"✅ Stored {stored_count} trending phrases for {source}")
        
    except Exception as e:
        print(f"❌ Error analyzing content from {source}: {e}")
        import traceback
        traceback.print_exc()

def save_llm_trending_words_to_db(db: Session, ai_response: str, target_date: date, limit: int = 15):
    """Parse LLM response and save top trending words to database"""
    try:
        if not ai_response or ai_response.strip() == "":
            print("❌ No AI response to parse")
            return
        
        # Parse the LLM response to extract trending words
        lines = ai_response.strip().split('\n')
        saved_count = 0
        
        for line in lines:
            if saved_count >= limit:
                break
                
            # Clean the line and extract the trending word/phrase
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering if present (1. , 2. , etc.)
            import re
            cleaned_line = re.sub(r'^\d+\.\s*', '', line)
            # Remove Bengali numbering (১. , ২. , etc.)
            cleaned_line = re.sub(r'^[\u09E6-\u09EF]+\.\s*', '', cleaned_line)
            # Remove markdown formatting
            cleaned_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_line)  # Remove **bold**
            cleaned_line = re.sub(r'\*([^*]+)\*', r'\1', cleaned_line)      # Remove *italic*
            cleaned_line = re.sub(r'`([^`]+)`', r'\1', cleaned_line)        # Remove `code`
            # Remove quotation marks around phrases
            cleaned_line = re.sub(r'^["\'](.+)["\']$', r'\1', cleaned_line)
            cleaned_line = cleaned_line.strip()
            
            # Skip if too short or contains unwanted patterns
            if len(cleaned_line) < 2:
                continue
            
            # Skip if contains person indicators or unwanted patterns
            person_indicators = ['মাননীয়', 'জনাব', 'মিসেস', 'মিস', 'ডঃ', 'প্রফেসর']
            if any(indicator in cleaned_line for indicator in person_indicators):
                continue
            
            # Determine phrase type
            word_count = len(cleaned_line.split())
            if word_count == 1:
                phrase_type = 'unigram'
            elif word_count == 2:
                phrase_type = 'bigram'
            else:
                phrase_type = 'trigram'
            
            # Create TrendingPhrase object
            trending_phrase = TrendingPhrase(
                date=target_date,
                phrase=cleaned_line,
                score=1.0 - (saved_count * 0.1),  # Decreasing score based on order
                frequency=1,
                phrase_type=phrase_type,
                source='llm_generated'
            )
            
            db.add(trending_phrase)
            saved_count += 1
            print(f"💾 Saved LLM trending word {saved_count}: {cleaned_line}")
        
        # Commit the changes
        db.commit()
        print(f"✅ Successfully saved {saved_count} LLM trending words to database")
        
    except Exception as e:
        print(f"❌ Error saving LLM trending words: {e}")
        db.rollback()

def optimize_text_for_ai_analysis(texts, analyzer, max_chars=12000, max_articles=150):
    """
    Optimize texts for AI analysis while keeping MORE CONTENT per article
    Target: 12000 chars max for 5000 token capacity (12000 chars ≈ 4800 tokens)
    
    Strategy:
    1. Keep complete cleaned headings (no keyword extraction)
    2. Light deduplication
    3. Comma separation for clarity
    4. Priority-based selection
    """
    print(f"🔧 Optimizing {len(texts)} texts for Groq API limits (COMPLETE HEADINGS MODE)...")
    
    if not texts:
        return ""
    
    # Step 1: Keep complete cleaned headings (no aggressive keyword extraction)
    processed_headings = []
    processed_count = 0
    
    for text in texts[:max_articles]:  # Limit number of articles
        if not text or len(text.strip()) < 5:
            continue
            
        # Light normalization only
        normalized = analyzer.processor.normalize_text(text)
        
        # Light stop words filtering but keep most content
        words = normalized.split()
        filtered_words = [
            w for w in words 
            if len(w) >= 2  # Very lenient length requirement
            and not w.isdigit()  # No pure numbers
            and w not in ['এর', 'যে', 'করে', 'হয়', 'দিয়ে', 'থেকে', 'এই', 'সেই']  # Only remove very common ones
        ]
        
        if len(filtered_words) >= 3:  # Keep if has reasonable content
            # Keep the complete filtered heading (no truncation)
            complete_heading = ' '.join(filtered_words)
            
            # Limit individual heading length for readability
            if len(complete_heading) > 80:
                complete_heading = complete_heading[:77] + "..."
                
            processed_headings.append(complete_heading)
            processed_count += 1
    
    print(f"📊 Processed {processed_count} complete headings")
    
    # Step 2: Light deduplication (less aggressive)
    unique_headings = []
    seen_words = set()
    
    for heading in processed_headings:
        # Check for major overlap only
        words = set(heading.lower().split())
        
        # Check overlap with existing content (less aggressive - 60% threshold)
        has_major_overlap = False
        for existing_words in seen_words:
            if words and existing_words:
                overlap = len(words.intersection(existing_words))
                if overlap > 0 and overlap / max(len(words), len(existing_words)) > 0.6:  # 60% overlap = skip
                    has_major_overlap = True
                    break
        
        if not has_major_overlap and words:
            seen_words.add(frozenset(words))
            unique_headings.append(heading)
    
    print(f"🔄 Light deduplication: {len(processed_headings)} -> {len(unique_headings)} unique headings")
    
    # Step 3: Combine with comma separators for clarity
    if not unique_headings:
        return ""
    
    # Join with comma and space for clear separation between articles
    combined_text = ' • '.join(unique_headings)  # Using bullet for better separation
    
    # Step 4: Smart truncation if needed
    if len(combined_text) > max_chars:
        print(f"⚠️  Text too long ({len(combined_text)} chars), truncating to {max_chars}...")
        
        # Try to fit as many complete headings as possible
        final_headings = []
        current_length = 0
        
        for heading in unique_headings:
            addition_length = len(heading) + 3  # +3 for " • "
            if current_length + addition_length <= max_chars - 10:  # Leave some margin
                final_headings.append(heading)
                current_length += addition_length
            else:
                break
        
        combined_text = ' • '.join(final_headings)
        if len(combined_text) < len(' • '.join(unique_headings)):
            combined_text += "..."
    
    # Calculate stats
    original_total = sum(len(t) for t in texts if t)
    compression_ratio = len(combined_text) / max(original_total, 1) * 100
    
    print(f"✅ Optimized to {len(combined_text)} chars from {len(texts)} texts")
    print(f"📈 Compression: {compression_ratio:.1f}% of original size")
    print(f"🎯 Token estimate: ~{len(combined_text)//3} tokens (limit: 5000 capacity)")
    print(f"📄 Included {len(combined_text.split(' • '))} complete headings")
    
    return combined_text

# Category Detection System for Bengali Newspapers
def detect_category_from_url(url, title="", content=""):
    """
    Enhanced category detection using comprehensive URL patterns as primary method
    and content analysis as secondary method for Bengali newspapers
    
    Returns Bengali category name with high accuracy
    Based on analysis of 500 Bengali newspaper URLs with 87.2% success rate
    """
    
    # URL Pattern Detection (PRIMARY method - comprehensive patterns)
    url_patterns = {
        # National/Bangladesh News
        'জাতীয়': [
            r'/bangladesh', r'/national', r'/country', r'/dhaka', r'/chittagong',
            r'/barisal', r'/rangpur', r'/sylhet', r'/khulna', r'/rajshahi', r'/mymensingh',
            r'/সারাদেশ', r'/জাতীয়', r'/country-news'
        ],
        
        # International News
        'আন্তর্জাতিক': [
            r'/international', r'/world', r'/middle-east', r'/america', r'/asia',
            r'/europe', r'/africa', r'/বিদেশ', r'/আন্তর্জাতিক'
        ],
        
        # Politics
        'রাজনীতি': [
            r'/politics', r'/political', r'/election', r'/govt', r'/government',
            r'/রাজনীতি'
        ],
        
        # Sports
        'খেলাধুলা': [
            r'/sports', r'/cricket', r'/football', r'/game', r'/tennis', r'/খেলা'
        ],
        
        # Entertainment
        'বিনোদন': [
            r'/entertainment', r'/bollywood', r'/hollywood', r'/tollywood',
            r'/dhallywood', r'/music', r'/cinema', r'/television', r'/বিনোদন'
        ],
        
        # Business/Economy
        'অর্থনীতি': [
            r'/business', r'/economy', r'/economics', r'/market', r'/bank',
            r'/finance', r'/অর্থনীতি'
        ],
        
        # Technology
        'প্রযুক্তি': [
            r'/technology', r'/tech', r'/digital', r'/প্রযুক্তি'
        ],
        
        # Health
        'স্বাস্থ্য': [
            r'/health', r'/medical', r'/corona', r'/covid', r'/dengue', r'/স্বাস্থ্য'
        ],
        
        # Education
        'শিক্ষা': [
            r'/education', r'/campus', r'/university', r'/school', r'/শিক্ষা'
        ],
        
        # Opinion/Editorial
        'মতামত': [
            r'/opinion', r'/editorial', r'/op-ed', r'/column', r'/analysis', r'/মতামত'
        ],
        
        # Lifestyle
        'লাইফস্টাইল': [
            r'/lifestyle', r'/life', r'/fashion', r'/food', r'/care',
            r'/rupbatika', r'/জীবনধারা'
        ],
        
        # Religion
        'ধর্ম': [
            r'/religion', r'/islam', r'/islamic', r'/islam-life', r'/ইসলাম'
        ],
        
        # Environment
        'পরিবেশ': [
            r'/environment', r'/climate', r'/weather', r'/পরিবেশ'
        ],
        
        # Science
        'বিজ্ঞান': [
            r'/science', r'/research', r'/বিজ্ঞান'
        ],
        
        # Jobs/Career
        'চাকরি': [
            r'/job', r'/career', r'/employment', r'/job-seek', r'/চাকরি'
        ],
        
        # Photos/Gallery
        'ছবি': [
            r'/picture', r'/photo', r'/gallery', r'/photos', r'/ছবি'
        ],
        
        # Video
        'ভিডিও': [
            r'/video', r'/videos', r'/ভিডিও'
        ],
        
        # Women
        'নারী': [
            r'/women', r'/woman', r'/নারী'
        ],
        
        # Fact Check
        'ফ্যাক্ট চেক': [
            r'/fact-check', r'/factcheck', r'/verification'
        ]
    }
    
    # Check URL patterns first (87.2% success rate)
    url_lower = url.lower()
    for category, patterns in url_patterns.items():
        for pattern in patterns:
            if re.search(pattern, url_lower):
                return category
    
    # Handle uncategorized URLs with source-specific patterns
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    path = parsed_url.path.lower()
    
    # Source-specific subcategorization for better tracking
    if 'prothomalo.com' in domain and re.search(r'/[a-z]{10,}$', path):
        return 'প্রথম আলো নিবন্ধ'
    elif 'samakal.com' in domain and '/divisions/' in path:
        return 'সমকাল আঞ্চলিক'
    elif 'jugantor.com' in domain and path in ['/', '/national', '/politics', '/international']:
        return 'যুগান্তর বিভাগীয়'
    
    # Content-based detection (SECONDARY method for unmatched URLs)
    if title or content:
        text_to_check = f"{title} {content}".lower()
        
        # Comprehensive Bengali keywords with higher coverage
        content_keywords = {
            'রাজনীতি': [
                'রাজনীতি', 'সরকার', 'মন্ত্রী', 'প্রধানমন্ত্রী', 'নির্বাচন', 'ভোট', 'পার্টি', 'নেতা',
                'সংসদ', 'মেয়র', 'কাউন্সিলর', 'চেয়ারম্যান', 'আওয়ামী', 'বিএনপি', 'জাতীয়'
            ],
            'আন্তর্জাতিক': [
                'আন্তর্জাতিক', 'বিশ্ব', 'যুক্তরাষ্ট্র', 'ভারত', 'চীন', 'ইউরোপ', 'ইরান', 'ইসরায়েল',
                'পাকিস্তান', 'মিয়ানমার', 'ট্রাম্প', 'বাইডেন', 'পুতিন', 'মোদী', 'ইউক্রেন', 'গাজা'
            ],
            'খেলাধুলা': [
                'খেলা', 'ক্রিকেট', 'ফুটবল', 'টেস্ট', 'ম্যাচ', 'দল', 'খেলোয়াড়', 'টুর্নামেন্ট',
                'বাংলাদেশ ক্রিকেট', 'টাইগার', 'সাকিব', 'মুশফিক', 'তামিম', 'বিসিবি'
            ],
            'অর্থনীতি': [
                'অর্থনীতি', 'টাকা', 'ব্যাংক', 'ব্যবসা', 'বাজার', 'দাম', 'বাণিজ্য', 'বিনিয়োগ',
                'রপ্তানি', 'আমদানি', 'জিডিপি', 'ডলার', 'শেয়ার', 'স্টক', 'কৃষি', 'শিল্প', 'গার্মেন্টস'
            ],
            'প্রযুক্তি': [
                'প্রযুক্তি', 'কম্পিউটার', 'ইন্টারনেট', 'মোবাইল', 'অ্যাপ', 'সফটওয়্যার', 'ডিজিটাল',
                'আর্টিফিশিয়াল', 'এআই', 'গুগল', 'ফেসবুক', 'হোয়াটসঅ্যাপ', 'চ্যাটজিপিটি'
            ],
            'বিনোদন': [
                'বিনোদন', 'সিনেমা', 'নাটক', 'গান', 'শিল্পী', 'অভিনেতা', 'অভিনেত্রী', 'চলচ্চিত্র',
                'হলিউড', 'বলিউড', 'ঢালিউড', 'শাকিব খান', 'কনসার্ট', 'অনুষ্ঠান'
            ],
            'স্বাস্থ্য': [
                'স্বাস্থ্য', 'চিকিৎসা', 'ডাক্তার', 'হাসপাতাল', 'ওষুধ', 'রোগ', 'চিকিৎসক',
                'করোনা', 'কোভিড', 'ভ্যাকসিন', 'টিকা', 'ডেঙ্গু', 'ডায়াবেটিস', 'ক্যান্সার'
            ],
            'শিক্ষা': [
                'শিক্ষা', 'বিশ্ববিদ্যালয়', 'কলেজ', 'স্কুল', 'পরীক্ষা', 'ছাত্র', 'শিক্ষার্থী',
                'এইচএসসি', 'এসএসসি', 'ভর্তি', 'ফলাফল', 'বৃত্তি', 'শিক্ষক', 'ঢাকা বিশ্ববিদ্যালয়', 'বুয়েট'
            ],
            'লাইফস্টাইল': [
                'জীবনযাত্রা', 'ফ্যাশন', 'রান্না', 'ভ্রমণ', 'স্টাইল', 'খাবার', 'রেসিপি', 'বিউটি',
                'সৌন্দর্য', 'মেকআপ', 'পোশাক', 'ট্রেন্ড', 'টুরিজম', 'পর্যটন', 'শপিং'
            ],
            'মতামত': [
                'মতামত', 'বিশ্লেষণ', 'কলাম', 'সম্পাদকীয়', 'দৃষ্টিভঙ্গি', 'মন্তব্য', 'পর্যালোচনা',
                'সমালোচনা', 'প্রবন্ধ', 'আলোচনা', 'গবেষণা'
            ],
            'ধর্ম': [
                'ইসলাম', 'ধর্ম', 'নামাজ', 'হজ', 'রমজান', 'ঈদ', 'মুসলিম', 'ইসলামী', 'কোরআন',
                'হাদিস', 'মসজিদ', 'ইমাম', 'জুমা', 'হিন্দু', 'পূজা', 'মন্দির', 'খ্রিস্টান'
            ]
        }
        
        # Score categories based on keyword matches
        category_scores = {}
        for category, keywords in content_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_to_check)
            if score > 0:
                category_scores[category] = score
        
        # Return highest scoring category if any matches found
        if category_scores:
            return max(category_scores, key=category_scores.get)
    
    # Default category for unmatched URLs
    return 'সাধারণ'

def categorize_articles(articles):
    """
    Add category detection to a list of articles
    
    Args:
        articles: List of article dictionaries with 'url', 'title', 'content' etc.
    
    Returns:
        List of articles with 'category' field added
    """
    categorized_articles = []
    
    for article in articles:
        # Create a copy to avoid modifying original
        categorized_article = article.copy()
        
        # Detect category
        category = detect_category_from_url(
            article.get('url', ''),
            article.get('title', ''),
            article.get('content', '') or article.get('text', '')
        )
        
        categorized_article['category'] = category
        categorized_articles.append(categorized_article)
    
    return categorized_articles

# Enhanced optimize function with category support
def optimize_text_for_ai_analysis_with_categories(texts, analyzer, max_chars=12000, max_articles=150, enable_categories=True):
    """
    Enhanced text optimization with category-wise formatting for better LLM analysis
    Updated for 5000 token capacity (12000 chars ≈ 4800 tokens)
    
    Args:
        texts: List of text articles (can include url, title, content fields)
        analyzer: TrendingBengaliAnalyzer instance
        max_chars: Maximum characters in output (default 12000 for 5000 token capacity)
        max_articles: Maximum number of articles to process (default 150)
        enable_categories: Whether to group by categories
    
    Returns:
        Formatted text optimized for LLM analysis with category grouping
    """
    print(f"🔧 Optimizing {len(texts)} texts with category support...")
    
    if not texts:
        return ""
    
    # If texts are dictionaries with metadata, extract and categorize
    if enable_categories and texts and isinstance(texts[0], dict):
        categorized_texts = categorize_articles(texts[:max_articles])
        
        # Group by category
        category_groups = defaultdict(list)
        for article in categorized_texts:
            category = article.get('category', 'সাধারণ')
            # Use title or content for text processing
            text_content = article.get('title', '') or article.get('content', '') or article.get('text', '')
            if text_content:
                category_groups[category].append(text_content)
        
        # Category weights for prioritization
        category_weights = {
            'রাজনীতি': 1.5,      # Politics - highest priority
            'অর্থনীতি': 1.3,      # Economics - high priority
            'আন্তর্জাতিক': 1.2,   # International - medium-high
            'খেলাধুলা': 1.0,      # Sports - normal
            'প্রযুক্তি': 1.1,      # Technology - slightly higher
            'বিনোদন': 0.9,       # Entertainment - lower
            'লাইফস্টাইল': 0.8,    # Lifestyle - lower
            'সাধারণ': 1.0         # General - normal
        }
        
        # Sort categories by weight
        sorted_categories = sorted(category_groups.keys(), 
                                 key=lambda x: category_weights.get(x, 1.0), 
                                 reverse=True)
        
        formatted_sections = []
        total_chars = 0
        
        # Process each category
        for category in sorted_categories:
            if total_chars >= max_chars * 0.9:  # Leave some buffer
                break
                
            category_texts = category_groups[category]
            if not category_texts:
                continue
            
            # Process this category's texts using original function
            category_optimized = optimize_text_for_ai_analysis(
                category_texts, 
                analyzer, 
                max_chars=max_chars // len(sorted_categories), 
                max_articles=len(category_texts)
            )
            
            if category_optimized.strip():
                section = f"{category}: {category_optimized}"
                if total_chars + len(section) < max_chars:
                    formatted_sections.append(section)
                    total_chars += len(section)
        
        result = " | ".join(formatted_sections)
        
        print(f"✅ Category-optimized to {len(result)} chars from {len(texts)} texts")
        print(f"🏷️ Categories processed: {len(formatted_sections)}")
        
        return result
    
    else:
        # Fallback to original function for simple text lists
        # Convert dict articles to text strings
        text_list = []
        for item in texts:
            if isinstance(item, dict):
                # Extract text from dict
                text_content = item.get('title', '') or item.get('content', '') or item.get('text', '')
                if text_content:
                    text_list.append(text_content)
            else:
                # Already a string
                text_list.append(str(item))
        
        return optimize_text_for_ai_analysis(text_list, analyzer, max_chars, max_articles)

def process_mixed_content_for_llm(newspaper_articles: List[Dict], social_media_content: List[Dict], 
                                analyzer, max_chars: int = 12000) -> Dict[str, str]:
    """
    Process mixed newspaper and social media content for LLM analysis
    Creates separate optimized texts for each source type
    
    Args:
        newspaper_articles: List of newspaper articles with metadata
        social_media_content: List of social media content items
        analyzer: TrendingBengaliAnalyzer instance
        max_chars: Maximum characters per source type
        
    Returns:
        Dictionary with separate optimized texts for each source
    """
    print(f"🔄 Processing mixed content: {len(newspaper_articles)} newspaper + {len(social_media_content)} social media")
    
    result = {
        'newspaper_text': '',
        'social_media_text': '',
        'combined_text': '',
        'source_stats': {
            'newspaper_count': len(newspaper_articles),
            'social_media_count': len(social_media_content),
            'total_items': len(newspaper_articles) + len(social_media_content)
        }
    }
    
    # Process newspaper content with categories
    if newspaper_articles:
        print("📰 Processing newspaper content with categories...")
        newspaper_text = optimize_text_for_ai_analysis_with_categories(
            newspaper_articles,
            analyzer,
            max_chars=max_chars // 2,  # Half for newspapers
            max_articles=100,
            enable_categories=True
        )
        result['newspaper_text'] = newspaper_text
        print(f"📰 Newspaper text optimized: {len(newspaper_text)} chars")
    
    # Process social media content
    if social_media_content:
        print("📱 Processing social media content...")
        
        # Group social media content by platform/subreddit
        platform_groups = defaultdict(list)
        for item in social_media_content:
            platform = item.get('subreddit', item.get('platform', 'unknown'))
            # Extract text content for processing
            text_content = item.get('content', '') or item.get('text_content', '')
            if text_content:
                platform_groups[platform].append(text_content)
        
        # Create platform-organized text
        social_sections = []
        remaining_chars = max_chars // 2  # Half for social media
        
        # Sort platforms by content volume (prioritize active subreddits)
        sorted_platforms = sorted(platform_groups.keys(), 
                                key=lambda x: len(platform_groups[x]), 
                                reverse=True)
        
        for platform in sorted_platforms:
            if remaining_chars <= 100:  # Leave some buffer
                break
                
            platform_texts = platform_groups[platform]
            
            # Process this platform's content
            platform_optimized = optimize_text_for_ai_analysis(
                platform_texts,
                analyzer,
                max_chars=min(remaining_chars // len(sorted_platforms), 2000),
                max_articles=len(platform_texts)
            )
            
            if platform_optimized.strip():
                section = f"📱{platform}: {platform_optimized}"
                if len(section) < remaining_chars:
                    social_sections.append(section)
                    remaining_chars -= len(section)
        
        social_media_text = " | ".join(social_sections)
        result['social_media_text'] = social_media_text
        print(f"📱 Social media text optimized: {len(social_media_text)} chars")
    
    # Create combined text with source labels
    combined_parts = []
    if result['newspaper_text']:
        combined_parts.append(f"📰সংবাদ: {result['newspaper_text']}")
    if result['social_media_text']:
        combined_parts.append(f"📱সামাজিক মাধ্যম: {result['social_media_text']}")
    
    result['combined_text'] = " || ".join(combined_parts)
    
    print(f"🎯 Mixed content processing complete:")
    print(f"   📰 Newspaper: {len(result['newspaper_text'])} chars")
    print(f"   📱 Social Media: {len(result['social_media_text'])} chars")
    print(f"   🔗 Combined: {len(result['combined_text'])} chars")
    
    return result

def create_mixed_content_llm_prompt(combined_text, limit):
    """
    Create LLM prompt for mixed content (newspaper + social media).
    
    Args:
        combined_text: String with mixed content
        limit: Number of trending words to generate
    
    Returns:
        str: LLM prompt
    """
    return f"""
আপনি একজন বাংলা ভাষার বিশেষজ্ঞ এবং সংবাদ বিশ্লেষক। আজকের (২০২৫-০৬-২৪) বাংলাদেশের সংবাদপত্র এবং সামাজিক মিডিয়ার মিশ্র কনটেন্ট থেকে ট্রেন্ডিং শব্দ/বাক্যাংশ তৈরি করতে হবে।

**বিশ্লেষণের জন্য কনটেন্ট:**
{combined_text}

**নির্দেশনা:**
১. সংবাদপত্র এবং সামাজিক মিডিয়া - উভয় মাধ্যমের গুরুত্বপূর্ণ বিষয়গুলো বিবেচনা করুন
২. সর্বোচ্চ {limit}টি ট্রেন্ডিং শব্দ/বাক্যাংশ তৈরি করুন
৩. প্রতিটি এন্ট্রি ২-৮ শব্দের মধ্যে হতে হবে
৪. রাজনৈতিক, অর্থনৈতিক, সামাজিক, আন্তর্জাতিক, খেলাধুলা, প্রযুক্তি এবং বিনোদন - সব ক্ষেত্র থেকে নির্বাচন করুন
৫. সামাজিক মিডিয়ার প্রভাবশালী আলোচনাগুলোকে অগ্রাধিকার দিন
৬. শুধুমাত্র বাংলায় উত্তর দিন

**আউটপুট ফরম্যাট:**
১. [শব্দ/বাক্যাংশ]
২. [শব্দ/বাক্যাংশ]
৩. [শব্দ/বাক্যাংশ]

এভাবে {limit}টি এন্ট্রি তৈরি করুন।
"""
