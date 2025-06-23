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
        # ("kaler_kantho", scrape_kaler_kantho),
        ("jugantor", scrape_jugantor),
        ("ittefaq", scrape_ittefaq),
        # ("bd_pratidin", scrape_bd_pratidin),
        ("manab_zamin", scrape_manab_zamin),
        # ("samakal", scrape_samakal),
        # ("amader_shomoy", scrape_amader_shomoy),
        ("janakantha", scrape_janakantha),
        ("inqilab", scrape_inqilab),
        # ("sangbad", scrape_sangbad),
        # ("noya_diganta", scrape_noya_diganta),
        # ("jai_jai_din", scrape_jai_jai_din),
        ("manobkantha", scrape_manobkantha),
        ("ajkaler_khobor", scrape_ajkaler_khobor),
        ("ajker_patrika", scrape_ajker_patrika),
        # ("protidiner_sangbad", scrape_protidiner_sangbad),
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
    """Generate trending word candidates using REAL-TIME analysis and save top 15 LLM words to database"""
    print("Starting real-time trending analysis with database save...")
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
    
    # Fetch Google Trends
    google_trends = get_google_trends_bangladesh()
    # Fetch YouTube trending
    youtube_trends = get_youtube_trending_bangladesh()
    # Fetch SerpApi Google Trends
    serpapi_trends = get_serpapi_trending_bangladesh()
    
    # print("[SerpApi] Final trending phrases (Bangladesh):")
    for idx, trend in enumerate(serpapi_trends, 1):
        print(f"  {idx}. {' '.join(trend) if isinstance(trend, list) else trend}")
    
    # Combine all sources for AI
    texts.extend([' '.join(words) for words in google_trends if words])
    texts.extend([' '.join(words) for words in youtube_trends if words])
    texts.extend([' '.join(trend) for trend in serpapi_trends if trend])
    
    if not texts:
        msg = "No articles or trends available for analysis"
        print(msg)
        return msg
    
    # --- AI Response (Groq) ---
    from app.services.advanced_bengali_nlp import TrendingBengaliAnalyzer
    analyzer = TrendingBengaliAnalyzer()
    # Use ULTRA optimized text processing for Groq token limits
    print(f"🔧 Using ULTRA optimization for {len(texts)} total texts...")
    combined_text = optimize_text_for_ai_analysis(texts, analyzer, max_chars=2500, max_articles=100)  # Much stricter limits
    print(f"📊 Ultra-Optimized Combined Text Size: {len(combined_text)} characters")
    print(f"📊 Successfully optimized from {len(texts)} original texts")
    ai_response = None
    print(f"Combined Text Preview (first 100 chars): {combined_text[:100]}...")
    
    # Token estimation for Groq limits
    estimated_tokens = len(combined_text) // 2  # More conservative for Bengali
    print(f"🎯 Estimated tokens: ~{estimated_tokens:.0f} (Groq limit: 12,000)")
    
    if estimated_tokens > 10000:  # More safety margin
        print("⚠️  Text might still be too long, further reducing...")
        # Emergency truncation
        safe_chars = int(10000 * 2)
        if len(combined_text) > safe_chars:
            combined_text = combined_text[:safe_chars-3] + "..."
            print(f"🔧 Emergency truncated to {len(combined_text)} characters")

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
                timeout=60.0  # 60 second timeout for client
            )
        except Exception as client_error:
            print(f"❌ Failed to initialize Groq client: {client_error}")
            raise client_error
        
        prompt = f"""
            নিচের বাংলা সংবাদের টেক্সট থেকে আজকের জন্য সবচেয়ে গুরুত্বপূর্ণ এবং trending {limit}টি শব্দ বা বাক্যাংশ খুঁজে বের করো যা বিশেষভাবে noun (বিশেষ্য) এবং adjective (বিশেষণ) প্রকৃতির এবং অর্থবহ।

            **অবশ্যই অনুসরণীয় নিয়মাবলী:**
            1. **Noun (বিশেষ্য) এবং Adjective (বিশেষণ) ভিত্তিক অর্থবহ শব্দ/বাক্যাংশ দাও**
            2. **Hot trending topics/phrases খুঁজে বের করো** - যা এখন সবচেয়ে জনপ্রিয় এবং আলোচিত
            3. **একটি টপিকের জন্য শুধুমাত্র একটি প্রতিনিধিত্বকারী phrase দাও**
            4. **কোনো ব্যক্তির নাম দিও না** (যেমন: ট্রাম্প, বাইডেন, মোদি, হাসিনা ইত্যাদি)
            5. **ছোট ও সংক্ষিপ্ত phrase দাও** - সর্বোচ্চ ২-৪ শব্দ। দীর্ঘ বাক্য দিও না
            6. **সাধারণ stop words এবং verb (ক্রিয়া) এড়িয়ে চলো** (যেমন: এই, সেই, করা, হওয়া, যে, যার, বলা, দেওয়া, নেওয়া)
            7. **শুধুমাত্র বিষয়বস্তু/থিম ভিত্তিক concrete noun/adjective phrase দাও** - খবরের মূল বিষয় যা trending
            8. **প্রতিটি শব্দ/বাক্যাংশ সংখ্যা দিয়ে আলাদা লাইনে লেখো** (১., ২., ৩.... ৪. ইত্যাদি)
            9. **শুধুমাত্র বাংলা শব্দ/বাক্যাংশ দাও**
            10. **একই টপিকের ভিন্ন ভিন্ন রূপ এড়িয়ে চলো** - সবচেয়ে প্রতিনিধিত্বকারী একটি phrase দাও

            # উদাহরণ (শুধুমাত্র বোঝার জন্য - এগুলো অবশ্যই ব্যবহার করতে হবে এমন নয়):
            # ✔️ ভালো ধরনের: "ইসরাইল-ইরানের সংঘাত", "জ্বালানি সংকট", "নির্বাচনী প্রচারণা", "অর্থনৈতিক মন্দা", "শিক্ষা সংকট"
            # ❌ এড়িয়ে চলো: "ইরানের", "হামলা", "ট্রাম্প বলছেন যে...", "সরকার নিখোঁজ করে...", "বলেছেন", "করেছেন"

            টেক্সট:
            {combined_text}

            trending শব্দ/বাক্যাংশ ({limit}টি):
            """
        
        print(f"📤 Sending request to Groq API...")
        print(f"📊 Prompt length: {len(prompt)} characters")
        
        # Retry logic for Groq API connection issues
        max_retries = 3
        retry_delay = 2
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
                    max_tokens=1000,
                    timeout=30.0  # 30 second timeout
                )
                print(f"✅ API call successful on attempt {attempt + 1}")
                break
                
            except Exception as api_error:
                print(f"❌ API attempt {attempt + 1} failed: {str(api_error)}")
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
    
    # --- NLP Analysis Response (WITHOUT DATABASE for NLP results) ---
    analyzer_inputs = []
    for a in articles:
        analyzer_inputs.append({
            'title': a.get('title', ''),
            'heading': a.get('heading', ''),
            'source': a.get('source', 'news')
        })
    
    for trend in google_trends:
        analyzer_inputs.append({'title': ' '.join(trend), 'heading': '', 'source': 'google_trends'})
    
    for trend in youtube_trends:
        analyzer_inputs.append({'title': ' '.join(trend), 'heading': '', 'source': 'youtube_trending'})
    
    for trend in serpapi_trends:
        analyzer_inputs.append({'title': ' '.join(trend) if isinstance(trend, list) else trend, 'heading': '', 'source': 'serpapi_trends'})
    
    print(f"\n🧠 Running NLP Analysis on {len(analyzer_inputs)} inputs...")
    analyzer_response = analyzer.analyze_trending_content(analyzer_inputs, source_type='mixed')
    
    # Count unique newspaper sources from analyzer inputs
    newspaper_sources = set()
    for item in analyzer_inputs:
        item_source = item.get('source', 'unknown')
        if item_source not in ['google_trends', 'youtube_trending', 'serpapi_trends', 'unknown']:
            newspaper_sources.add(item_source)
    
    newspaper_count = len(newspaper_sources)
    print(f"📰 Summary includes content from {newspaper_count} newspaper sources")
    
    # Start with empty summary array and add heading separately at the end
    summary = []
    trending_keywords = analyzer_response.get('trending_keywords', [])
    
    if not isinstance(trending_keywords, list):
        print(f"[Analyzer] 'trending_keywords' missing or not a list. analyzer_response: {analyzer_response}")
        trending_keywords = []
    
    # Track which newspapers contain each phrase for summary
    phrase_newspaper_counts = {}
    for keyword_score in trending_keywords[:10]:
        if isinstance(keyword_score, (list, tuple)) and len(keyword_score) == 2:
            keyword, score = keyword_score
            keyword_clean = keyword.strip()
            
            # Count how many newspapers contain this phrase
            newspapers_with_phrase = set()
            for item in analyzer_inputs:
                title = item.get('title', '').lower()
                heading = item.get('heading', '').lower()
                combined_text = f"{title} {heading}".lower()
                
                if keyword_clean.lower() in combined_text:
                    item_source = item.get('source', 'unknown')
                    if item_source not in ['google_trends', 'youtube_trending', 'serpapi_trends', 'unknown']:
                        newspapers_with_phrase.add(item_source)
            
            phrase_newspapers = len(newspapers_with_phrase)
            phrase_newspaper_counts[keyword_clean] = phrase_newspapers
        
    # Add trending keywords to summary with newspaper counts
    for keyword_score in trending_keywords[:10]:
        if isinstance(keyword_score, (list, tuple)) and len(keyword_score) == 2:
            keyword, score = keyword_score
            keyword_clean = keyword.strip()
            phrase_newspapers = phrase_newspaper_counts.get(keyword_clean, 0)
            summary.append(f"  🔸 {keyword}: {score:.4f} | Newspapers: {phrase_newspapers}/{newspaper_count}")
        else:
            summary.append(f"  🔸 {keyword_score}")
    
    summary.append("\n🏷️ Named Entities:")
    for entity_type, entities in analyzer_response.get('named_entities', {}).items():
        if entities:
            summary.append(f"  📍 {entity_type}: {entities[:5]}")
    
    summary.append(f"\n💭 Sentiment: {analyzer_response.get('sentiment_analysis', '')}")
    summary.append(f"\n📈 Statistics: {analyzer_response.get('content_statistics', '')}")
    
    # Final summary
    summary.append(f"\n🤖 AI Generated Trending Words:\n{ai_response}")
    summary.append(f"\n💾 Database Status: Top 15 LLM trending words saved for trending analysis section")
    
    # Add the combined text for frontend debugging
    summary.append(f"\n📋 সম্পূর্ণ AI প্রার্থিতালিকা:")
    summary.append(f"📊 Groq API তে পাঠানো Combined Text ({len(combined_text)} chars):")
    summary.append(f"{'='*50}")
    summary.append(combined_text)
    summary.append(f"{'='*50}")
    
    # Add heading at the beginning
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
                    phrase=keyword_clean,
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

