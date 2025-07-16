# PROMPT MESSAGES AND FREQUENCY FLOW ANALYSIS

## Overview
This document explains the prompt messages used in the main pipeline, their purpose, and how frequency is calculated and flows through the system.

## 1. PROMPT MESSAGES IN THE MAIN PIPELINE

### A. Reddit Subreddit Analysis Prompt (Individual Subreddit Processing)
**Location**: `routes_new.py` lines 225-239  
**Purpose**: Extract trending words from individual Reddit subreddits

```bengali
তুমি একজন বিশেষজ্ঞ বাংলাদেশি সংবাদ বিশ্লেষক। নিচের Reddit r/{subreddit} থেকে পোস্টগুলো বিশ্লেষণ করে ঠিক 2টি ট্রেন্ডিং শব্দ/বাক্যাংশ বের করো।

Reddit Content from r/{subreddit}:
{subreddit_content}

নির্দেশনা:
1. ঠিক 2টি সবচেয়ে প্রাসঙ্গিক ট্রেন্ডিং শব্দ/বাক্যাংশ বের করো
2. প্রতিটি শব্দ/বাক্যাংশ 2-4 শব্দের মধ্যে হতে হবে
3. শব্দগুলো বাংলা বা ইংরেজি হতে পারে, কিন্তু অর্থবহ হতে হবে
4. ব্যক্তিগত নাম এড়িয়ে চলো, বিষয়বস্তুর উপর ফোকাস করো
5. সাম্প্রতিক ও আলোচিত বিষয়গুলো অগ্রাধিকার দাও

আউটপুট ফরম্যাট:
1. শব্দ১
2. শব্দ২

শুধুমাত্র উপরের ফরম্যাটে 2টি শব্দ দাও। অতিরিক্ত ব্যাখ্যা যোগ করো না।
```

**Function**: Extracts exactly 2 trending words per subreddit to maintain balance across different data sources.

### B. Final Category-wise Selection Prompt (Main LLM Analysis)
**Location**: `routes_new.py` lines 327-354  
**Purpose**: Select the top 10 most relevant words from each category

```bengali
তুমি একজন বিশেষজ্ঞ বাংলাদেশি সংবাদ বিশ্লেষক।আপনাকে নিম্নলিখিত ক্যাটেগরি অনুযায়ী ট্রেন্ডিং শব্দগুলো থেকে প্রতিটি ক্যাটেগরি থেকে সবচেয়ে গুরুত্বপূর্ণ 10টি করে শব্দ বেছে নিতে হবে। এমন শব্দ/বাক্যাংশ দাও যেটা শুনলে মানুষ বুঝতে পারবে যে এটা কীসের সাথে সম্পর্কিত। যার একটা অর্থ থাকবে, এমন কিছু দেবে না যেটা অর্থহীন এবং যেটা দেখলে কনটেক্সট বোঝা যাবে না।

ক্যাটেগরি অনুযায়ী ট্রেন্ডিং শব্দ:
{categories_text}

নির্বাচনের নিয়মাবলী:
1. প্রতিটি ক্যাটেগরি থেকে সবচেয়ে প্রাসঙ্গিক ১০টি শব্দ নির্বাচন করুন
2. প্রতিটি শব্দ/বাক্যাংশ ২-৪ শব্দের মধ্যে এবং স্পষ্ট অর্থবোধক হতে হবে
3. এক ক্যাটেগরিতে একই টপিক বা অর্থের কাছাকাছি শব্দ থাকবে না, প্রতিটি শব্দ ইউনিক ও প্রসঙ্গভিত্তিক অর্থবহ হতে হবে
4. response শুধুমাত্র bangla language a deo
5. ব্যক্তিগত নাম এড়িয়ে চলুন, বিষয়বস্তুর উপর ফোকাস করুন
6. সাম্প্রতিক ও জনপ্রিয় বিষয়গুলো অগ্রাধিকার দিন

আউটপুট ফরম্যাট:
প্রতিটি ক্যাটেগরির জন্য নিম্নরূপ ফরম্যাটে দিন:

ক্যাটেগরি নাম:
1. শব্দ১
2. শব্দ২
3. শব্দ৩
4. শব্দ৪
...
10. শব্দ১০

অন্য ক্যাটেগরি নাম:
1. শব্দ১
2. শব্দ২
...
...
10. শব্দ১০

শুধুমাত্র উপরের ফরম্যাটে উত্তর দিন। অতিরিক্ত ব্যাখ্যা বা মন্তব্য যোগ করবেন না।
```

**Function**: The main LLM analysis that curates the final set of trending words for the frontend display.

## 2. FREQUENCY CALCULATION AND FLOW

