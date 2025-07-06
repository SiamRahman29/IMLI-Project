import re
from typing import List
# from pytrends.request import TrendReq
from googleapiclient.discovery import build
import os
import pandas as pd
from app.services.stopwords import STOP_WORDS
import requests

def remove_stop_words(tokens: List[str]) -> List[str]:
    return [word for word in tokens if word not in STOP_WORDS]

def remove_special_characters(text: str) -> str:
    # Remove anything that's not a Bangla/English letter or number
    return re.sub(r'[^\u0980-\u09FFa-zA-Z0-9\s]', '', text)

def simple_stem(word: str) -> str:
    # Placeholder for Bangla stemming (can be replaced with a real stemmer)
    # For now, just return the word as is
    return word

def stem_words(tokens: List[str]) -> List[str]:
    return [simple_stem(word) for word in tokens]

def preprocess_text(text: str) -> List[str]:
    text = remove_special_characters(text)
    tokens = text.split()
    tokens = remove_stop_words(tokens)
    tokens = stem_words(tokens)
    return tokens

def get_google_trends_bangladesh():
    """Fetch trending searches for Bangladesh using Google Trends API and preprocess them."""
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        trends = []
        try:
            trending_searches = pytrends.trending_searches(pn='bangladesh')
            trends = trending_searches.iloc[:, 0].tolist()
            # print(f"[pytrends] trending_searches (bangladesh): {trends}")
            if not trends or (isinstance(trends, float) and pd.isna(trends[0])):
                raise Exception('No trends found')
        except Exception as e:
            # print(f"[pytrends] trending_searches failed: {e}")
            try:
                realtime = pytrends.realtime_trending_searches(pn='BD')
                if isinstance(realtime, pd.DataFrame) and 'title' in realtime.columns:
                    trends = realtime['title'].tolist()
                    # print(f"[pytrends] realtime_trending_searches (BD): {trends}")
                else:
                    print("[pytrends] realtime_trending_searches returned no 'title' column")
                    trends = []
            except Exception as e2:
                # print(f"[pytrends] realtime_trending_searches failed: {e2}")
                # Fallback: use related_queries for a generic term
                try:
                    pytrends.build_payload(["বাংলাদেশ"], cat=0, timeframe='now 7-d', geo='BD', gprop='')
                    related = pytrends.related_queries()
                    # print(f"[pytrends] related_queries: {related}")
                    if related:
                        for v in related.values():
                            if v and v.get('top') is not None:
                                trends.extend(v['top']['query'].tolist())
                    if not trends:
                        # As a last fallback, use suggestions
                        suggestions = pytrends.suggestions(keyword="বাংলাদেশ")
                        # print(f"[pytrends] suggestions: {suggestions}")
                        trends = [s['title'] for s in suggestions if 'title' in s]
                except Exception as e3:
                    # print(f"[pytrends] related_queries/suggestions failed: {e3}")
                    trends = []
        processed = [preprocess_text(t) for t in trends if t]
        # print(f"[pytrends] Processed Google Trends: {processed}")
        return processed
    except Exception as e:
        # print(f"Error fetching Google Trends: {e}")
        return []

def get_youtube_trending_bangladesh():
    """Fetch trending YouTube video titles for Bangladesh and preprocess them."""
    try:
        api_key = os.environ.get('YOUTUBE_API_KEY')
        if not api_key:
            raise ValueError('YOUTUBE_API_KEY not set in environment.')
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.videos().list(
            part='snippet',
            chart='mostPopular',
            regionCode='BD',
            maxResults=20
        )
        response = request.execute()
        titles = [item['snippet']['title'] for item in response.get('items', [])]
        processed = [preprocess_text(t) for t in titles]
        return processed
    except Exception as e:
        print(f"Error fetching YouTube trending videos: {e}")
        return []

def get_serpapi_trending_bangladesh():
    """Fetch trending topics/phrases for Bangladesh using SerpApi Google Search."""
    api_key = os.environ.get('SERPAPI_API_KEY')
    if not api_key:
        # print('[SerpApi] SERPAPI_API_KEY not set in environment.')
        return []
    url = 'https://serpapi.com/search.json'
    params = {
        'engine': 'google',
        'q': 'বাংলাদেশ trending',
        'hl': 'bn',
        'gl': 'bd',
        'google_domain': 'google.com',
        'num': '10',
        # 'api_key': api_key
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        # print(f"[SerpApi] Raw response: {data}")
        trends = []
        # if 'organic_results' in data:
        #     for item in data['organic_results']:
        #         # Try to extract title and snippet
        #         if 'title' in item:
        #             trends.append(item['title'])
        #         if 'snippet' in item:
        #             trends.append(item['snippet'])
        # else:
        #     print('[SerpApi] No organic_results in response.')
        processed = [preprocess_text(t) for t in trends if t]
        # print(f"[SerpApi] Processed SerpApi Trends: {processed}")
        return processed
    except Exception as e:
        # print(f"[SerpApi] Error fetching SerpApi trends: {e}")
        return []

# Placeholder for Twitter trending hashtags

def get_twitter_trending_bangladesh():
    # TODO: Implement Twitter API integration
    return []

# Placeholder for Facebook Insights API

def get_facebook_trending_bangladesh():
    # TODO: Implement Facebook Insights API integration
    return []
