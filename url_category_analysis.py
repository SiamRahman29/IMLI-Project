#!/usr/bin/env python3
"""
URL Pattern & Category Detection Analysis
Author: AI Assistant
Date: 2025-06-24
"""

import json
import re
from collections import defaultdict
from urllib.parse import urlparse

def analyze_url_patterns():
    """Analyze URL patterns and categorize them"""
    
    # Load JSON data
    with open('scraped_urls_from_active_newspapers_20250624_015711.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print('🔍 URL Pattern & Category Detection Analysis')
    print('=' * 80)
    print(f'Total URLs: {data["extraction_info"]["total_urls"]}')
    print(f'Total Sources: {data["extraction_info"]["total_sources"]}')
    print()
    
    # Category detection function
    def detect_category(url, title=''):
        """Detect category based on URL pattern and title"""
        path = urlparse(url).path.lower()
        title = title.lower()
        domain = urlparse(url).netloc.lower()
        
        # URL path-based detection (priority order matters)
        if any(x in path for x in ['/fact-check', '/factcheck']):
            return 'Fact-Check'
        elif any(x in path for x in ['/bangladesh', '/national', '/country', '/dhaka', '/chittagong', '/barisal', '/rangpur']):
            return 'National/Bangladesh'
        elif any(x in path for x in ['/international', '/world', '/middle-east', '/america', '/asia', '/europe']):
            return 'International'
        elif any(x in path for x in ['/sports', '/cricket', '/football', '/game', '/tennis']):
            return 'Sports'
        elif any(x in path for x in ['/business', '/economy', '/economics', '/market', '/bank']):
            return 'Business/Economy'
        elif any(x in path for x in ['/politics', '/political', '/election']):
            return 'Politics'
        elif any(x in path for x in ['/entertainment', '/bollywood', '/hollywood', '/music', '/cinema', '/television']):
            return 'Entertainment'
        elif any(x in path for x in ['/technology', '/tech', '/digital']):
            return 'Technology'
        elif any(x in path for x in ['/health', '/medical', '/corona', '/covid', '/dengue']):
            return 'Health'
        elif any(x in path for x in ['/education', '/campus', '/university', '/school']):
            return 'Education'
        elif any(x in path for x in ['/opinion', '/editorial', '/op-ed', '/column', '/analysis']):
            return 'Opinion/Editorial'
        elif any(x in path for x in ['/lifestyle', '/life', '/fashion', '/food', '/care', '/rupbatika']):
            return 'Lifestyle'
        elif any(x in path for x in ['/religion', '/islam', '/islamic']):
            return 'Religion'
        elif any(x in path for x in ['/environment', '/climate', '/weather']):
            return 'Environment'
        elif any(x in path for x in ['/science', '/research']):
            return 'Science'
        elif any(x in path for x in ['/job', '/career', '/employment']):
            return 'Jobs/Career'
        elif any(x in path for x in ['/picture', '/photo', '/gallery', '/photos']):
            return 'Photos/Gallery'
        elif any(x in path for x in ['/video', '/videos']):
            return 'Video'
        elif any(x in path for x in ['/web-stories', '/stories']):
            return 'Web Stories'
        elif any(x in path for x in ['/women', '/woman']):
            return 'Women'
        elif any(x in path for x in ['/trivia', '/odd', '/adda']):
            return 'Trivia/Miscellaneous'
        elif 'epaper' in domain:
            return 'E-Paper'
        elif path in ['/', '/national', '/country-news', '/poll', '/namaz-sehri-iftar-time']:
            return 'Homepage/Category'
        
        return 'General/Other'
    
    # Analyze URL patterns by source
    url_patterns_by_source = defaultdict(set)
    category_breakdown = defaultdict(lambda: defaultdict(int))
    overall_categories = defaultdict(int)
    
    for source, urls in data['urls_by_source'].items():
        print(f'📰 {source.upper()} Analysis ({len(urls)} URLs)')
        print('-' * 50)
        
        # Sample URLs for pattern display
        sample_urls = urls[:5]
        print('Sample URLs:')
        for i, url_data in enumerate(sample_urls, 1):
            url = url_data['url']
            title = url_data.get('title', '')[:60] + '...' if len(url_data.get('title', '')) > 60 else url_data.get('title', '')
            category = detect_category(url, title)
            
            print(f'  {i}. {url}')
            print(f'     Title: {title}')
            print(f'     Category: {category}')
            
            # Extract URL pattern
            parsed = urlparse(url)
            path = parsed.path
            pattern = re.sub(r'/[a-f0-9]{8,}', '/[ID]', path)  # Hex IDs
            pattern = re.sub(r'/\d{6,}', '/[NUMBER]', pattern)  # Long numbers
            pattern = re.sub(r'/ajp[a-z0-9]+', '/[ARTICLE_ID]', pattern)  # Ajker Patrika IDs
            pattern = re.sub(r'/[a-z0-9]{10,}', '/[LONG_ID]', pattern)  # Other long IDs
            
            url_patterns_by_source[source].add(f'{parsed.netloc}{pattern}')
        
        print()
        
        # Categorize all URLs for this source
        for url_data in urls:
            url = url_data['url']
            title = url_data.get('title', '')
            category = detect_category(url, title)
            
            category_breakdown[source][category] += 1
            overall_categories[category] += 1
        
        # Display URL patterns for this source
        print('🔗 URL Patterns:')
        for pattern in sorted(url_patterns_by_source[source]):
            print(f'   {pattern}')
        
        # Display categories for this source
        print(f'\n📊 Categories:')
        source_total = len(urls)
        for cat, count in sorted(category_breakdown[source].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / source_total) * 100
            print(f'   {cat:25} : {count:3d} URLs ({percentage:5.1f}%)')
        
        print('\n' + '='*80 + '\n')
    
    # Overall summary
    print('🎯 OVERALL CATEGORY SUMMARY')
    print('=' * 80)
    total_urls = data['extraction_info']['total_urls']
    
    for cat, count in sorted(overall_categories.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_urls) * 100
        bar_length = int(percentage / 2)  # Scale for visual bar
        bar = '█' * bar_length + '░' * (50 - bar_length)
        print(f'{cat:25} : {count:3d} URLs ({percentage:5.1f}%) {bar[:20]}')
    
    print(f'\nTotal URLs Processed: {total_urls}')
    
    # URL Pattern Summary
    print('\n🔗 UNIQUE URL PATTERNS SUMMARY')
    print('=' * 80)
    all_patterns = set()
    for source_patterns in url_patterns_by_source.values():
        all_patterns.update(source_patterns)
    
    for pattern in sorted(all_patterns):
        print(f'   {pattern}')
    
    print(f'\nTotal Unique Patterns: {len(all_patterns)}')

if __name__ == "__main__":
    analyze_url_patterns()