### Step 1: Initial Data Collection
**Sources**: 
- Newspaper articles (scraped from multiple Bengali newspapers)
- Reddit posts (from Bangladesh-related subreddits)

### Step 2: N-gram Analysis and Initial Frequency Calculation
**Location**: `helpers.py` - `calculate_frequency_scores()` method
**Process**:
```python
def calculate_frequency_scores(self, texts: List[str]) -> Dict[str, Dict]:
    """Calculate frequency-based scores for n-grams"""
    # Process unigrams, bigrams, and trigrams
    # Count occurrences across all texts
    # Calculate TF-IDF scores
    # Return frequency dictionary with counts
```

**Frequency Sources**:
1. **Article Headlines**: Counted in article titles and headings
2. **Article Content**: Full text analysis for n-gram extraction
3. **Reddit Posts**: Post titles and content analysis

### Step 3: Category-wise Trending Word Aggregation
**Location**: `routes_new.py` - Category processing section
**Process**:
- Words are grouped by categories (রাজনীতি, অর্থনীতি, খেলাধুলা, etc.)
- Initial frequency comes from n-gram analysis
- Words are ranked by combined frequency and relevance scores

### Step 4: LLM Selection with Frequency Preservation
**Location**: `routes_new.py` lines 420-450
**Process**:
```python
# Find frequency from original category_wise_trending data
frequency = 1  # Default frequency

# Search in the original category trending words for frequency info
original_words = category_wise_trending.get(current_category, [])
for orig_word in original_words:
    if isinstance(orig_word, dict) and orig_word.get('word') == word:
        frequency = orig_word.get('frequency', 1)
        break
    elif isinstance(orig_word, str) and orig_word == word:
        # If it's a simple string, estimate frequency by counting in articles
        if results and 'category_wise_articles' in results:
            category_articles = results['category_wise_articles'].get(current_category, [])
            word_count = 0
            for article in category_articles:
                heading = article.get('heading', '') + ' ' + article.get('title', '')
                word_count += heading.lower().count(word.lower())
            frequency = max(1, word_count)
        break
```

### Step 5: Final Frontend Data Structure
**Location**: `routes_new.py` lines 440-444
**Output Format**:
```python
word_info = {
    'word': word,
    'frequency': frequency,
    'category': current_category
}
```

## 3. FREQUENCY CALCULATION METHODS

### Method A: Direct Frequency Lookup
- If word exists in `category_wise_trending` with frequency data
- Uses pre-calculated frequency from n-gram analysis

### Method B: Article-based Counting
- When word is found but lacks frequency data
- Counts occurrences in category-specific article headlines
- Formula: `word_count = heading.lower().count(word.lower())`
- Minimum frequency = 1

### Method C: Fallback Default
- When no frequency data is available
- Default frequency = 1
- Applied to LLM-generated words not found in original data

## 4. WHY FREQUENCY SOMETIMES DEFAULTS TO 1

### Reasons for Default Frequency:
1. **New LLM Words**: LLM generates contextually relevant words not present in original frequency analysis
2. **Synonym Selection**: LLM chooses better synonyms or variations of original words
3. **Data Source Mismatch**: Word appears in Reddit but not in newspaper articles (or vice versa)
4. **Processing Limitations**: Some words may be filtered out during n-gram processing

### When Frequency is Calculated:
1. **Direct Match**: Word exists in `category_wise_trending` with frequency data
2. **Article Counting**: Word found in category articles, frequency calculated by counting
3. **High-frequency Words**: Words that appear multiple times across different sources

## 5. DATA FLOW SUMMARY

```
Newspaper Articles + Reddit Posts
         ↓
N-gram Analysis (helpers.py)
         ↓
Frequency Calculation
         ↓
Category-wise Grouping
         ↓
LLM Selection (2 prompts)
         ↓
Frequency Attachment/Calculation
         ↓
Frontend Display (GenerateWords.jsx)
         ↓
Hover Tooltips with Frequency
```

## 6. FREQUENCY DISPLAY IN FRONTEND

### Visual Indicators:
- **Frequency Badge**: Shows actual count next to each word
- **Hover Tooltip**: Bengali text showing "ফ্রিকোয়েন্সি: X" (Frequency: X)
- **Color Coding**: Different badge styles for different frequency ranges

### Frontend Data Structure:
```javascript
{
  word: "শব্দ",
  frequency: 5,
  category: "রাজনীতি"
}
```

## 7. OPTIMIZATION NOTES

### Current Limitations:
1. Default frequency of 1 for many LLM-selected words
2. Frequency calculation limited to headline matching
3. No cross-category frequency normalization

### Potential Improvements:
1. Full-text frequency analysis instead of headline-only
2. Weighted frequency based on article importance
3. Time-based frequency decay for trending analysis
4. Cross-source frequency aggregation
