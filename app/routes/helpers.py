import os
import re
import requests
from requests.exceptions import Timeout, ConnectionError
from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple
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
from sqlalchemy.orm import Session
from app.models.word import Article, TrendingPhrase
from app.services.social_media_scraper import scrape_social_media_content
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

BENGALI_STOP_WORDS = {
    'এবং', 'বা', 'কিন্তু', 'তবে', 'যদি', 'তাহলে', 'কেননা', 'যেহেতু', 'অতএব', 'সুতরাং',
    'এর', 'তার', 'তাদের', 'আমার', 'আমাদের', 'তোমার', 'তোমাদের', 'তিনি', 'তারা', 'আমি', 'আমরা',
    'তুমি', 'তোমরা', 'সে', 'এই', 'এটি', 'ওই', 'ওটি', 'যে', 'যেটি', 'কী', 'কি', 'কেন', 'কোথায়',
    'কখন', 'কীভাবে', 'কোন', 'কত', 'কতটা', 'হয়', 'হয়েছে', 'হবে', 'হচ্ছে', 'থাকা', 'থাকে', 'থাকবে',
    'আছে', 'ছিল', 'থেকে', 'পর্যন্ত', 'দিয়ে', 'করে', 'জন্য', 'সাথে', 'মধ্যে', 'ভিতরে', 'বাইরে',
    'উপর', 'নিচে', 'আগে', 'পরে', 'সময়', 'দিন', 'রাত', 'সকাল', 'বিকাল', 'সন্ধ্যা', 'এখন', 'তখন',
    'একটি', 'একটা', 'দুটি', 'দুটো', 'তিনটি', 'তিনটে', 'চারটি', 'চারটে', 'পাঁচটি', 'পাঁচটে',
    'না', 'নেই', 'নয়', 'নি', 'অন্য', 'আরও', 'আরো', 'অনেক', 'সব', 'সকল', 'প্রতি', 'খুব', 'বেশ',
    'ভাল', 'ভালো', 'মন্দ', 'ভাল', 'মানুষ', 'লোক', 'জন', 'গুলি', 'গুলো', 'টি', 'টা', 'খানা', 'খানি',
    'টুকু', 'মত', 'মতো', 'মতন', 'হিসেবে', 'হিসেবে', 'রূপে', 'হিসেবে', 'বলে', 'বলা', 'বলেন', 'বলেছেন',
    'বলছেন', 'বলবেন', 'বর', 'বরং', 'মাঝে', 'মাঝেমাঝে', 'কখনো', 'কখনও', 'সর্বদা', 'সবসময়', 'প্রায়',
    'প্রায়ই', 'কখনো', 'কদাচিৎ', 'মোটেও', 'মোটেই', 'একেবারে', 'একদম', 'পুরোপুরি', 'সম্পূর্ণ', 'সম্পূর্ণভাবে',
    'হয়তো', 'হয়ত', 'অবশ্যই', 'অবশ্য', 'নিশ্চয়', 'নিশ্চিত', 'সম্ভবত', 'হয়নি', 'নয়', 'না', 'কোনো',
    'কোন', 'কেউ', 'কেউই', 'কিছু', 'কিছুই', 'কোথাও', 'কোথাওই', 'কখনো', 'কখনোই', 'যখন', 'তখনই',
    'যেখানে', 'সেখানে', 'যেভাবে', 'সেভাবে', 'যতটা', 'ততটা', 'যতক্ষণ', 'ততক্ষণ', 'প্রথম', 'দ্বিতীয়',
    'তৃতীয়', 'চতুর্থ', 'পঞ্চম', 'ষষ্ঠ', 'সপ্তম', 'অষ্টম', 'নবম', 'দশম', 'একে', 'তাকে', 'তাদেরকে',
    'আমাকে', 'আমাদেরকে', 'তোমাকে', 'তোমাদেরকে', 'এটাকে', 'ওটাকে', 'যাকে', 'কাকে', 'ঐ', 'ওই',
    'এই', 'সেই', 'যে', 'যেই', 'কোন', 'কোনো', 'একজন', 'দুজন', 'তিনজন', 'চারজন', 'পাঁচজন',
    'নতুন', 'পুরাতন', 'পুরোনো', 'বড়', 'ছোট', 'ভালো', 'খারাপ', 'সুন্দর', 'কুৎসিত', 'উচ্চ', 'নিম্ন',
    'অই', 'অগত্যা','বাংলাদেশ', 'টাকা','শতাংশ','পানি', 'অত: পর', 'অতএব', 'অথচ', 'অথবা', 'অধিক', 'অধীনে', 'অধ্যায়', 'অনুগ্রহ',
    'অনুভূত', 'অনুযায়ী','ঋণ', 'অনুরূপ', 'অনুসন্ধান', 'অনুসরণ', 'অনুসারে', 'অনুসৃত', 'অনেক', 'অনেকে',
    'অনেকেই', 'অন্তত', 'অন্য', 'অন্যত্র', 'অন্যান্য', 'অপেক্ষাকৃতভাবে', 'অবধি', 'অবশ্য', 'অবশ্যই',
    'অবস্থা', 'অবিলম্বে', 'অভ্যন্তরস্থ', 'অর্জিত', 'অর্থাত', 'অসদৃশ', 'অসম্ভাব্য', 'আইন', 'আউট',
    'আক্রান্ত', 'আগামী', 'আগে', 'আগেই', 'আগ্রহী', 'আছে', 'আজ', 'আট', 'আদেশ', 'আদ্যভাগে', 'আন্দাজ',
    'আপনার', 'আপনি', 'আবার', 'আমরা', 'আমাকে', 'আমাদিগের', 'আমাদের', 'আমার', 'আমি', 'আর', 'আরও',
    'আশি', 'আশু', 'আসা', 'আসে', 'ই','বিএনপি', 'ইচ্ছা', 'ইচ্ছাপূর্বক', 'ইতিমধ্যে', 'ইতোমধ্যে', 'ইত্যাদি',
    'ইশারা', 'ইহা', 'ইহাতে', 'উক্তি', 'উচিত', 'উচ্চ', 'উঠা', 'উত্তম', 'উত্তর', 'উনি', 'উপর',
    'উপরে', 'উপলব্ধ', 'উপায়', 'উভয়', 'উল্লেখ', 'উল্লেখযোগ্যভাবে', 'উহার', 'ঊর্ধ্বতন', 'এ', 'এপর্যন্ত',
    'এঁদের', 'এঁরা', 'এই', 'এইগুলো', 'এইভাবে', 'এক', 'একই', 'একটি', 'একদা', 'একবার', 'একভাবে',
    'একরকম', 'একসঙ্গে', 'একা', 'একে', 'এক্', 'এখন', 'এখনও', 'এখনো', 'এখানে', 'এখানেই', 'এছাড়াও',
    'এটা', 'এটাই', 'এটি', 'এত', 'এতটাই', 'এতদ্বারা', 'এতে', 'এদিকে', 'এদের', 'এপর্যন্ত', 'এবং',
    'এবার', 'এমন', 'এমনকি', 'এমনকী', 'এমনি', 'এর', 'এরকম', 'এরা', 'এল', 'এলাকায়', 'এলাকার', 'এস',
    'এসে', 'ঐ', 'ও', 'ওঁদের', 'ওঁর', 'ওঁরা', 'ওই', 'ওকে', 'ওখানে', 'ওদের', 'ওর', 'ওরা', 'ওহে',
    'কক্ষ', 'কখন', 'কখনও', 'কত', 'কবে', 'কম', 'কমনে', 'কয়েক', 'কয়েকটি', 'করছে', 'করছেন', 'করতে',
    'করবে', 'করবেন', 'করলে', 'করলেন', 'করলো', 'করা', 'করাই', 'করাত', 'করার', 'করায়', 'করি',
    'করিতে', 'করিয়া', 'করিয়ে', 'করে', 'করেই', 'করেছিল', 'করেছিলেন', 'করেছে', 'করেছেন', 'করেন',
    'কর্তব্য', 'কাউকে', 'কাছ', 'কাছাকাছি', 'কাছে', 'কাজ', 'কাজে', 'কারও', 'কারণ', 'কারণসমূহ', 'কারো',
    'কি', 'কিংবা', 'কিছু', 'কিছুই', 'কিছুটা', 'কিছুনা', 'কিনা', 'কিন্তু', 'কিভাবে', 'কী', 'কূপ', 'কে',
    'কেউ', 'কেউই', 'কেউনা', 'কেখা', 'কেন', 'কেবল', 'কেবা', 'কেস', 'কেহ', 'কোটি', 'কোথা', 'কোথাও',
    'কোথায়', 'কোন', 'কোনও', 'কোনো', 'ক্রম', 'ক্ষেত্রে', 'কয়েক', 'কয়েকটি', 'খুঁজছেন', 'খুব',
    'খোলা', 'খোলে', 'গড়', 'গত', 'গিয়ে', 'গিয়েছিলাম', 'গিয়েছে', 'গিয়ে', 'গিয়েছে', 'গুরুত্ব', 'গুলি',
    'গেছে', 'গেল', 'গেলে', 'গোটা', 'গোষ্ঠীবদ্ধ', 'গ্রহণ', 'গ্রুপ', 'ঘর', 'ঘোষণা', 'চলে', 'চান', 'চায়',
    'চার', 'চালা', 'চালান', 'চালু', 'চায়', 'চেয়ে', 'চেয়েছিলেন', 'চেষ্টা', 'চেয়ে', 'ছয়', 'ছাড়া',
    'ছাড়াছাড়ি', 'ছাড়া', 'ছাড়াও', 'ছিল', 'ছিলেন', 'ছোট', 'জন', 'জনকে', 'জনাব', 'জনাবা', 'জনের',
    'জন্য', 'জানতাম', 'জানতে', 'জানা', 'জানানো', 'জানায়', 'জানিয়ে', 'জানিয়েছে', 'জানে', 'জায়গা',
    'জিজ্ঞাসা', 'জিজ্ঞেস', 'জিনিস', 'জে', 'জ্নজন', 'টা', 'টি', 'ঠিক', 'ঠিকআছে', 'ডগা', 'তখন', 'তত',
    'তত্কারণে', 'তত্প্রতি', 'তথা', 'তদনুসারে', 'তদ্ব্যতীত', 'তন্নতন্ন', 'তবু', 'তবে', 'তরুণ', 'তা',
    'তাঁকে', 'তাঁদের', 'তাঁর', 'তাঁরা', 'তাঁহারা', 'তাই', 'তাও', 'তাকে', 'তাতে', 'তাদের', 'তার', 'তারপর',
    'তারপরেও', 'তারা', 'তারিখ', 'তারৈ', 'তাহলে', 'তাহা', 'তাহাতে', 'তাহাদিগকে', 'তাহাদেরই', 'তাহার',
    'তিন', 'তিনি', 'তিনিও', 'তীক্ষ্ন', 'তুমি', 'তুলে', 'তেমন', 'তৈরীর', 'তো', 'তোমার', 'তোলে', 'থাকবে',
    'থাকবেন', 'থাকা', 'থাকায়', 'থাকায়', 'থাকে', 'থাকেন', 'থেকে', 'থেকেই', 'থেকেও', 'দরকারী', 'দলবদ্ধ',
    'দান', 'দিকে', 'দিতে', 'দিন', 'দিয়ে', 'দিয়েছে', 'দিয়েছেন', 'দিলেন', 'দিয়ে', 'দিয়েছে', 'দিয়েছেন',
    'দু', 'দুই', 'দুটি', 'দুটো', 'দূরে', 'দেওয়ার', 'দেওয়া', 'দেওয়ার', 'দেখতে', 'দেখা', 'দেখাচ্ছে',
    'দেখিয়েছেন', 'দেখে', 'দেখেন', 'দেন', 'দেয়', 'দেয়', 'দ্বারা', 'দ্বিগুণ', 'দ্বিতীয়', 'দ্য', 'ধরা',
    'ধরে', 'ধামার', 'নতুন', 'নব্বই', 'নয়', 'নাই', 'নাকি', 'নাগাদ', 'নানা', 'নাম', 'নিচে', 'নিছক',
    'নিজে', 'নিজেই', 'নিজেকে', 'নিজেদের', 'নিজেদেরকে', 'নিজের', 'নিতে', 'নিদিষ্ট', 'নিম্নাভিমুখে',
    'নিয়ে', 'নির্দিষ্ট', 'নির্বিশেষে', 'নিশ্চিত', 'নিয়ে', 'নেই', 'নেওয়ার', 'নেওয়া', 'নেয়ার', 'নয়',
    'পক্ষই', 'পক্ষে', 'পঞ্চম', 'পড়া', 'পণ্য', 'পথ', 'পয়েন্ট', 'পর', 'পরন্তু', 'পরবর্তী', 'পরিণত',
    'পরিবর্তে', 'পরে', 'পরেই', 'পরেও', 'পর্যন্ত', 'পর্যাপ্ত', 'পাঁচ', 'পাওয়া', 'পাচ', 'পায়', 'পারা',
    'পারি', 'পারিনি', 'পারে', 'পারেন', 'পালা', 'পাশ', 'পাশে', 'পিছনে', 'পিঠের', 'পুরোনো', 'পুরোপুরি',
    'পূর্বে', 'পৃষ্ঠা', 'পৃষ্ঠাগুলি', 'পেছনে', 'পেয়েছেন', 'পেয়ে', 'পেয়্র্', 'প্রকৃতপক্ষে', 'প্রণীত', 'প্রতি',
    'প্রথম', 'প্রদত্ত', 'প্রদর্শনী', 'প্রদর্শিত', 'প্রধানত', 'প্রবলভাবে', 'প্রভৃতি', 'প্রমাণীকরণ', 'প্রযন্ত',
    'প্রয়োজন', 'প্রয়োজনীয়', 'প্রসূত', 'প্রাক্তন', 'প্রাথমিক', 'প্রাথমিকভাবে', 'প্রান্ত', 'প্রাপ্ত',
    'প্রায়', 'প্রায়ই', 'প্রায়', 'ফলাফল','লাখ','জুন','টাকা','ফলে', 'ফিক্স', 'ফিরে', 'ফের', 'বক্তব্য', 'বছর', 'বড়', 'বদলে',
    'বন', 'বন্ধ', 'বরং', 'বরাবর', 'বর্ণন', 'বর্তমান', 'বলতে', 'বলল', 'বললেন', 'বলা', 'বলে', 'বলেছেন',
    'বলেন', 'বসে', 'বহু', 'কর','বা', 'বাঁক','বিএনপি', 'বাইরে', 'বাকি', 'বাড়ি', 'বাতিক', 'বাদ', 'বাদে', 'বার', 'বাহিরে',
    'বিনা', 'বিন্দু', 'বিভিন্ন', 'বিশেষ', 'বিশেষণ', 'বিশেষত', 'বিশেষভাবে', 'বিশ্ব', 'বিষয়টি', 'বুঝিয়ে',
    'বৃহত্তর', 'বের', 'বেশ', 'বেশি', 'বেশী', 'ব্যতীত', 'ব্যবহার', 'ব্যবহারসমূহ', 'ব্যবহৃত', 'ব্যাক',
    'ব্যাপকভাবে', 'ব্যাপারে', 'ভবিষ্যতে', 'ভান', 'ভাবে', 'ভাবেই', 'ভাল', 'ভিতরে', 'ভিন্ন', 'ভিন্নভাবে',
    'মত', 'মতো', 'মতোই', 'মধ্যভাগে', 'মধ্যে', 'মধ্যেই', 'মধ্যেও', 'মনে', 'মনে হয়', 'মস্ত', 'মহান',
    'মাত্র', 'মাধ্যম', 'মাধ্যমে', 'মান', 'মানানসই', 'মানুষ', 'মানে', 'মামলা', 'মিলিয়ন', 'মুখ', 'মূলত',
    'মোট', 'মোটেই', 'যখন', 'যখনই', 'যত', 'যতটা', 'যথা', 'যথাক্রমে', 'যথেষ্ট', 'যদি', 'যদিও', 'যন্ত্রাংশ',
    'যা', 'যাঁর', 'যাঁরা', 'যাই', 'যাওয়া', 'যাওয়ার', 'যাওয়া', 'যাওয়ার', 'যাকে', 'যাচ্ছে', 'যাতে', 'যাদের',
    'যান', 'যাবে', 'যায়', 'যার', 'যারা', 'যাহার', 'যাহোক', 'যিনি', 'যে', 'যেখানে', 'যেখানেই', 'যেটি',
    'যেতে', 'যেন', 'যেমন', 'যেহেতু', 'যোগ', 'রকম', 'রয়েছে', 'রাখা', 'রাখে', 'রাজী', 'রাজ্যের', 'রেখে',
    'রয়েছে', 'লক্ষ', 'লাইন', 'লাল', 'শত', 'শব্দ', 'শীঘ্র', 'শীঘ্রই', 'শুধু', 'শুরু', 'শুরুতে', 'শূন্য',
    'শেষ', 'সংক্রান্ত', 'সংক্ষিপ্ত', 'সংক্ষেপে', 'সংখ্যা', 'সংখ্যার', 'সংশ্লিষ্ট', 'সক্ষম', 'সঙ্গে',
    'সঙ্গেও', 'সত্য', 'সত্যিই', 'সদয়', 'সদস্য', 'সদস্যদের', 'সফলভাবে', 'সব', 'সবচেয়ে', 'সবাই', 'সবার',
    'সময়', 'সমস্ত', 'সমান', 'সম্পন্ন', 'সম্প্রতি', 'সম্ভব', 'সম্ভবত', 'সম্ভাব্য', 'সরাইয়া', 'সর্বত্র',
    'সর্বদা', 'সর্বস্বান্ত', 'সহ', 'সহিত', 'সাত', 'সাধারণ', 'সাধারণত', 'সাব', 'সাবেক', 'সামগ্রিক', 'সামনে',
    'সামান্য', 'সাম্প্রতিক', 'সুতরাং', 'সুত্র', 'সূচক', 'সে', 'সে হবে', 'সেই', 'সেকেন্ড', 'সেখান', 'সেখানে',
    'সেগুলো', 'সেটা', 'সেটাই', 'সেটাও', 'সেটি', 'সেরা', 'স্টপ', 'স্থাপিত', 'স্পষ্ট', 'স্পষ্টত', 'স্পষ্টতই',
    'স্ব', 'স্বয়ং', 'স্বাগত', 'স্বাভাবিকভাবে', 'স্বার্থ', 'স্বয়ং', 'হইতে', 'হইবে', 'হইয়া', 'হওয়া', 'হওয়ায়',
    'হওয়ার', 'হচ্ছে', 'হত', 'হতে', 'হতেই', 'হন', 'হবে', 'হবেন', 'হয়', 'হয়তো', 'হয়নি', 'হয়ে', 'হয়েই',
    'হয়েছিল', 'হয়েছে', 'হয়েছেন', 'হল', 'হলে', 'হলেই', 'হলেও', 'হলো', 'হাজার', 'হায়', 'হারানো',
    'হিসাবে', 'হৈলে', 'হোক', 'হয়', 'হয়তো', 'হয়নি', 'হয়ে', 'হয়েই', 'হয়েছিল', 'হয়েছে', 'হয়েছেন', 'অংশ'
}


