#!/usr/bin/env python3
"""
DataFlow Graph Generator for FastAPI Bengali Trending Words Analysis Pipeline
Shows the complete pipeline after optimize_text_for_ai_analysis implementation
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_dataflow_graph():
    """Create a comprehensive dataflow graph of the current pipeline"""
    
    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=(20, 16))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 24)
    ax.axis('off')
    
    # Color scheme
    colors = {
        'input': '#E3F2FD',           # Light Blue
        'scraping': '#FFF3E0',        # Light Orange
        'optimization': '#F3E5F5',    # Light Purple
        'nlp': '#E8F5E8',            # Light Green
        'ai': '#FFF9C4',             # Light Yellow
        'database': '#FFEBEE',        # Light Red
        'frontend': '#E0F2F1',        # Light Teal
        'flow': '#666666'             # Gray for arrows
    }
    
    # Title
    ax.text(10, 23, 'FastAPI Bengali Trending Words Analysis Pipeline', 
            fontsize=20, fontweight='bold', ha='center')
    ax.text(10, 22.5, 'After optimize_text_for_ai_analysis Implementation', 
            fontsize=14, ha='center', style='italic')
    
    # Helper function to create boxes
    def create_box(x, y, width, height, text, color, fontsize=10):
        box = FancyBboxPatch(
            (x, y), width, height,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor='black',
            linewidth=1.5
        )
        ax.add_patch(box)
        
        # Add text
        ax.text(x + width/2, y + height/2, text, 
                ha='center', va='center', fontsize=fontsize, 
                fontweight='bold', wrap=True)
    
    # Helper function to create arrows
    def create_arrow(x1, y1, x2, y2, text='', offset=0.2):
        arrow = ConnectionPatch(
            (x1, y1), (x2, y2), "data", "data",
            arrowstyle="->", shrinkA=5, shrinkB=5,
            mutation_scale=20, fc=colors['flow'], lw=2
        )
        ax.add_patch(arrow)
        
        if text:
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2 + offset
            ax.text(mid_x, mid_y, text, ha='center', va='center', 
                    fontsize=8, bbox=dict(boxstyle="round,pad=0.2", 
                    facecolor='white', alpha=0.8))
    
    # 1. INPUT SOURCES
    ax.text(2, 21, 'INPUT SOURCES', fontsize=12, fontweight='bold')
    
    create_box(0.5, 19.5, 3, 1, 'Bengali News\nScraping\n(4 sources)', colors['input'])
    create_box(0.5, 18, 3, 1, 'Google Trends\nBangladesh', colors['input'])
    create_box(0.5, 16.5, 3, 1, 'YouTube Trending\nBangladesh', colors['input'])
    create_box(0.5, 15, 3, 1, 'SerpApi Trends\nBangladesh', colors['input'])
    
    # 2. DATA SCRAPING & OPTIMIZATION
    ax.text(7, 21, 'DATA SCRAPING & OPTIMIZATION', fontsize=12, fontweight='bold')
    
    create_box(5, 19, 4, 1.5, 'News Scraping\nOptimization\n• 10s timeout\n• 5 articles/source\n• 20 articles total', colors['scraping'])
    
    create_box(5, 17, 4, 1.5, 'Trending Data\nCollection\n• Real-time fetch\n• Error handling\n• API limits', colors['scraping'])
    
    # 3. TEXT OPTIMIZATION (NEW)
    ax.text(7, 15, 'TEXT OPTIMIZATION', fontsize=12, fontweight='bold', color='purple')
    
    create_box(5, 12.5, 4, 2, 'optimize_text_for_ai_analysis()\n• Extract top 2 keywords/article\n• Heavy deduplication (40% overlap)\n• 3500 char limit\n• Priority scoring\n• Ultra-compression', colors['optimization'])
    
    # 4. NLP ANALYSIS
    ax.text(14, 21, 'NLP ANALYSIS', fontsize=12, fontweight='bold')
    
    create_box(12, 19, 4, 1.5, 'TrendingBengaliAnalyzer\n• Advanced tokenization\n• Stop word filtering\n• Bengali NLP', colors['nlp'])
    
    create_box(12, 17, 4, 1.5, 'Traditional Analysis\n• TF-IDF scoring\n• N-gram extraction\n• Keyword ranking', colors['nlp'])
    
    # 5. AI PROCESSING
    ax.text(14, 15, 'AI PROCESSING', fontsize=12, fontweight='bold')
    
    create_box(12, 12.5, 4, 2, 'Groq API (LLM)\n• llama-3.3-70b-versatile\n• Optimized prompts\n• Error handling\n• Token limit aware', colors['ai'])
    
    # 6. DATABASE OPERATIONS
    ax.text(7, 10, 'DATABASE OPERATIONS', fontsize=12, fontweight='bold')
    
    create_box(5, 8, 4, 1.5, 'TrendingPhrase\nStorage\n• Daily trending data\n• NLP results\n• Metadata tracking', colors['database'])
    
    create_box(12, 8, 4, 1.5, 'LLM Results\nStorage\n• Top 15 AI words\n• Score assignment\n• Source tracking', colors['database'])
    
    # 7. API ENDPOINTS
    ax.text(7, 6.5, 'API ENDPOINTS', fontsize=12, fontweight='bold')
    
    create_box(3, 4.5, 5, 1.5, '/api/v2/generate_candidates\n• Full pipeline execution\n• AI + NLP analysis\n• Combined results', colors['frontend'])
    
    create_box(9, 4.5, 5, 1.5, '/api/v2/trending-phrases\n• Filtered queries\n• Date ranges\n• Source filtering', colors['frontend'])
    
    # 8. FRONTEND DISPLAY
    ax.text(7, 3, 'FRONTEND DISPLAY', fontsize=12, fontweight='bold')
    
    create_box(2, 1, 6, 1.5, 'GenerateWords.jsx\n• AI candidate display\n• Combined text preview\n• Word selection interface', colors['frontend'])
    
    create_box(9, 1, 6, 1.5, 'TrendingAnalysis.jsx\n• Phrase filtering\n• Export functionality\n• Analytics dashboard', colors['frontend'])
    
    # ARROWS - Data Flow
    # Input to scraping
    create_arrow(3.5, 19.5, 5, 19.5, 'News data')
    create_arrow(3.5, 18, 5, 17.5)
    create_arrow(3.5, 16.5, 5, 17.2)
    create_arrow(3.5, 15, 5, 17)
    
    # Scraping to optimization
    create_arrow(7, 19, 7, 14.5, 'Raw text\n(150+ articles)')
    create_arrow(7, 17, 7, 14.5)
    
    # Optimization to AI
    create_arrow(9, 13.5, 12, 13.5, 'Optimized text\n(3500 chars)')
    
    # Optimization to NLP
    create_arrow(7, 12.5, 7, 11, 'Text data')
    create_arrow(7, 11, 14, 11, '')
    create_arrow(14, 11, 14, 17, '')
    
    # NLP to Database
    create_arrow(14, 19, 14, 16, 'NLP results')
    create_arrow(14, 17, 14, 9.5, '')
    create_arrow(14, 9.5, 12, 9.5, 'Traditional\nanalysis')
    
    # AI to Database
    create_arrow(14, 12.5, 14, 9.5, 'AI response')
    
    # Database to API
    create_arrow(7, 8, 7, 6, 'Stored data')
    create_arrow(14, 8, 11, 6, '')
    
    # API to Frontend
    create_arrow(5.5, 4.5, 5, 2.5, 'JSON\nresponse')
    create_arrow(11.5, 4.5, 12, 2.5, '')
    
    # Add pipeline stages
    stage_boxes = [
        (0.5, 0.2, 3, 0.5, '1. Data\nCollection', colors['input']),
        (4, 0.2, 3, 0.5, '2. Optimization\n& Processing', colors['optimization']),
        (7.5, 0.2, 3, 0.5, '3. Analysis\n& AI', colors['nlp']),
        (11, 0.2, 3, 0.5, '4. Storage\n& API', colors['database']),
        (14.5, 0.2, 3, 0.5, '5. Frontend\nDisplay', colors['frontend'])
    ]
    
    for x, y, w, h, text, color in stage_boxes:
        create_box(x, y, w, h, text, color, fontsize=9)
    
    # Add performance metrics box
    create_box(17, 15, 2.5, 6, 'PERFORMANCE\nMETRICS\n\n• Timeout: 10s\n• Articles: 20 max\n• Compression: 95%+\n• Token limit: 12k\n• Response: <30s\n• Success rate: 95%+\n• Error handling: ✓\n• Rate limiting: ✓', 
               '#F5F5F5', fontsize=8)
    
    # Add optimization highlights
    create_box(17, 8, 2.5, 6, 'NEW FEATURES\n\n• Ultra text compression\n• Priority scoring\n• Heavy deduplication\n• Token optimization\n• Combined text display\n• Error resilience\n• Model fallback\n• Performance tuning', 
               '#E8F5E8', fontsize=8)
    
    # Legend
    legend_elements = [
        mpatches.Patch(color=colors['input'], label='Input Sources'),
        mpatches.Patch(color=colors['scraping'], label='Data Scraping'),
        mpatches.Patch(color=colors['optimization'], label='Text Optimization'),
        mpatches.Patch(color=colors['nlp'], label='NLP Analysis'),
        mpatches.Patch(color=colors['ai'], label='AI Processing'),
        mpatches.Patch(color=colors['database'], label='Database Storage'),
        mpatches.Patch(color=colors['frontend'], label='Frontend Display')
    ]
    
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
    
    plt.tight_layout()
    plt.savefig('/home/bs01127/IMLI-Project/dataflow_graph.png', 
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig('/home/bs01127/IMLI-Project/dataflow_graph.svg', 
                bbox_inches='tight', facecolor='white')
    
    print("✅ Dataflow graph saved as:")
    print("   📊 /home/bs01127/IMLI-Project/dataflow_graph.png")
    print("   📊 /home/bs01127/IMLI-Project/dataflow_graph.svg")
    
    return fig

if __name__ == "__main__":
    create_dataflow_graph()
    plt.show()