def optimize_text_for_ai_analysis(texts, analyzer, max_chars=2500, max_articles=100):
    """
    ULTRA optimize large volume of texts for Groq token limits
    Target: 2500 chars max for better performance
    
    Strategy:
    1. Extract only top keywords from each article  
    2. Heavy deduplication
    3. Strict character limits
    4. Priority-based selection
    """
    print(f"🔧 ULTRA optimizing {len(texts)} texts for Groq API limits...")
    
    if not texts:
        return ""
    
    # Step 1: Extract ONLY key keywords from each text (super compact)
    optimized_keywords = []
    processed_count = 0
    
    for text in texts[:max_articles]:  # Strict article limit
        if not text or len(text.strip()) < 3:
            continue
            
        # Normalize and extract meaningful words
        normalized = analyzer.processor.normalize_text(text)
        tokens = analyzer.processor.advanced_tokenize(normalized)
        
        # Keep only the BEST meaningful words (very strict filtering)
        meaningful_words = [
            w for w in tokens 
            if w not in analyzer.processor.stop_words 
            and len(w) >= 3  # Min 3 chars
            and not w.isdigit()  # No numbers
            and len(w) <= 12  # Reduced max length
        ]
        
        if len(meaningful_words) >= 1:  # Need at least 1 word
            # Take only TOP 1 word per article + 1 short bigram max
            top_keywords = meaningful_words[:1]  # Only 1 word per article
            
            # Add 1 very short bigram if possible
            if len(meaningful_words) >= 2:
                bigram = ' '.join(meaningful_words[:2])
                if len(bigram) <= 15:  # Very short bigrams only
                    top_keywords.append(bigram)
            
            # Join with minimal separator, max 25 chars per article
            article_keywords = ' '.join(top_keywords[:2])  # Max 2 elements
            if len(article_keywords) > 25:
                article_keywords = article_keywords[:22] + "..."
                
            optimized_keywords.append(article_keywords)
            processed_count += 1
    
    print(f"📊 Processed {processed_count} articles into ultra-compact keywords")
    
    # Step 2: HEAVY deduplication (remove similar content aggressively)
    unique_keywords = []
    seen_words = set()
    
    for keywords in optimized_keywords:
        # Split into words and check for significant overlap
        words = set(keywords.lower().replace(' ', '_').split())
        
        # Check overlap with existing content (more aggressive)
        has_significant_overlap = False
        for existing_words in seen_words:
            if words and existing_words:
                overlap = len(words.intersection(existing_words))
                if overlap > 0 and overlap / max(len(words), len(existing_words)) > 0.3:  # 30% overlap = skip (more aggressive)
                    has_significant_overlap = True
                    break
        
        if not has_significant_overlap and words:
            seen_words.add(frozenset(words))
            unique_keywords.append(keywords)
    
    print(f"🔄 Heavy deduplication: {len(optimized_keywords)} -> {len(unique_keywords)} unique entries")
    
    # Step 3: Smart truncation to fit token limits
    if not unique_keywords:
        return ""
    
    # Score and prioritize keywords
    keywords_with_score = []
    for keyword_set in unique_keywords:
        words = keyword_set.split()
        # Score: favor diverse, meaningful words
        unique_word_count = len(set(words))
        total_length = len(keyword_set)
        score = unique_word_count * 3 + (total_length * 0.1)  # Favor diversity over length
        keywords_with_score.append((keyword_set, score))
    
    # Sort by score and build final text
    keywords_with_score.sort(key=lambda x: x[1], reverse=True)
    
    final_keywords = []
    current_chars = 0
    
    for keyword_set, score in keywords_with_score:
        # Add keyword set if it fits
        addition_length = len(keyword_set) + 1  # +1 for separator
        if current_chars + addition_length <= max_chars:
            final_keywords.append(keyword_set)
            current_chars += addition_length
        else:
            # Try to fit a truncated version if significant space remains
            remaining_space = max_chars - current_chars - 1
            if remaining_space > 15:  # Only if meaningful space
                truncated = keyword_set[:remaining_space-3] + "..."
                final_keywords.append(truncated)
            break
    
    combined_text = ' | '.join(final_keywords)  # Use pipe separator for compactness
    
    # Final safety check
    if len(combined_text) > max_chars:
        combined_text = combined_text[:max_chars-3] + "..."
    
    # Calculate compression stats
    original_total = sum(len(t) for t in texts if t)
    compression_ratio = len(combined_text) / max(original_total, 1) * 100
    
    print(f"✅ ULTRA-compressed: {len(combined_text)} chars from {len(texts)} texts")
    print(f"📈 Compression: {compression_ratio:.2f}% of original size")
    print(f"🎯 Token estimate: ~{len(combined_text)//3} tokens (limit: 12k)")
    
    return combined_text