class BengaliTextProcessor:
    def __init__(self):
        self.stop_words = BENGALI_STOP_WORDS
        
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
        # Bengali sentence endings
        sentences = re.split(r'[।!?]', text)
        return [sent.strip() for sent in sentences if sent.strip()]
    
    def tokenize_words(self, text: str) -> List[str]:
        """Tokenize text into words"""
        words = re.findall(r'\b[\u0980-\u09FF]+\b', text)
        return [word for word in words if len(word) > 1]  # Filter single characters
    
    def remove_stop_words(self, words: List[str]) -> List[str]:
        """Remove Bengali stop words"""
        return [word for word in words if word not in self.stop_words]
    
    def generate_ngrams(self, words: List[str], n: int) -> List[str]:
        """Generate n-grams from word list"""
        if len(words) < n:
            return []
        return [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]

class TrendingAnalyzer:
    def __init__(self):
        self.text_processor = BengaliTextProcessor()
        
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
    
    # Fetch social media content
    print("Fetching social media content...")
    try:
        social_media_posts = scrape_social_media_content()
        print(f"Fetched {len(social_media_posts)} social media posts")
    except Exception as e:
        print(f"Error fetching social media content: {e}")
        social_media_posts = []
    
    # Combine all content
    all_content = news_articles + social_media_posts
    
    if not all_content:
        print("No content fetched, skipping analysis")
        return
    
    # Store articles and posts in database
    print("Storing content in the database...")
    store_news(db, news_articles)
    if social_media_posts:
        store_social_media_content(db, social_media_posts)
    
    # Analyze trending phrases for each source separately
    print("Analyzing trending phrases...")
    analyzer = TrendingAnalyzer()
    
    today = date.today()
    
    # Clear existing data for today
    db.query(TrendingPhrase).filter(TrendingPhrase.date == today).delete()
    
    # Analyze news content
    if news_articles:
        analyze_and_store_trends(db, analyzer, news_articles, 'news', today)
    
    # Analyze social media content  
    if social_media_posts:
        analyze_and_store_trends(db, analyzer, social_media_posts, 'social_media', today)
    
    db.commit()
    print("Comprehensive trending phrases analysis completed and stored!")

