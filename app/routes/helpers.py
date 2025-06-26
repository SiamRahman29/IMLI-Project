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
        seen_urls = set()
        for entry in feed.entries:
            url = entry.get('link', '')
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            try:
                res = robust_request(url)
                if not res:
                    continue
                soup = BeautifulSoup(res.text, "html.parser")
                # Only use h1 tags for headings
                headings = [tag.text.strip() for tag in soup.find_all('h1') if tag.text.strip()]
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
        "https://www.jugantor.com/tech"
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
        "https://sangbad.net.bd/opinion/open-discussion/"
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
    try:
        homepage = "https://www.dailynayadiganta.com/"
        res = robust_request(homepage)
        if not res:
            return articles
        soup = BeautifulSoup(res.text, "html.parser")
        seen_urls = set()
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
        for link in soup.select("h2 a, h3 a, a[href*='/news/'], a[href*='/details/']"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
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
                # Only use h1 tags for headings
                headings = [tag.text.strip() for tag in article_soup.find_all('h1') if tag.text.strip()]
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
                # Only use h1 tags for headings
                headings = [tag.text.strip() for tag in article_soup.find_all('h1') if tag.text.strip()]
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



def generate_trending_word_candidates_realtime_with_save(db: Session, limit: int = 15, sources: List[str] = None) -> str:
    """Generate trending word candidates using REAL-TIME analysis with selective data sources and save top 15 LLM words to database"""
    
    # Default to both sources if not specified
    if sources is None:
        sources = ['newspaper', 'reddit']
    
    print(f"Starting real-time trending analysis with selected sources: {sources}")
    print("=" * 60)
    
    # Fetch news articles (conditional based on source selection)
    articles = []
    texts = []
    if 'newspaper' in sources:
        print("📰 Fetching newspaper content...")
        articles = fetch_news() or []
        # Use only heading for content (as requested)
        for a in articles:
            heading = a.get('heading', '').strip() 
            if heading:
                texts.append(heading)
        print(f"📰 Extracted {len(texts)} text segments from {len(articles)} scraped articles")
    else:
        print("⏭️ Skipping newspaper content (not selected)")
    
    # Fetch social media content (conditional based on source selection)
    social_media_content = []
    if 'reddit' in sources:
        try:
            print("📱 Fetching social media content (Reddit)...")
            from app.services.social_media_scraper import scrape_social_media_content
            social_media_content = scrape_social_media_content()
            print(f"📱 Retrieved {len(social_media_content)} social media items")
        except Exception as e:
            print(f"⚠️ Social media scraping failed: {e}")
            social_media_content = []
    else:
        print("⏭️ Skipping Reddit content (not selected)")
    
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

                    এভাবে {limit}টি এন্ট্রি তৈরি করুন।
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
        # Import the category-wise analyzer from routes_new.py
        from app.services.filtered_newspaper_service import FilteredNewspaperScraper
        from app.services.category_llm_analyzer import (
            get_জাতীয়_trending_words, get_অর্থনীতি_trending_words, get_রাজনীতি_trending_words,
            get_লাইফস্টাইল_trending_words, get_বিনোদন_trending_words, get_খেলাধুলা_trending_words,
            get_ধর্ম_trending_words, get_চাকরি_trending_words, get_শিক্ষা_trending_words,
            get_স্বাস্থ্য_trending_words, get_মতামত_trending_words, get_বিজ্ঞান_trending_words
        )
        
        # Target categories
        TARGET_CATEGORIES = [
            'জাতীয়', 'অর্থনীতি', 'রাজনীতি', 'লাইফস্টাইল', 'বিনোদন', 
            'খেলাধুলা', 'ধর্ম', 'চাকরি', 'শিক্ষা', 'স্বাস্থ্য', 'মতামত', 'বিজ্ঞান'
        ]
        
        print(f"🚀 Starting filtered newspaper scraping for {len(TARGET_CATEGORIES)} categories...")
        
        # Initialize filtered newspaper scraper
        scraper = FilteredNewspaperScraper(TARGET_CATEGORIES)
        
        # Scrape all newspapers with category filtering
        results = scraper.scrape_all_newspapers()
        
        print(f"📊 Scraped {results['scraping_info']['total_articles']} articles")
        
        # Category-wise LLM trending word extraction
        category_functions = {
            'জাতীয়': get_জাতীয়_trending_words,
            'অর্থনীতি': get_অর্থনীতি_trending_words,
            'রাজনীতি': get_রাজনীতি_trending_words,
            'লাইফস্টাইল': get_লাইফস্টাইল_trending_words,
            'বিনোদন': get_বিনোদন_trending_words,
            'খেলাধুলা': get_খেলাধুলা_trending_words,
            'ধর্ম': get_ধর্ম_trending_words,
            'চাকরি': get_চাকরি_trending_words,
            'শিক্ষা': get_শিক্ষা_trending_words,
            'স্বাস্থ্য': get_স্বাস্থ্য_trending_words,
            'মতামত': get_মতামত_trending_words,
            'বিজ্ঞান': get_বিজ্ঞান_trending_words
        }
        
        # Extract trending words for each category
        all_trending_words = []
        category_wise_trending = {}
        
        for category in TARGET_CATEGORIES:
            articles = results['category_wise_articles'][category]
            
            if articles:
                print(f"🤖 Processing {category} category with {len(articles)} articles...")
                
                # Get trending words for this category using LLM
                trending_words = category_functions[category](articles)
                
                category_wise_trending[category] = trending_words
                all_trending_words.extend(trending_words)
                
                print(f"✅ {category}: {len(trending_words)} trending words extracted")
            else:
                print(f"⚠️ {category}: No articles found")
                category_wise_trending[category] = []
        
        print(f"🎉 Total trending words extracted from newspapers: {len(all_trending_words)}")
        
        return {
            "status": "success",
            "message": f"Category-wise analysis completed with {len(all_trending_words)} words",
            "category_wise_trending": category_wise_trending,
            "trending_words": all_trending_words,
            "scraping_info": results['scraping_info']
        }
        
    except Exception as e:
        import traceback
        error_detail = f"Newspaper category analysis failed: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_detail}")
        return {
            "status": "failed",
            "message": error_detail,
            "trending_words": []
        }


