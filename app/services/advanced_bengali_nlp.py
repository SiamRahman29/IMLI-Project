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


class AdvancedBengaliProcessor:
    
    def __init__(self):
        self.stop_words = {
            'এবং', 'বা', 'কিন্তু', 'তবে', 'যদি', 'তাহলে', 'কেননা', 'যেহেতু', 'অতএব', 'সুতরাং',
            'এর', 'তার', 'তাদের', 'আমার', 'আমাদের', 'তোমার', 'তোমাদের', 'তিনি', 'তারা', 'আমি', 'আমরা',
            'তুমি', 'তোমরা', 'সে', 'এই', 'এটি', 'ওই', 'ওটি', 'যে', 'যেটি', 'কী', 'কি', 'কেন', 'কোথায়',
            'কখন', 'কীভাবে', 'কোন', 'কত', 'কতটা', 'হয়', 'হয়েছে', 'হবে', 'হচ্ছে', 'থাকা', 'থাকে', 'থাকবে',
            'আছে', 'ছিল', 'থেকে', 'পর্যন্ত', 'দিয়ে', 'করে', 'জন্য', 'সাথে', 'মধ্যে', 'ভিতরে', 'বাইরে',
            'উপর', 'নিচে', 'আগে', 'পরে', 'সময়', 'দিন', 'রাত', 'সকাল', 'বিকাল', 'সন্ধ্যা', 'এখন', 'তখন',
            'একটি', 'একটা', 'দুটি', 'দুটো', 'তিনটি', 'তিনটে', 'চারটি', 'চারটে', 'পাঁচটি', 'পাঁচটে',
            'না', 'নেই', 'নয়', 'নি', 'অন্য', 'আরও', 'আরো', 'অনেক', 'সব', 'সকল', 'প্রতি', 'খুব', 'বেশ',
            'লাইক', 'শেয়ার', 'কমেন্ট', 'ফলো', 'আনফলো', 'পোস্ট', 'স্ট্যাটাস', 'আপডেট', 'ট্যাগ',
            'কইছে', 'করছে', 'করব', 'করবো', 'যাব', 'যাবো', 'আসব', 'আসবো', 'হইছে', 'হবো', 'যাই', 'কি', 'কেমন',
            'ভাই', 'আপু', 'দাদা', 'আন্টি', 'আংকেল', 'বোন', 'ভাবী',
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
            'অই', 'অগত্যা', 'অত: পর', 'অতএব', 'অথচ', 'অথবা', 'অধিক', 'অধীনে', 'অধ্যায়', 'অনুগ্রহ',
            'অনুভূত', 'অনুযায়ী', 'অনুরূপ', 'অনুসন্ধান', 'অনুসরণ', 'অনুসারে', 'অনুসৃত', 'অনেক', 'অনেকে',
            'অনেকেই', 'অন্তত', 'অন্য', 'অন্যত্র', 'অন্যান্য', 'অপেক্ষাকৃতভাবে', 'অবধি', 'অবশ্য', 'অবশ্যই',
            'অবস্থা', 'অবিলম্বে', 'অভ্যন্তরস্থ', 'অর্জিত', 'অর্থাত', 'অসদৃশ', 'অসম্ভাব্য', 'আইন', 'আউট',
            'আক্রান্ত', 'আগামী', 'আগে', 'আগেই', 'আগ্রহী', 'আছে', 'আজ', 'আট', 'আদেশ', 'আদ্যভাগে', 'আন্দাজ',
            'আপনার', 'আপনি', 'আবার', 'আমরা', 'আমাকে', 'আমাদিগের', 'আমাদের', 'আমার', 'আমি', 'আর', 'আরও',
            'আশি', 'আশু', 'আসা', 'আসে', 'ই', 'ইচ্ছা', 'ইচ্ছাপূর্বক', 'ইতিমধ্যে', 'ইতোমধ্যে', 'ইত্যাদি',
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
            'প্রায়', 'প্রায়ই', 'প্রায়', 'ফলাফল', 'ফলে', 'ফিক্স', 'ফিরে', 'ফের', 'বক্তব্য', 'বছর', 'বড়', 'বদলে',
            'বন', 'বন্ধ', 'বরং', 'বরাবর', 'বর্ণন', 'বর্তমান', 'বলতে', 'বলল', 'বললেন', 'বলা', 'বলে', 'বলেছেন',
            'বলেন', 'বসে', 'বহু', 'বা', 'বাঁক', 'বাইরে', 'বাকি', 'বাড়ি', 'বাতিক', 'বাদ', 'বাদে', 'বার', 'বাহিরে',
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
                    words.append(word)
        
        return words
    
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
            min_df=2,
            max_df=0.8,
            lowercase=False
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
        if len(phrases) < n_clusters:
            # If we have fewer phrases than clusters, put each in its own cluster
            return {i: [phrase] for i, phrase in enumerate(phrases)}
        
        def bengali_preprocessor(text):
            words = self.advanced_tokenize(text)
            return ' '.join(words)
        
        vectorizer = TfidfVectorizer(
            preprocessor=bengali_preprocessor,
            ngram_range=(1, 2),
            max_features=500,
            min_df=1,
            lowercase=False
        )
        
        try:
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
            # Fallback: return all phrases in one cluster
            return {0: phrases}
    
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


class TrendingBengaliAnalyzer:
    """
    Main analyzer class for Bengali trending content
    """
    
    def __init__(self):
        self.processor = AdvancedBengaliProcessor()
    
    def analyze_trending_content(self, contents: List[Dict], source_type: str = 'mixed') -> Dict:
        """
        Comprehensive analysis of trending content
        """
        # Extract text content
        texts = []
        for content in contents:
            if 'title' in content and 'description' in content:
                text = f"{content['title']} {content['description']}"
            elif 'content' in content:
                text = content['content']
            else:
                continue
            texts.append(text)
        
        if not texts:
            return {}
        
        # Update word frequency cache
        self.processor.update_word_frequency_cache(texts)
        
        # Extract trending keywords
        trending_keywords = self.processor.extract_trending_keywords(texts, top_k=100)
        
        # Extract named entities
        all_entities = {'persons': [], 'places': [], 'organizations': [], 'dates': []}
        for text in texts:
            entities = self.processor.extract_named_entities(text)
            for entity_type in all_entities:
                all_entities[entity_type].extend(entities[entity_type])
        
        # Remove duplicates and count frequencies
        for entity_type in all_entities:
            entity_counter = Counter(all_entities[entity_type])
            all_entities[entity_type] = entity_counter.most_common(20)
        
        # Sentiment analysis
        sentiment_scores = []
        for text in texts:
            sentiment = self.processor.calculate_text_sentiment(text)
            sentiment_scores.append(sentiment)
        
        # Average sentiment
        avg_sentiment = {
            'positive': np.mean([s['positive'] for s in sentiment_scores]),
            'negative': np.mean([s['negative'] for s in sentiment_scores]),
            'neutral': np.mean([s['neutral'] for s in sentiment_scores])
        }
        
        # Cluster similar phrases
        phrases = [kw[0] for kw in trending_keywords[:50]]
        clustered_phrases = self.processor.cluster_similar_phrases(phrases, n_clusters=8)
        
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
    
    def save_models(self):
        """Save all models for future use"""
        self.processor.save_word_frequency_model()


def test_bengali_analyzer():
    """Test the Bengali analyzer with sample text"""
    analyzer = TrendingBengaliAnalyzer()
    
    sample_contents = [
        {
            'title': 'বাংলাদেশের অর্থনীতি ভালো অবস্থায়',
            'description': 'দেশের অর্থনৈতিক অবস্থা উন্নতির দিকে এগিয়ে চলেছে। মানুষের আয় বৃদ্ধি পাচ্ছে।'
        },
        {
            'title': 'শিক্ষা ক্ষেত্রে নতুন পরিকল্পনা',
            'description': 'সরকার শিক্ষা ক্ষেত্রে আধুনিকায়নের জন্য নতুন পরিকল্পনা গ্রহণ করেছে।'
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
