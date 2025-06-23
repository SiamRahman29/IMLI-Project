"""
Advanced Bengali Text Analytics Service
Implements state-of-the-art NLP techniques for Bengali language processing
"""

import re
import pickle
import os
from typing import List, Dict, Tuple, Set
from collections import Counter, defaultdict
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from app.services.stopwords import STOP_WORDS


class AdvancedBengaliProcessor:
    
    def __init__(self):
        self.stop_words = STOP_WORDS
        
        self.sentence_enders = {'।', '!', '?', '...', '!!', '???'}
        
        self.punctuation = {
            '।', '!', '?', ',', ';', ':', '"', "'", '(', ')', '[', ']', '{', '}',
            '...', '!!', '???', '—', '-', '–', '৷', '৹', '৺', '৻'
        }
        
        # Load or create word frequency cache
        self.word_freq_cache = {}
        self.load_word_frequency_model()
    
    def load_word_frequency_model(self):
        """Load pre-trained word frequency model or create new one"""
        model_path = "models/bengali_word_freq.pkl"
        
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    self.word_freq_cache = pickle.load(f)
                print("Loaded Bengali word frequency model")
            except Exception as e:
                print(f"Error loading word frequency model: {e}")
                self.word_freq_cache = {}
        else:
            print("No pre-trained word frequency model found. Will build dynamically.")
    
    def save_word_frequency_model(self):
        """Save word frequency model for future use"""
        os.makedirs("models", exist_ok=True)
        model_path = "models/bengali_word_freq.pkl"
        
        try:
            with open(model_path, 'wb') as f:
                pickle.dump(self.word_freq_cache, f)
            print("Saved Bengali word frequency model")
        except Exception as e:
            print(f"Error saving word frequency model: {e}")
    
    def normalize_text(self, text: str) -> str:
        if not text:
            return ""
        
        text = re.sub(r'[\u200C\u200D]', '', text)  # Remove ZWJ and ZWNJ
        
        text = re.sub(r'ৗ', 'ৌ', text)  # Normalize au vowel
        text = re.sub(r'ো', 'ো', text)  # Normalize o vowel
        
        text = re.sub(r'[।!?]{3,}', '।', text)
        text = re.sub(r'[.]{3,}', '...', text)
        
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def advanced_tokenize(self, text: str) -> List[str]:
        """Advanced tokenization for Bengali text"""
        try:
            if not isinstance(text, str):
                text = str(text) if text is not None else ""
            
            text = self.normalize_text(text)
            
            sentences = []
            current_sentence = ""
            
            for char in text:
                if char in self.sentence_enders:
                    if current_sentence.strip():
                        sentences.append(current_sentence.strip())
                    current_sentence = ""
                else:
                    current_sentence += char
            
            if current_sentence.strip():
                sentences.append(current_sentence.strip())
            
            # Tokenize words from sentences
            words = []
            for sentence in sentences:
                # Remove punctuation except for compound words
                sentence = re.sub(r'[^\u0980-\u09FF\s-]', ' ', sentence)
                
                # Split by whitespace and filter
                sentence_words = sentence.split()
                for word in sentence_words:
                    word = word.strip('-')
                    if len(word) > 1 and word not in self.stop_words:
                        # Ensure the word is a string
                        words.append(str(word))
            
            return words
            
        except Exception as e:
            print(f"Error in advanced_tokenize: {e}")
            # Fallback tokenization
            if isinstance(text, str):
                simple_words = text.split()
                return [str(w) for w in simple_words if w and len(w) > 1]
            else:
                return []
    # Named Entity Recognition
    def extract_named_entities(self, text: str) -> Dict[str, List[str]]:
        entities = {
            'persons': [],
            'places': [],
            'organizations': [],
            'dates': []
        }
        
        person_patterns = [
            r'(?:মাননীয়|জনাব|মিসেস|মিস|ডঃ|প্রফেসর|শেখ|মোঃ|সৈয়দ)\s+([^\s]+(?:\s+[^\s]+)?)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:সাহেব|সাহেবা|বেগম|খান|চৌধুরী|আহমেদ|হোসেন)'
        ]
        
        place_patterns = [
            r'(ঢাকা|চট্টগ্রাম|সিলেট|রাজশাহী|খুলনা|বরিশাল|রংপুর|ময়মনসিংহ)',
            r'([^\s]+(?:পুর|গঞ্জ|নগর|শহর|বাজার|হাট))',
            r'([^\s]+\s+(?:জেলা|উপজেলা|থানা|ইউনিয়ন))'
        ]
        
        org_patterns = [
            r'([^\s]+(?:\s+[^\s]+)*)\s+(?:ব্যাংক|বিশ্ববিদ্যালয়|কলেজ|স্কুল|হাসপাতাল|কোম্পানি|লিমিটেড)',
            r'(?:বাংলাদেশ|সরকারি|বেসরকারি)\s+([^\s]+(?:\s+[^\s]+)*)'
        ]
        
        date_patterns = [
            r'(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})',
            r'([০-৯]{1,2}[/.-][০-৯]{1,2}[/.-][০-৯]{2,4})',
            r'(\d{1,2}\s+(?:জানুয়ারি|ফেব্রুয়ারি|মার্চ|এপ্রিল|মে|জুন|জুলাই|আগস্ট|সেপ্টেম্বর|অক্টোবর|নভেম্বর|ডিসেম্বর)\s+\d{4})'
        ]
        
        for pattern in person_patterns:
            matches = re.findall(pattern, text)
            entities['persons'].extend(matches)
        
        for pattern in place_patterns:
            matches = re.findall(pattern, text)
            entities['places'].extend(matches)
        
        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            entities['organizations'].extend(matches)
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            entities['dates'].extend(matches)
        
        for entity_type in entities:
            entities[entity_type] = list(set([e.strip() for e in entities[entity_type] if e.strip()]))
        
        return entities
    
    def calculate_text_sentiment(self, text: str) -> Dict[str, float]:
        """Basic sentiment analysis for Bengali text"""

        positive_words = {
            'ভালো', 'সুন্দর', 'চমৎকার', 'দারুণ', 'অসাধারণ', 'চমৎকার', 'খুশি', 'আনন্দ', 'উৎসাহ',
            'গর্ব', 'সফল', 'জয়', 'বিজয়', 'সাফল্য', 'প্রশংসা', 'ভালোবাসা', 'মিষ্টি', 'সুখ',
            'হাসি', 'হাসতে', 'পছন্দ', 'ভালোবাসি', 'পবিত্র', 'পুণ্য', 'শান্তি', 'আশা', 'স্বপ্ন'
        }
        
        negative_words = {
            'খারাপ', 'দুঃখ', 'কষ্ট', 'ব্যথা', 'যন্ত্রণা', 'রাগ', 'ক্রোধ', 'দুর্ভোগ', 'সমস্যা',
            'বিপদ', 'অসুখ', 'রোগ', 'মৃত্যু', 'মরে', 'মারা', 'হত্যা', 'চুরি', 'ডাকাতি', 'দুর্নীতি',
            'ঘৃণা', 'ভয়', 'আতঙ্ক', 'চিন্তা', 'দুশ্চিন্তা', 'হতাশা', 'ব্যর্থ', 'পরাজয়', 'হার'
        }
        
        words = self.advanced_tokenize(text.lower())
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        total_words = len(words)
        
        if total_words == 0:
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
        
        positive_score = positive_count / total_words
        negative_score = negative_count / total_words
        neutral_score = 1.0 - positive_score - negative_score
        
        return {
            'positive': positive_score,
            'negative': negative_score,
            'neutral': max(0.0, neutral_score)
        }
    
    def extract_trending_keywords(self, texts: List[str], top_k: int = 50) -> List[Tuple[str, float]]:
        """Extract trending keywords using advanced TF-IDF with custom Bengali preprocessing"""
        
        def bengali_preprocessor(text):
            words = self.advanced_tokenize(text)
            return ' '.join(words)
        
        def bengali_tokenizer(text):
            return text.split()
        
        # Custom TF-IDF with Bengali preprocessing
        vectorizer = TfidfVectorizer(
            tokenizer=bengali_tokenizer,
            preprocessor=bengali_preprocessor,
            ngram_range=(1, 3),
            max_features=1000,
            min_df=1,
            max_df=1.0,
            lowercase=False,
            token_pattern=None  # Suppress warning: token_pattern is ignored when tokenizer is set
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            
            # Create keyword-score pairs
            keyword_scores = list(zip(feature_names, mean_scores))
            
            # Sort by score and return top k
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            return keyword_scores[:top_k]
            
        except Exception as e:
            print(f"Error in trending keywords extraction: {e}")
            return []
    
    def cluster_similar_phrases(self, phrases: List[str], n_clusters: int = 5) -> Dict[int, List[str]]:
        """Cluster similar phrases using TF-IDF and K-means"""
        try:
            # Filter to only non-empty strings and ensure all are strings
            filtered_phrases = []
            for p in phrases:
                if p is not None and isinstance(p, str) and p.strip():
                    filtered_phrases.append(p.strip())
                elif p is not None:
                    # Convert non-string to string as fallback
                    str_p = str(p).strip()
                    if str_p:
                        filtered_phrases.append(str_p)
            
            phrases = filtered_phrases
            
            if len(phrases) == 0:
                print("No valid phrases for clustering")
                return {}
                
            if len(phrases) < n_clusters:
                # If we have fewer phrases than clusters, put each in its own cluster
                return {i: [phrase] for i, phrase in enumerate(phrases)}
            
            def safe_bengali_preprocessor(text):
                """Safe preprocessor that handles errors gracefully"""
                try:
                    if not isinstance(text, str):
                        text = str(text)
                    words = self.advanced_tokenize(text)
                    # Ensure all words are strings
                    safe_words = [str(w) for w in words if w is not None]
                    return ' '.join(safe_words)
                except Exception as e:
                    print(f"Error in preprocessor for text '{text}': {e}")
                    # Fallback: just return cleaned text
                    if isinstance(text, str):
                        return re.sub(r'[^\u0980-\u09FF\s]', ' ', text)
                    else:
                        return str(text)
            
            vectorizer = TfidfVectorizer(
                preprocessor=safe_bengali_preprocessor,
                ngram_range=(1, 2),
                max_features=500,
                min_df=1,
                lowercase=False,
                token_pattern=r'(?u)\b\w\w+\b'  # Use explicit pattern instead of None
            )
            
            tfidf_matrix = vectorizer.fit_transform(phrases)
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(tfidf_matrix)
            
            # Group phrases by cluster
            clustered_phrases = defaultdict(list)
            for phrase, cluster_id in zip(phrases, clusters):
                clustered_phrases[cluster_id].append(phrase)
            
            return dict(clustered_phrases)
            
        except Exception as e:
            print(f"Error in phrase clustering: {e}")
            import traceback
            print(f"Clustering error traceback: {traceback.format_exc()}")
            # Fallback: return all phrases in one cluster
            if phrases:
                return {0: phrases}
            else:
                return {}
    
    def calculate_phrase_importance(self, phrase: str, context_texts: List[str]) -> float:
        """Calculate importance score for a phrase within given context"""
        
        # Frequency in context
        phrase_lower = phrase.lower()
        frequency = sum(1 for text in context_texts if phrase_lower in text.lower())
        
        # Length bonus (longer phrases tend to be more specific)
        word_count = len(phrase.split())
        length_score = min(word_count * 0.3, 1.0)
        
        # Named entity bonus
        entities = self.extract_named_entities(phrase)
        entity_score = 0.2 if any(entities.values()) else 0.0
        
        # Frequency score (logarithmic to avoid outliers)
        freq_score = np.log(frequency + 1) * 0.5
        
        return freq_score + length_score + entity_score
    
    def update_word_frequency_cache(self, texts: List[str]):
        """Update word frequency cache with new texts"""
        for text in texts:
            words = self.advanced_tokenize(text)
            for word in words:
                self.word_freq_cache[word] = self.word_freq_cache.get(word, 0) + 1
    
    def filter_and_deduplicate_keywords(self, trending_keywords, max_results=15):
        """
        Filter and deduplicate trending keywords to avoid repetitive and low-quality phrases
        """
        if not trending_keywords:
            return []
        
        # Person name patterns to exclude
        person_indicators = [
            'মাননীয়', 'জনাব', 'মিসেস', 'মিস', 'ডঃ', 'প্রফেসর', 'শেখ', 'মোঃ', 'সৈয়দ',
            'সাহেব', 'সাহেবা', 'বেগম', 'খান', 'চৌধুরী', 'আহমেদ', 'হোসেন', 'উদ্দিন', 'রহমান'
        ]
        
        # Low-quality phrase patterns to exclude (compiled for safety)
        exclude_patterns = []
        try:
            pattern_strings = [
                r'বলেছেন যে',
                r'নিশ্চিত করেছে যে',
                r'জানিয়েছেন যে',
                r'সরকার.*যে',
                r'প্রধানমন্ত্রী.*যে',
                r'মন্ত্রী.*যে',
                r'.{30,}',  # Very long phrases (30+ characters)
            ]
            for pattern_str in pattern_strings:
                exclude_patterns.append(re.compile(pattern_str))
        except Exception as e:
            print(f"Error compiling regex patterns: {e}")
            exclude_patterns = []
        
        filtered_keywords = []
        seen_topics = set()
        
        for keyword, score in trending_keywords:
            try:
                keyword_text = str(keyword).strip() if keyword else ""
                
                # Skip if empty or too short
                if len(keyword_text) < 2:
                    continue
                
                # Skip if contains person indicators
                if any(indicator in keyword_text for indicator in person_indicators):
                    continue
                
                # Skip if matches exclude patterns (safely)
                skip_pattern = False
                for pattern in exclude_patterns:
                    try:
                        if pattern.search(keyword_text):
                            skip_pattern = True
                            break
                    except Exception as pattern_error:
                        print(f"Pattern search error: {pattern_error}")
                        continue
                
                if skip_pattern:
                    continue
                
                # Skip common stop words that might slip through
                if keyword_text in ['করা', 'হওয়া', 'দেওয়া', 'নেওয়া', 'বলা', 'আসা', 'যাওয়া']:
                    continue
                
                # Deduplicate similar topics
                # Check if this keyword is too similar to already selected ones
                is_duplicate = False
                normalized_keyword = keyword_text.lower().strip()
                
                for seen_topic in seen_topics:
                    # Check for substring relationship
                    if (normalized_keyword in seen_topic or seen_topic in normalized_keyword):
                        # If current has higher score and is more comprehensive, replace
                        if len(normalized_keyword) > len(seen_topic):
                            seen_topics.remove(seen_topic)
                            # Remove the old entry from filtered_keywords
                            filtered_keywords = [(k, s) for k, s in filtered_keywords if k.lower().strip() != seen_topic]
                            break
                        else:
                            is_duplicate = True
                            break
                    
                    # Check for word overlap (if 70% words are common, consider duplicate)
                    words1 = set(normalized_keyword.split())
                    words2 = set(seen_topic.split())
                    if words1 and words2:
                        overlap = len(words1.intersection(words2)) / min(len(words1), len(words2))
                        if overlap > 0.7:
                            if score > dict(filtered_keywords).get(seen_topic, 0):
                                seen_topics.remove(seen_topic)
                                filtered_keywords = [(k, s) for k, s in filtered_keywords if k.lower().strip() != seen_topic]
                                break
                            else:
                                is_duplicate = True
                                break
                
                if not is_duplicate:
                    filtered_keywords.append((keyword_text, score))
                    seen_topics.add(normalized_keyword)
                
                # Stop when we have enough results
                if len(filtered_keywords) >= max_results:
                    break
                    
            except Exception as keyword_error:
                print(f"Error processing keyword '{keyword}': {keyword_error}")
                continue
        
        # Sort by score in descending order
        filtered_keywords.sort(key=lambda x: x[1], reverse=True)
        
        return filtered_keywords

    def analyze_trending_content(self, contents, source_type='news'):
        """
        Comprehensive analysis of trending content
        """
        print(" Incoming contents:")
        print(contents)
        # Extract text content
        texts = []
        for content in contents:
            if 'title' in content and 'heading' in content:
                text = f"{content['title']} {content['heading']}"
            elif 'content' in content:
                text = content['content']
            else:
                continue
            texts.append(text)
        print(" Step 1 - Extracted Texts:")
        for t in texts:
            print(t)
        print(f" Number of extracted texts: {len(texts)}")
        print("\n")
        if not texts:
            print(" No texts extracted. Returning early.")
            return {}
        # Update word frequency cache
        self.update_word_frequency_cache(texts)
        print(" Step 2 - Word Frequency Cache Updated:")
        print(f"   Total unique words in cache: {len(self.word_freq_cache)}")
        if self.word_freq_cache:
            # Show top 10 most frequent words
            top_words = sorted(self.word_freq_cache.items(), key=lambda x: x[1], reverse=True)[:10]
            print("   Top 10 most frequent words:")
            for i, (word, freq) in enumerate(top_words, 1):
                print(f"     {i:2d}. {word:20s} - {freq:3d} times")
        print("\n")
        # Extract trending keywords with TF-IDF scores (sorted by importance)
        trending_keywords = self.extract_trending_keywords(texts, top_k=100)
        print(" Step 3 - Trending Keywords (TF-IDF sorted by importance):")
        print("Top 10 Keywords with highest TF-IDF scores:")
        for i, (keyword, score) in enumerate(trending_keywords[:10], 1):
            print(f"  {i:2d}. {keyword:30s} - Score: {score:.6f}")
        print(f"Total keywords extracted: {len(trending_keywords)}")
        print("\n")
        
        # Filter and deduplicate keywords for better quality
        trending_keywords = self.filter_and_deduplicate_keywords(trending_keywords, max_results=15)
        print(" Step 3.1 - Filtered & Deduplicated Keywords:")
        print("After filtering and deduplication:")
        for i, (keyword, score) in enumerate(trending_keywords[:10], 1):
            print(f"  {i:2d}. {keyword:30s} - Score: {score:.6f}")
        print(f"Final filtered keywords count: {len(trending_keywords)}")
        print("\n")
        # Prepare trending keywords (list of tuples) as a prompt for LLM
        llm_prompt = "ট্রেন্ডিং বাংলা শব্দ/বাক্যাংশ ও স্কোর (শব্দ:স্কোর):\n" + "\n".join(f"{i+1}. {kw}: {score:.4f}" for i, (kw, score) in enumerate(trending_keywords))
        # Example: Call your LLM here (replace with your actual LLM call)
        # llm_response = call_groq_llm(llm_prompt)
        # print(" LLM Response:")
        # print(llm_response)
        # Extract named entities
        all_entities = {'persons': [], 'places': [], 'organizations': [], 'dates': []}
        for text in texts:
            entities = self.extract_named_entities(text)
            for entity_type in all_entities:
                all_entities[entity_type].extend(entities[entity_type])
        print(" Step 4 - Named Entities (raw):")
        print(all_entities)
        print("\n")
        # Remove duplicates and count frequencies
        for entity_type in all_entities:
            entity_counter = Counter(all_entities[entity_type])
            all_entities[entity_type] = entity_counter.most_common(20)
        print(" Step 5 - Named Entities (deduped, counted):")
        print(all_entities)
        print("\n")
        # Sentiment analysis
        sentiment_scores = []
        for text in texts:
            sentiment = self.calculate_text_sentiment(text)
            sentiment_scores.append(sentiment)
        print(" Step 6 - Sentiment Scores:")
        print(sentiment_scores)
        print("\n")
        # Average sentiment
        avg_sentiment = {
            'positive': np.mean([s['positive'] for s in sentiment_scores]),
            'negative': np.mean([s['negative'] for s in sentiment_scores]),
            'neutral': np.mean([s['neutral'] for s in sentiment_scores])
        }
        print(" Step 7 - Average Sentiment:")
        print(avg_sentiment)
        print("\n")
        # Cluster similar phrases
        phrases = [kw[0] for kw in trending_keywords[:50]]
        if not phrases:
            clustered_phrases = {}
        else:
            clustered_phrases = self.cluster_similar_phrases(phrases, n_clusters=8)
        print(" Step 8 - Clustered Phrases:")
        print(clustered_phrases)
        print("\n")
        # Filter and deduplicate trending keywords for better quality
        filtered_trending_keywords = self.filter_and_deduplicate_keywords(trending_keywords, max_results=15)
        print(" Step 9 - Filtered and Deduplicated Trending Keywords:")
        for i, (keyword, score) in enumerate(filtered_trending_keywords, 1):
            print(f"  {i:2d}. {keyword:30s} - Score: {score:.6f}")
        print(f"Total filtered keywords: {len(filtered_trending_keywords)}")
        print("\n")
        return {
            'trending_keywords': trending_keywords,
            'named_entities': all_entities,
            'sentiment_analysis': avg_sentiment,
            'phrase_clusters': clustered_phrases,
            'content_statistics': {
                'total_texts': len(texts),
                'total_words': sum(len(self.advanced_tokenize(text)) for text in texts),
                'unique_words': len(set(word for text in texts for word in self.advanced_tokenize(text))),
                'source_type': source_type
            }
        }
    
    def save_models(self):
        """Save all models for future use"""
        self.processor.save_word_frequency_model()


def test_bengali_analyzer():
    """Test the Bengali analyzer with sample text"""
    analyzer = TrendingBengaliAnalyzer()
    
    sample_contents = [
        {
            'title': 'বাংলাদেশের অর্থনীতি ভালো অবস্থায়',
            'heading': 'দেশের অর্থনৈতিক অবস্থা উন্নতির দিকে এগিয়ে চলেছে। মানুষের আয় বৃদ্ধি পাচ্ছে।'
        },
        {
            'title': 'শিক্ষা ক্ষেত্রে নতুন পরিকল্পনা',
            'heading': 'সরকার শিক্ষা ক্ষেত্রে আধুনিকায়নের জন্য নতুন পরিকল্পনা গ্রহণ করেছে।'
        }
    ]
    
    result = analyzer.analyze_trending_content(sample_contents, 'news')
    
    print("Trending Keywords:")
    for keyword, score in result['trending_keywords'][:10]:
        print(f"  {keyword}: {score:.4f}")
    
    print("\nNamed Entities:")
    for entity_type, entities in result['named_entities'].items():
        if entities:
            print(f"  {entity_type}: {entities[:5]}")
    
    print(f"\nSentiment: {result['sentiment_analysis']}")
    print(f"\nStatistics: {result['content_statistics']}")


if __name__ == "__main__":
    test_bengali_analyzer()


# Add TrendingBengaliAnalyzer class for compatibility
class TrendingBengaliAnalyzer:
    """
    Wrapper class for advanced Bengali text analysis
    Provides trending analysis capabilities for Bengali content
    """
    
    def __init__(self):
        self.processor = AdvancedBengaliProcessor()
    
    def analyze_trending_content(self, contents: List[Dict], source_type: str = 'news') -> Dict:
        """
        Analyze trending content and return comprehensive analysis results
        
        Args:
            contents: List of content dictionaries with 'title', 'heading', 'source' fields
            source_type: Type of source ('news', 'social_media', 'mixed')
        
        Returns:
            Dictionary containing trending analysis results
        """
        # Extract texts from content
        texts = []
        for content in contents:
            text_parts = []
            if content.get('title'):
                text_parts.append(content['title'])
            if content.get('heading'):
                text_parts.append(content['heading'])
            if text_parts:
                texts.append(' '.join(text_parts))
        
        if not texts:
            return {
                'trending_keywords': [],
                'named_entities': {'persons': [], 'places': [], 'organizations': [], 'dates': []},
                'sentiment_analysis': {'positive': 0, 'negative': 0, 'neutral': 1},
                'phrase_clusters': {},
                'content_statistics': {'total_texts': 0, 'total_words': 0, 'unique_words': 0, 'source_type': source_type}
            }
        
        # Extract trending keywords
        trending_keywords = self.processor.extract_trending_keywords(texts, top_k=50)
        
        # Filter and deduplicate keywords
        trending_keywords = self.filter_and_deduplicate_keywords(trending_keywords, max_results=15)
        
        # Extract named entities
        all_entities = {'persons': [], 'places': [], 'organizations': [], 'dates': []}
        for text in texts:
            entities = self.processor.extract_named_entities(text)
            for entity_type in all_entities:
                all_entities[entity_type].extend(entities[entity_type])
        
        # Remove duplicates from entities
        for entity_type in all_entities:
            all_entities[entity_type] = list(set(all_entities[entity_type]))
        
        # Calculate sentiment
        sentiment_scores = []
        for text in texts:
            sentiment = self.processor.calculate_text_sentiment(text)
            sentiment_scores.append(sentiment)
        
        avg_sentiment = {
            'positive': np.mean([s['positive'] for s in sentiment_scores]),
            'negative': np.mean([s['negative'] for s in sentiment_scores]),
            'neutral': np.mean([s['neutral'] for s in sentiment_scores])
        }
        
        # Cluster phrases
        phrases = [kw[0] for kw in trending_keywords[:20]]
        clustered_phrases = {}
        if phrases:
            try:
                clustered_phrases = self.processor.cluster_similar_phrases(phrases, n_clusters=min(5, len(phrases)))
            except Exception as e:
                print(f"Error clustering phrases: {e}")
                clustered_phrases = {}
        
        return {
            'trending_keywords': trending_keywords,
            'named_entities': all_entities,
            'sentiment_analysis': avg_sentiment,
            'phrase_clusters': clustered_phrases,
            'content_statistics': {
                'total_texts': len(texts),
                'total_words': sum(len(self.processor.advanced_tokenize(text)) for text in texts),
                'unique_words': len(set(word for text in texts for word in self.processor.advanced_tokenize(text))),
                'source_type': source_type
            }
        }
    
    def filter_and_deduplicate_keywords(self, trending_keywords, max_results=15):
        """Filter and deduplicate trending keywords for better quality"""
        if not trending_keywords:
            return []
        
        # Person name patterns to exclude
        person_indicators = [
            'মাননীয়', 'জনাব', 'মিসেস', 'মিস', 'ডঃ', 'প্রফেসর', 'শেখ', 'মোঃ', 'সৈয়দ',
            'সাহেব', 'সাহেবা', 'বেগম', 'খান', 'চৌধুরী', 'আহমেদ', 'হোসেন', 'উদ্দিন', 'রহমান'
        ]
        
        # Low-quality phrase patterns to exclude
        exclude_patterns = [
            r'বলেছেন যে',
            r'নিশ্চিত করেছে যে',
            r'জানিয়েছেন যে',
            r'সরকার.*যে',
            r'প্রধানমন্ত্রী.*যে',
            r'মন্ত্রী.*যে',
            r'.{30,}',  # Very long phrases (30+ characters)
        ]
        
        filtered_keywords = []
        seen_topics = set()
        
        for keyword, score in trending_keywords:
            keyword_text = keyword.strip()
            
            # Skip if empty or too short
            if len(keyword_text) < 2:
                continue
            
            # Skip if contains person indicators
            if any(indicator in keyword_text for indicator in person_indicators):
                continue
            
            # Skip if matches exclude patterns
            if any(re.search(pattern, keyword_text) for pattern in exclude_patterns):
                continue
            
            # Skip common stop words that might slip through
            if keyword_text in ['করা', 'হওয়া', 'দেওয়া', 'নেওয়া', 'বলা', 'আসা', 'যাওয়া']:
                continue
            
            # Deduplicate similar topics
            is_duplicate = False
            normalized_keyword = keyword_text.lower().strip()
            
            for seen_topic in seen_topics:
                # Check for substring relationship
                if (normalized_keyword in seen_topic or seen_topic in normalized_keyword):
                    # If current has higher score and is more comprehensive, replace
                    if len(normalized_keyword) > len(seen_topic):
                        seen_topics.remove(seen_topic)
                        filtered_keywords = [(k, s) for k, s in filtered_keywords if k.lower().strip() != seen_topic]
                        break
                    else:
                        is_duplicate = True
                        break
                
                # Check for word overlap
                words1 = set(normalized_keyword.split())
                words2 = set(seen_topic.split())
                if words1 and words2:
                    overlap = len(words1.intersection(words2)) / min(len(words1), len(words2))
                    if overlap > 0.7:
                        if score > dict(filtered_keywords).get(seen_topic, 0):
                            seen_topics.remove(seen_topic)
                            filtered_keywords = [(k, s) for k, s in filtered_keywords if k.lower().strip() != seen_topic]
                            break
                        else:
                            is_duplicate = True
                            break
            
            if not is_duplicate:
                filtered_keywords.append((keyword_text, score))
                seen_topics.add(normalized_keyword)
            
            if len(filtered_keywords) >= max_results:
                break
        
        # Sort by score in descending order
        filtered_keywords.sort(key=lambda x: x[1], reverse=True)
        
        return filtered_keywords