def reddit_trending_analysis(db: Session, sources: List[str]) -> Dict[str, any]:
    """
    Perform Reddit analysis as per user workflow requirements
    
    Returns:
        Dict with Reddit LLM response and trending words
    """
    if 'reddit' not in sources:
        return {
            "status": "skipped", 
            "message": "Reddit source not selected",
            "trending_words": []
        }
    
    print("📡 Starting Reddit trending analysis...")
    
    try:
        # Import Reddit scraper
        import sys
        import os
        
        # Add the project root to Python path
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from app.services.reddit_data_scrapping import RedditDataScrapper
        
        # Create Reddit scraper and run analysis
        scraper = RedditDataScrapper()
        reddit_results = scraper.run_comprehensive_analysis(posts_per_subreddit=20)
        
        # Extract emerging words from Reddit results
        emerging_words = reddit_results.get('emerging_words', [])
        reddit_trending = [item['emerging_word'] for item in emerging_words if item.get('emerging_word')]
        
        print(f"📡 Reddit analysis completed with {len(reddit_trending)} trending words")
        
        return {
            "status": "success",
            "message": f"Reddit analysis completed with {len(reddit_trending)} words",
            "trending_words": reddit_trending,
            "subreddit_results": reddit_results.get('subreddit_responses', []),
            "summary": reddit_results.get('summary', {})
        }
        
    except Exception as e:
        import traceback
        error_detail = f"Reddit analysis failed: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_detail}")
        return {
            "status": "failed",
            "message": error_detail,
            "trending_words": []
        }
