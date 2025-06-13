import re
from typing import List
from pytrends.request import TrendReq
from googleapiclient.discovery import build
import os
import pandas as pd
from app.services.stopwords import STOP_WORDS

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
        # Try trending_searches for Bangladesh (may not always be available)
        try:
            trending_searches = pytrends.trending_searches(pn='bangladesh')
            # trending_searches is a DataFrame, get the first column as list
            trends = trending_searches.iloc[:, 0].tolist()
            if not trends or (isinstance(trends, float) and pd.isna(trends[0])):
                raise Exception('No trends found')
        except Exception:
            # Fallback to realtime trending if trending_searches fails or is empty
            realtime = pytrends.realtime_trending_searches(pn='BD')
            if 'title' in realtime:
                trends = realtime['title'].tolist()
            else:
                trends = []
        processed = [preprocess_text(t) for t in trends if t]
        return processed
    except Exception as e:
        print(f"Error fetching Google Trends: {e}")
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

# Placeholder for Twitter trending hashtags

def get_twitter_trending_bangladesh():
    # TODO: Implement Twitter API integration
    return []

# Placeholder for Facebook Insights API

def get_facebook_trending_bangladesh():
    # TODO: Implement Facebook Insights API integration
    return []
