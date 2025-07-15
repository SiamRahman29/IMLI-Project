#!/usr/bin/env python3
"""
Enhanced URL Pattern-Based Category Detection System
Author: AI Assistant
Date: 2025-06-24

This system uses URL patterns as the primary method for category detection
and creates separate categories for uncategorized URLs to ensure nothing is missed.
"""

import json
import re
from collections import defaultdict
from urllib.parse import urlparse
from datetime import datetime


class URLPatternCategoryDetector:
   def __init__(self):
       """Initialize the category detector with comprehensive URL patterns"""
      
       # Primary URL pattern-based categories (in priority order)
       self.url_patterns = {
           # Fact Check (highest priority)
           'Fact-Check': [
               r'/fact-check',
               r'/factcheck',
               r'/verification'
           ],
          
           # National/Bangladesh News
           'National/Bangladesh': [
               r'/bangladesh',
               r'/national',
               r'/country',
               r'/dhaka',
               r'/chittagong',
               r'/barisal',
               r'/rangpur',
               r'/sylhet',
               r'/khulna',
               r'/rajshahi',
               r'/mymensingh',
               r'/সারাদেশ',  # Encoded Bengali
               r'/জাতীয়',   # Encoded Bengali
               r'/country-news'
           ],
          
           # International News
           'International': [
               r'/international',
               r'/world',
               r'/middle-east',
               r'/america',
               r'/asia',
               r'/europe',
               r'/africa',
               r'/বিদেশ',    # Encoded Bengali
               r'/আন্তর্জাতিক'  # Encoded Bengali
           ],
          
           # Politics
           'Politics': [
               r'/politics',
               r'/political',
               r'/election',
               r'/রাজনীতি'   # Encoded Bengali
           ],
          
           # Sports
           'Sports': [
               r'/sports',
               r'/cricket',
               r'/football',
               r'/game',
               r'/tennis',
               r'/খেলা'      # Encoded Bengali
           ],
          
           # Entertainment
           'Entertainment': [
               r'/entertainment',
               r'/bollywood',
               r'/hollywood',
               r'/tollywood',
               r'/dhallywood',
               r'/music',
               r'/cinema',
               r'/web-stories',
               r'/stories',
               r'/television',
               r'/বিনোদন'    # Encoded Bengali
           ],
          
           # Business/Economy
           'Business/Economy': [
               r'/business',
               r'/economy',
               r'/economics',
               r'/market',
               r'/bank',
               r'/finance',
               r'/অর্থনীতি'   # Encoded Bengali
           ],
          
           # Technology
           'Technology': [
               r'/technology',
               r'/tech',
               r'/digital',
               r'/প্রযুক্তি'   # Encoded Bengali
           ],
          
           # Health
           'Health': [
               r'/health',
               r'/medical',
               r'/corona',
               r'/covid',
               r'/dengue',
               r'/স্বাস্থ্য'   # Encoded Bengali
           ],
          
           # Education
           'Education': [
               r'/education',
               r'/campus',
               r'/university',
               r'/school',
               r'/disease',
               r'/শিক্ষা'     # Encoded Bengali
           ],
          
           # Opinion/Editorial
           'Opinion/Editorial': [
               r'/opinion',
               r'/editorial',
               r'/op-ed',
               r'/column',
               r'/analysis',
               r'/মতামত'     # Encoded Bengali
           ],
          
           # Lifestyle
           'Lifestyle': [
               r'/lifestyle',
               r'/life',
               r'/fashion',
               r'/food',
               r'/care',
               r'/rupbatika',
               r'/জীবনধারা'   # Encoded Bengali
           ],
          
           # Religion
           'Religion': [
               r'/religion',
               r'/islam',
               r'/islamic',
               r'/islam-life',
               r'/ইসলাম'     # Encoded Bengali
           ],
          
           # Environment
           'Environment': [
               r'/environment',
               r'/climate',
               r'/weather',
               r'/পরিবেশ'    # Encoded Bengali
           ],
          
           # Science
           'Science': [
               r'/science',
               r'/research',
               r'/tech',
               r'/it',
               r'/বিজ্ঞান'    # Encoded Bengali
           ],
          
           # Jobs/Career
           'Jobs/Career': [
               r'/job',
               r'/career',
               r'/employment',
               r'/job-seek',
               r'/চাকরি'     # Encoded Bengali
           ],
          
           # Photos/Gallery
           'Photos/Gallery': [
               r'/picture',
               r'/photo',
               r'/gallery',
               r'/photos',
               r'/ছবি'       # Encoded Bengali
           ],
          
           # Video
           'Video': [
               r'/video',
               r'/videos',
               r'/ভিডিও'     # Encoded Bengali
           ],
          
           # Women
           'Women': [
               r'/women',
               r'/woman',
               r'/নারী'      # Encoded Bengali
           ],
          
           # Trivia/Miscellaneous
           'Trivia/Miscellaneous': [
               r'/trivia',
               r'/odd',
               r'/adda',
               r'/আড্ডা'      # Encoded Bengali
           ],
          
           # Web Stories
           'Web Stories': [
               r'/web-stories',
               r'/stories'
           ],
           
           # Literature/Culture
           'Literature/Culture': [
               r'/literature',
               r'/sahitya',
               r'/সাহিত্য',
               r'/culture',
               r'/sangskriti',
               r'/সংস্কৃতি',
               r'/arts',
               r'/art-literature',
               r'/arts-and-literature',
               r'/sahitto-o-sangskriti',
               r'/সাহিত্য-সংস্কৃতি',
               r'/topic/literature',
               r'/catcn/literature',
               r'/newscat/literature',
               r'/category/literature',
               r'/category/সাহিত্য',
               r'/topic/সাহিত্য',
               r'/categories/সাহিত্য-ও-সংস্কৃতি'
           ],
           
           # Ethnic Minorities
           'Ethnic Minorities': [
               r'/ক্ষুদ্র.*নৃ.*গোষ্ঠী',
               r'/আদিবাসী',
               r'/upjati',
               r'/উপজাতি',
               r'/tribe',
               r'/tribal',
               r'/ethnic',
               r'/minority',
               r'/minorities',
               r'/indigenous',
               r'/topic/ক্ষুদ্র.*নৃ.*গোষ্ঠী',
               r'/topic/আদিবাসী',
               r'/tags/tribe',
               r'/topic/3942',
               r'/topic/ক্ষুদ্র%20নৃ-গোষ্ঠী',
               r'/topic/ক্ষুদ্র-জাতিগোষ্ঠী',
               r'/tag/ক্ষুদ্র-নৃ-গোষ্ঠী',
               r'/news/category/ক্ষুদ্র-নৃ-গোষ্ঠী'
           ]
       }
      
       # Special domain/path patterns
       self.special_patterns = {
           'E-Paper': [
               r'epaper\.',
               r'/epaper'
           ],
           'Homepage/Category': [
               r'^/$',
               r'/poll/',
               r'/namaz-sehri-iftar-time'
           ]
       }
      
       # Statistics tracking
       self.categorization_stats = {
           'total_urls': 0,
           'categorized_by_pattern': 0,
           'uncategorized': 0,
           'category_counts': defaultdict(int),
           'uncategorized_patterns': defaultdict(int)
       }
  
   def detect_category_by_url_pattern(self, url):
       """
       Detect category based on URL pattern (primary method)
       Returns: (category, confidence_score, matched_pattern)
       """
       parsed_url = urlparse(url)
       full_url = url.lower()
       path = parsed_url.path.lower()
       domain = parsed_url.netloc.lower()
      
       # Check special domain patterns first
       for category, patterns in self.special_patterns.items():
           for pattern in patterns:
               if re.search(pattern, full_url):
                   return category, 1.0, pattern
      
       # Check main URL patterns
       for category, patterns in self.url_patterns.items():
           for pattern in patterns:
               if re.search(pattern, path):
                   return category, 1.0, pattern
      
       # If no pattern matches, return None
       return None, 0.0, None
  
   def categorize_uncategorized_urls(self, uncategorized_urls):
       """
       Create sub-categories for uncategorized URLs based on their patterns
       """
       uncategorized_categories = defaultdict(list)
      
       for url_data in uncategorized_urls:
           url = url_data['url']
           parsed_url = urlparse(url)
           domain = parsed_url.netloc
           path = parsed_url.path
          
           # Create pattern-based subcategories
           if 'prothomalo.com' in domain:
               # Prothom Alo specific patterns
               if re.search(r'/[a-z]{10,}$', path):
                   subcategory = f"Prothomalo_Article_ID"
               else:
                   subcategory = f"Prothomalo_Other"
          
           elif 'jugantor.com' in domain:
               # Jugantor specific patterns
               if path in ['/', '/national', '/politics', '/international']:
                   subcategory = f"Jugantor_Category_Page"
               else:
                   subcategory = f"Jugantor_Other"
          
           elif 'samakal.com' in domain:
               # Samakal specific patterns
               if '/divisions/' in path:
                   subcategory = f"Samakal_Regional"
               elif domain.startswith('en.'):
                   subcategory = f"Samakal_English"
               else:
                   subcategory = f"Samakal_Other"
          
           elif 'dailyjanakantha.com' in domain:
               # Janakantha specific patterns
               if '/news/' in path:
                   subcategory = f"Janakantha_News_Article"
               else:
                   subcategory = f"Janakantha_Other"
          
           elif 'dailyinqilab.com' in domain:
               # Inqilab specific patterns
               if '/news/' in path:
                   subcategory = f"Inqilab_News_Article"
               else:
                   subcategory = f"Inqilab_Other"
          
           elif 'manobkantha.com.bd' in domain:
               # Manobkantha specific patterns
               if '/news/' in path:
                   # Try to extract category from URL
                   category_match = re.search(r'/news/([^/]+)/', path)
                   if category_match:
                       subcategory = f"Manobkantha_{category_match.group(1).title()}"
                   else:
                       subcategory = f"Manobkantha_News"
               else:
                   subcategory = f"Manobkantha_Other"
          
           elif 'ajkerpatrika.com' in domain:
               # Ajker Patrika specific patterns
               path_parts = [p for p in path.split('/') if p]
               if len(path_parts) >= 2:
                   subcategory = f"AjkerPatrika_{path_parts[0].title()}"
               else:
                   subcategory = f"AjkerPatrika_Other"
          
           else:
               # Unknown domain
               subcategory = f"Unknown_Domain_{domain.replace('.', '_')}"
          
           uncategorized_categories[subcategory].append(url_data)
      
       return uncategorized_categories
  
   def analyze_json_file(self, json_file_path):
       """
       Analyze the JSON file and categorize URLs using pattern-based detection
       """
       print('🔍 Enhanced URL Pattern-Based Category Detection')
       print('=' * 80)
      
       # Load JSON data
       with open(json_file_path, 'r', encoding='utf-8') as f:
           data = json.load(f)
      
       total_urls = data['extraction_info']['total_urls']
       self.categorization_stats['total_urls'] = total_urls
      
       print(f'📊 Processing {total_urls} URLs from {data["extraction_info"]["total_sources"]} sources')
       print()
      
       # Results storage
       categorized_urls = defaultdict(list)
       uncategorized_urls = []
       source_wise_stats = defaultdict(lambda: defaultdict(int))
      
       # Process each source
       for source, urls in data['urls_by_source'].items():
           print(f'📰 Processing {source.upper()} ({len(urls)} URLs)')
          
           source_categorized = 0
           source_uncategorized = 0
          
           for url_data in urls:
               url = url_data['url']
               category, confidence, pattern = self.detect_category_by_url_pattern(url)
              
               if category:
                   # Successfully categorized
                   url_data['category'] = category
                   url_data['detection_method'] = 'url_pattern'
                   url_data['matched_pattern'] = pattern
                   url_data['confidence'] = confidence
                  
                   categorized_urls[category].append(url_data)
                   source_wise_stats[source][category] += 1
                   source_categorized += 1
                   self.categorization_stats['categorized_by_pattern'] += 1
                   self.categorization_stats['category_counts'][category] += 1
               else:
                   # Could not categorize
                   url_data['category'] = 'Uncategorized'
                   url_data['detection_method'] = 'none'
                   url_data['matched_pattern'] = None
                   url_data['confidence'] = 0.0
                  
                   uncategorized_urls.append(url_data)
                   source_uncategorized += 1
                   self.categorization_stats['uncategorized'] += 1
                  
                   # Track uncategorized pattern
                   parsed_url = urlparse(url)
                   domain_pattern = parsed_url.netloc
                   self.categorization_stats['uncategorized_patterns'][domain_pattern] += 1
          
           # Show source statistics
           categorization_rate = (source_categorized / len(urls)) * 100
           print(f'   ✅ Categorized: {source_categorized}/{len(urls)} ({categorization_rate:.1f}%)')
           print(f'   ❓ Uncategorized: {source_uncategorized}')
           print()
      
       # Process uncategorized URLs into subcategories
       print('🔄 Processing Uncategorized URLs into Subcategories...')
       uncategorized_subcategories = self.categorize_uncategorized_urls(uncategorized_urls)
      
       # Display results
       self._display_results(categorized_urls, uncategorized_subcategories, source_wise_stats)
      
       # Save enhanced results
       self._save_enhanced_results(data, categorized_urls, uncategorized_subcategories)
      
       return categorized_urls, uncategorized_subcategories
  
   def _display_results(self, categorized_urls, uncategorized_subcategories, source_wise_stats):
       """Display comprehensive results"""
      
       print('\n🎯 CATEGORIZATION RESULTS')
       print('=' * 80)
      
       total_urls = self.categorization_stats['total_urls']
       categorized_count = self.categorization_stats['categorized_by_pattern']
       uncategorized_count = self.categorization_stats['uncategorized']
      
       print(f'📊 Overall Statistics:')
       print(f'   Total URLs: {total_urls}')
       print(f'   ✅ Categorized by Pattern: {categorized_count} ({(categorized_count/total_urls)*100:.1f}%)')
       print(f'   ❓ Uncategorized: {uncategorized_count} ({(uncategorized_count/total_urls)*100:.1f}%)')
       print()
      
       # Main categories
       print('📈 Main Categories (Pattern-Based):')
       for category, urls in sorted(categorized_urls.items(), key=lambda x: len(x[1]), reverse=True):
           count = len(urls)
           percentage = (count / total_urls) * 100
           bar = '█' * int(percentage / 2) + '░' * (25 - int(percentage / 2))
           print(f'   {category:25} : {count:3d} URLs ({percentage:5.1f}%) {bar[:20]}')
      
       print()
      
       # Uncategorized subcategories
       print('📋 Uncategorized Subcategories:')
       total_uncategorized = sum(len(urls) for urls in uncategorized_subcategories.values())
       for subcategory, urls in sorted(uncategorized_subcategories.items(), key=lambda x: len(x[1]), reverse=True):
           count = len(urls)
           percentage = (count / total_uncategorized) * 100 if total_uncategorized > 0 else 0
           print(f'   {subcategory:30} : {count:3d} URLs ({percentage:5.1f}%)')
      
       print(f'\n   Total Uncategorized Subcategories: {len(uncategorized_subcategories)}')
       print(f'   Total Uncategorized URLs: {total_uncategorized}')
  
   def _save_enhanced_results(self, original_data, categorized_urls, uncategorized_subcategories):
       """Save enhanced categorization results"""
      
       timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
       output_file = f'enhanced_categorized_urls_{timestamp}.json'
      
       # Prepare enhanced data structure
       enhanced_data = {
           'categorization_info': {
               'method': 'url_pattern_based',
               'total_urls': self.categorization_stats['total_urls'],
               'categorized_count': self.categorization_stats['categorized_by_pattern'],
               'uncategorized_count': self.categorization_stats['uncategorized'],
               'categorization_date': datetime.now().isoformat(),
               'main_categories_count': len(categorized_urls),
               'uncategorized_subcategories_count': len(uncategorized_subcategories)
           },
           'original_extraction_info': original_data['extraction_info'],
           'main_categories': {},
           'uncategorized_subcategories': {},
           'categorization_stats': dict(self.categorization_stats)
       }
      
       # Add main categories
       for category, urls in categorized_urls.items():
           enhanced_data['main_categories'][category] = {
               'count': len(urls),
               'urls': urls
           }
      
       # Add uncategorized subcategories
       for subcategory, urls in uncategorized_subcategories.items():
           enhanced_data['uncategorized_subcategories'][subcategory] = {
               'count': len(urls),
               'urls': urls
           }
      
       # Save to file
       with open(output_file, 'w', encoding='utf-8') as f:
           json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
      
       print(f'\n💾 Enhanced Results Saved:')
       print(f'   📄 File: {output_file}')
       print(f'   📊 Main Categories: {len(categorized_urls)}')
       print(f'   📋 Uncategorized Subcategories: {len(uncategorized_subcategories)}')
       print(f'   🔗 Total URLs: {self.categorization_stats["total_urls"]}')


def main():
   """Main function to run the enhanced category detection"""
  
   # Initialize detector
   detector = URLPatternCategoryDetector()
  
   # Analyze the JSON file
   json_file = 'scraped_urls_from_active_newspapers_20250624_015711.json'
  
   try:
       categorized_urls, uncategorized_subcategories = detector.analyze_json_file(json_file)
      
       print(f'\n✅ Enhanced URL Pattern-Based Category Detection Completed!')
       print(f'📊 {len(categorized_urls)} main categories + {len(uncategorized_subcategories)} uncategorized subcategories')
       print(f'🎯 No URL left uncategorized - everything is properly classified!')
      
   except FileNotFoundError:
       print(f'❌ Error: JSON file "{json_file}" not found!')
       print('Please make sure the file exists in the current directory.')
   except Exception as e:
       print(f'❌ Error: {str(e)}')


if __name__ == "__main__":
   main()