def analyze_and_store_trends(db: Session, analyzer: TrendingAnalyzer, 
                           content: List[Dict], source: str, target_date: date):
    """Analyze trends for a specific content source and store in database"""
    
    # Prepare text data
    texts = []
    for item in content:
        if source == 'news':
            combined_text = f"{item.get('title', '')} {item.get('description', '')}"
        else:  # social_media
            combined_text = item.get('content', '')
        texts.append(combined_text)
    
    if not texts:
        return
    
    # Calculate frequency scores
    frequency_scores = analyzer.calculate_frequency_scores(texts)
    
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
            articles.append({
                'title': entry.get('title', ''),
                'description': entry.get('summary', ''),
                'url': entry.get('link', ''),
                'published_date': datetime.now().date(),
                'source': 'prothom_alo'
            })
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
        for link in soup.select(".lead-news a, .lead-news-title a"):
            url = link.get('href')
            if not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            try:
                article_res = robust_request(url)
                if not article_res:
                    continue
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".news-details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
        for link in soup.select(".lead-news a, .main-news a, .news-title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p")])
                articles.append({
                    "title": title,
                    "description": body,
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
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p")])
                articles.append({
                    "title": title,
                    "description": body,
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
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p, .news-details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p, .news-details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p, .news-details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p, .news-details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p, .news-details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p, .news-details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p, .news-details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p, .news-details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p, .news-details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p, .news-details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p, .news-details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p, .news-details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p, .news-details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
        for link in soup.select(".lead-news a, .main-news a, .title a"):
            url = link.get('href')
            if url and not url.startswith('http'):
                url = homepage.rstrip('/') + '/' + url.lstrip('/')
            article_res = robust_request(url)
            if not article_res:
                continue
            try:
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                title = article_soup.select_one("h1").text.strip() if article_soup.select_one("h1") else ""
                body = " ".join([p.text for p in article_soup.select(".details-content p, .news-details p")])
                articles.append({
                    "title": title,
                    "description": body,
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
    articles.extend(scrape_prothom_alo())
    articles.extend(scrape_kaler_kantho())
    articles.extend(scrape_jugantor())
    articles.extend(scrape_ittefaq())
    articles.extend(scrape_bd_pratidin())
    articles.extend(scrape_manab_zamin())
    articles.extend(scrape_samakal())
    articles.extend(scrape_amader_shomoy())
    articles.extend(scrape_janakantha())
    articles.extend(scrape_inqilab())
    articles.extend(scrape_sangbad())
    articles.extend(scrape_noya_diganta())
    articles.extend(scrape_jai_jai_din())
    articles.extend(scrape_manobkantha())
    articles.extend(scrape_ajkaler_khobor())
    articles.extend(scrape_ajker_patrika())
    articles.extend(scrape_protidiner_sangbad())
    articles.extend(scrape_bangladesher_khabor())
    articles.extend(scrape_bangladesh_journal())
    return articles

def store_news(db: Session, articles: List[Dict]):
    """Store news articles in database"""
    for article_data in articles:
        article = Article(
            title=article_data.get('title', ''),
            description=article_data.get('description') or '',  # Ensure not None
            url=article_data.get('url', ''),
            published_date=article_data.get('published_date'),
            source=article_data.get('source', 'unknown')
        )
        db.add(article)
    
    db.commit()
    print(f"Stored {len(articles)} articles in database")

def fetch_social_media_posts():
    """Fetch social media posts from various Bengali platforms"""
    try:
        posts = scrape_social_media_content()
        print(f"Fetched {len(posts)} social media posts")
        return posts
    except Exception as e:
        print(f"Error fetching social media posts: {e}")
        return []

def parse_news(articles: List[Dict]) -> str:
    """Parse articles into combined text"""
    combined_texts = []
    for article in articles:
        title = article.get('title', '')
        description = article.get('description', '')
        combined_texts.append(f"{title}। {description}")
    
    return "\n".join(combined_texts)

def generate_trending_word_candidates(db: Session, limit: int = 10) -> str:
    """Generate trending word candidates using Groq AI, with pre-processing"""
    try:
        articles = fetch_news()
        if not articles:
            msg = "No articles available for analysis"
            print(msg)
            return msg

        # Pre-process: Clean, remove stopwords, NER, frequency, topic modeling
        from app.services.advanced_bengali_nlp import TrendingBengaliAnalyzer
        analyzer = TrendingBengaliAnalyzer()
        print(f"  Fetched articles (count={len(articles)}):")
        print("  Fetching content for every article URL.")
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=chrome_options)
        for idx, a in enumerate(articles, 1):
            if a.get('url'):
                try:
                    driver.get(a['url'])
                    paragraphs = driver.find_elements(By.TAG_NAME, 'p')
                    content = ' '.join([p.text for p in paragraphs if p.text.strip()])
                    a['description'] = content[:2000]  # Always overwrite for completeness
                    print(f"  Fetched content for article {idx} from {a['url']}")
                except Exception as e:
                    print(f"  Failed to fetch content for {a['url']}: {e}")
            print(f"[{idx}] Title: {a.get('title', '')}\n    Desc: {a.get('description', '')}\n    URL: {a.get('url', '')}\n    Date: {a.get('published_date', '')}\n    Source: {a.get('source', '')}\n")
        driver.quit()
        texts = [f"{a.get('title', '')}। {a.get('description', '')}" for a in articles]
        print(f"  Raw texts count: {len(texts)}")

        # Use analyzer's own methods for text processing
        cleaned_texts = [analyzer.processor.normalize_text(t) for t in texts]
        print(f"  Cleaned texts (first 2): {cleaned_texts[:2]}")

        tokenized = [analyzer.processor.advanced_tokenize(t) for t in cleaned_texts]
        # Remove stopwords using analyzer.processor.stop_words
        no_stopwords = [[w for w in words if w not in analyzer.processor.stop_words] for words in tokenized]
        print(f"  No stopwords (first 2): {no_stopwords[:2]}")
        # Print a sample for stopword removal verification
        if tokenized:
            print(f"[STOPWORDS] Before: {tokenized[0][:20]}")
            print(f"[STOPWORDS] After: {[w for w in tokenized[0] if w not in analyzer.processor.stop_words][:20]}")

        # Frequency count
        all_words = [w for words in no_stopwords for w in words]
        freq_counter = Counter(all_words)
        print(f"  Top 20 word frequencies: {freq_counter.most_common(20)}")

        # NER (simple regex-based)
        named_entities = set()
        for words in no_stopwords:
            for w in words:
                if w and w[0].isupper():
                    named_entities.add(w)
        print(f"  Named Entities (sample): {list(named_entities)[:10]}")

        #TODO Topic modeling (placeholder, real LDA etc. can be added)
        bigrams = []
        for words in no_stopwords:
            bigrams.extend([' '.join(words[i:i+2]) for i in range(len(words)-1)])
        bigram_counter = Counter(bigrams)
        print(f"  Top 10 bigrams (topics): {bigram_counter.most_common(10)}")

        # Prepare cleaned text for Groq (truncate to avoid token limit)
        cleaned_for_groq = []
        for words in no_stopwords[:15]:
            cleaned_for_groq.append(' '.join(words)[:500])
        combined_text = '\n'.join(cleaned_for_groq)
        print(f"Combined cleaned text for Groq: {combined_text}")
        # print(f"  Cleaned text sent to Groq (first 500 chars): {combined_text[:500]}")

        try:
            from groq import Groq
            import os
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not set in environment.")
            client = Groq(api_key=api_key)
            prompt = f"""
নিচের বাংলা সংবাদের টেক্সট থেকে আজকের জন্য সবচেয়ে গুরুত্বপূর্ণ এবং trending {limit}টি শব্দ বা বাক্যাংশ খুঁজে বের করো।\n\nনিয়মাবলী:\n1. শব্দগুলি অবশ্যই অর্থপূর্ণ এবং গুরুত্বপূর্ণ হতে হবে\n2. সাধারণ stop words (যেমন: এই, সেই, করা, হওয়া) এড়িয়ে চলো\n3. ব্যক্তির নাম, স্থানের নাম, সংস্থার নাম অন্তর্ভুক্ত করতে পারো\n4. একক শব্দ বা ছোট বাক্যাংশ (২-৩ শব্দ) উভয়ই গ্রহণযোগ্য\n5. প্রতিটি শব্দ/বাক্যাংশ আলাদা লাইনে লেখো\n6. শুধুমাত্র বাংলা শব্দ/বাক্যাংশ দাও, অন্য কিছু নয়\n\nটেক্সট:\n{combined_text}\n\ntrending শব্দ/বাক্যাংশ ({limit}টি):\n"""
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                stream=False,
            )
            print(f"  Groq response: {response.choices[0].message.content}")
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating trending words with Groq: {e}")
            return f"Error generating trending words: {e}"
    except Exception as e:
        print(f"[ERROR] generate_trending_word_candidates: {e}")
        return f"Error in trending word candidate generation: {e}"
