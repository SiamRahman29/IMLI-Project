#!/usr/bin/env python3
"""
Category-based Trending Analysis Service
Author: AI Assistant
Date: 2025-06-24

This service provides category-wise trending word analysis and database operations
for the enhanced category detection system.
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.models.word import CategoryTrendingPhrase, TrendingPhrase, Article
from app.routes.helpers import detect_category_from_url


class CategoryTrendingService:
    """Service for category-based trending phrase analysis"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def save_category_trending_phrases(self, phrases_by_category: Dict[str, List[Dict]], 
                                     analysis_date: date, source: str = "news") -> int:
        """
        Save category-wise trending phrases to database
        
        Args:
            phrases_by_category: Dict with category as key and list of phrase dicts as value
            analysis_date: Date of analysis
            source: Source of the phrases (news, social_media)
        
        Returns:
            Number of phrases saved
        """
        saved_count = 0
        
        try:
            for category, phrases in phrases_by_category.items():
                if not phrases:
                    continue
                
                for phrase_data in phrases:
                    category_phrase = CategoryTrendingPhrase(
                        date=analysis_date,
                        category=category,
                        phrase=phrase_data.get('phrase', ''),
                        score=phrase_data.get('score', 0.0),
                        frequency=phrase_data.get('frequency', 0),
                        phrase_type=phrase_data.get('phrase_type', 'unigram'),
                        source=source
                    )
                    
                    self.db.add(category_phrase)
                    saved_count += 1
            
            self.db.commit()
            print(f"✅ Saved {saved_count} category trending phrases to database")
            
        except Exception as e:
            self.db.rollback()
            print(f"❌ Error saving category phrases: {e}")
            raise
        
        return saved_count
    
    def get_category_trending_phrases(self, category: str, 
                                    start_date: Optional[date] = None,
                                    end_date: Optional[date] = None,
                                    limit: int = 20) -> List[Dict]:
        """
        Get trending phrases for a specific category
        
        Args:
            category: Category name (e.g., 'রাজনীতি', 'খেলাধুলা')
            start_date: Start date for filtering
            end_date: End date for filtering  
            limit: Maximum number of phrases to return
        
        Returns:
            List of trending phrase dictionaries
        """
        query = self.db.query(CategoryTrendingPhrase).filter(
            CategoryTrendingPhrase.category == category
        )
        
        if start_date:
            query = query.filter(CategoryTrendingPhrase.date >= start_date)
        if end_date:
            query = query.filter(CategoryTrendingPhrase.date <= end_date)
        
        phrases = query.order_by(desc(CategoryTrendingPhrase.score)).limit(limit).all()
        
        return [
            {
                'phrase': p.phrase,
                'score': p.score,
                'frequency': p.frequency,
                'phrase_type': p.phrase_type,
                'date': p.date.isoformat(),
                'category': p.category,
                'source': p.source
            }
            for p in phrases
        ]
    
    def get_top_categories_by_activity(self, analysis_date: Optional[date] = None,
                                     limit: int = 10) -> List[Dict]:
        """
        Get top categories by trending phrase activity
        
        Args:
            analysis_date: Specific date to analyze (default: today)
            limit: Number of top categories to return
        
        Returns:
            List of category activity statistics
        """
        if not analysis_date:
            analysis_date = date.today()
        
        # Get category statistics
        category_stats = self.db.query(
            CategoryTrendingPhrase.category,
            func.count(CategoryTrendingPhrase.id).label('phrase_count'),
            func.avg(CategoryTrendingPhrase.score).label('avg_score'),
            func.sum(CategoryTrendingPhrase.frequency).label('total_frequency')
        ).filter(
            CategoryTrendingPhrase.date == analysis_date
        ).group_by(
            CategoryTrendingPhrase.category
        ).order_by(
            desc('avg_score')
        ).limit(limit).all()
        
        return [
            {
                'category': stat.category,
                'phrase_count': stat.phrase_count,
                'avg_score': float(stat.avg_score or 0),
                'total_frequency': stat.total_frequency or 0
            }
            for stat in category_stats
        ]
    
    def get_category_trends_comparison(self, days: int = 7) -> Dict[str, Dict]:
        """
        Compare category trends over specified number of days
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with category trend comparisons
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get daily category scores
        daily_scores = self.db.query(
            CategoryTrendingPhrase.date,
            CategoryTrendingPhrase.category,
            func.avg(CategoryTrendingPhrase.score).label('daily_avg_score')
        ).filter(
            and_(
                CategoryTrendingPhrase.date >= start_date,
                CategoryTrendingPhrase.date <= end_date
            )
        ).group_by(
            CategoryTrendingPhrase.date,
            CategoryTrendingPhrase.category
        ).all()
        
        # Organize data by category
        category_trends = defaultdict(list)
        for record in daily_scores:
            category_trends[record.category].append({
                'date': record.date.isoformat(),
                'avg_score': float(record.daily_avg_score)
            })
        
        # Calculate trend direction for each category
        trend_analysis = {}
        for category, daily_data in category_trends.items():
            if len(daily_data) >= 2:
                # Sort by date
                daily_data.sort(key=lambda x: x['date'])
                
                # Calculate trend (simple: compare first half vs second half)
                mid_point = len(daily_data) // 2
                first_half_avg = sum(d['avg_score'] for d in daily_data[:mid_point]) / mid_point
                second_half_avg = sum(d['avg_score'] for d in daily_data[mid_point:]) / (len(daily_data) - mid_point)
                
                trend_direction = "increasing" if second_half_avg > first_half_avg else "decreasing"
                trend_strength = abs(second_half_avg - first_half_avg) / max(first_half_avg, 0.1)
                
                trend_analysis[category] = {
                    'daily_data': daily_data,
                    'trend_direction': trend_direction,
                    'trend_strength': trend_strength,
                    'first_half_avg': first_half_avg,
                    'second_half_avg': second_half_avg
                }
        
        return trend_analysis
    
    def categorize_and_save_articles(self, articles: List[Dict]) -> Dict[str, int]:
        """
        Categorize articles and save to database with category information
        
        Args:
            articles: List of article dictionaries with url, title, content
        
        Returns:
            Dictionary with categorization statistics
        """
        stats = defaultdict(int)
        
        try:
            for article_data in articles:
                # Detect category
                category = detect_category_from_url(
                    article_data.get('url', ''),
                    article_data.get('title', ''),
                    article_data.get('content', '') or article_data.get('description', '')
                )
                
                # Create Article instance
                article = Article(
                    title=article_data.get('title', ''),
                    description=article_data.get('content', '') or article_data.get('description', ''),
                    url=article_data.get('url'),
                    published_date=article_data.get('published_date'),
                    source=article_data.get('source', 'unknown'),
                    category=category
                )
                
                self.db.add(article)
                stats[category] += 1
                stats['total'] += 1
            
            self.db.commit()
            print(f"✅ Categorized and saved {stats['total']} articles")
            
        except Exception as e:
            self.db.rollback()
            print(f"❌ Error saving categorized articles: {e}")
            raise
        
        return dict(stats)
    
    def get_category_distribution(self, start_date: Optional[date] = None,
                                end_date: Optional[date] = None) -> Dict[str, int]:
        """
        Get distribution of articles by category
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
        
        Returns:
            Dictionary with category counts
        """
        query = self.db.query(
            Article.category,
            func.count(Article.id).label('count')
        ).filter(
            Article.category.isnot(None)
        )
        
        if start_date:
            query = query.filter(Article.published_date >= start_date)
        if end_date:
            query = query.filter(Article.published_date <= end_date)
        
        results = query.group_by(Article.category).all()
        
        return {result.category: result.count for result in results}
    
    def analyze_category_phrases_by_content(self, articles: List[Dict], 
                                          min_phrase_length: int = 3,
                                          max_phrases_per_category: int = 50) -> Dict[str, List[Dict]]:
        """
        Analyze articles content to extract category-wise trending phrases
        
        Args:
            articles: List of articles with title, content, url
            min_phrase_length: Minimum length for phrases
            max_phrases_per_category: Maximum phrases per category
        
        Returns:
            Dictionary with category as key and trending phrases as value
        """
        from app.routes.helpers import BengaliTextProcessor, TrendingAnalyzer
        
        text_processor = BengaliTextProcessor()
        analyzer = TrendingAnalyzer()
        
        # Group articles by category
        articles_by_category = defaultdict(list)
        
        for article in articles:
            category = detect_category_from_url(
                article.get('url', ''),
                article.get('title', ''),
                article.get('content', '') or article.get('description', '')
            )
            
            # Combine title and content
            full_text = f"{article.get('title', '')} {article.get('content', '') or article.get('description', '')}"
            if full_text.strip():
                articles_by_category[category].append(full_text)
        
        # Analyze each category
        category_phrases = {}
        
        for category, texts in articles_by_category.items():
            if not texts:
                continue
            
            # Combine all texts for this category
            combined_text = " ".join(texts)
            
            # Extract and filter phrases
            phrases = analyzer.filter_quality_phrases(
                {combined_text: len(texts)},
                min_length=min_phrase_length
            )
            
            # Convert to list format and limit
            phrase_list = []
            for phrase, frequency in phrases.items():
                if len(phrase_list) >= max_phrases_per_category:
                    break
                
                phrase_list.append({
                    'phrase': phrase,
                    'frequency': frequency,
                    'score': frequency * len(phrase.split()),  # Simple scoring
                    'phrase_type': 'bigram' if len(phrase.split()) == 2 else 'trigram' if len(phrase.split()) == 3 else 'unigram'
                })
            
            # Sort by score
            phrase_list.sort(key=lambda x: x['score'], reverse=True)
            category_phrases[category] = phrase_list[:max_phrases_per_category]
        
        return category_phrases
