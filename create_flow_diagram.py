#!/usr/bin/env python3
"""
Visual Flow Diagram Generator for IMLI Project
Shows the complete flow from data collection to frontend display
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

def create_flow_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # Colors
    data_color = '#E3F2FD'  # Light blue
    process_color = '#FFF3E0'  # Light orange
    llm_color = '#F3E5F5'  # Light purple
    frontend_color = '#E8F5E8'  # Light green
    
    # Title
    ax.text(5, 11.5, 'IMLI Project: Frequency Flow and Prompt Pipeline', 
            fontsize=16, fontweight='bold', ha='center')
    
    # Step 1: Data Sources
    ax.add_patch(Rectangle((0.5, 10), 2, 1, facecolor=data_color, edgecolor='black'))
    ax.text(1.5, 10.5, 'Newspaper Articles\n(Multiple Bengali Sources)', ha='center', va='center', fontsize=9)
    
    ax.add_patch(Rectangle((3, 10), 2, 1, facecolor=data_color, edgecolor='black'))
    ax.text(4, 10.5, 'Reddit Posts\n(Bangladesh Subreddits)', ha='center', va='center', fontsize=9)
    
    # Arrow down
    ax.arrow(2.5, 9.8, 0, -0.6, head_width=0.1, head_length=0.1, fc='black', ec='black')
    
    # Step 2: Initial Processing
    ax.add_patch(Rectangle((1, 8.5), 3, 1, facecolor=process_color, edgecolor='black'))
    ax.text(2.5, 9, 'N-gram Analysis\n(helpers.py)', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Arrow down
    ax.arrow(2.5, 8.3, 0, -0.6, head_width=0.1, head_length=0.1, fc='black', ec='black')
    
    # Step 3: Frequency Calculation
    ax.add_patch(Rectangle((0.5, 7), 4, 1, facecolor=process_color, edgecolor='black'))
    ax.text(2.5, 7.5, 'Frequency Calculation\n• Unigrams, Bigrams, Trigrams\n• TF-IDF Scoring', 
            ha='center', va='center', fontsize=8)
    
    # Arrow down
    ax.arrow(2.5, 6.8, 0, -0.6, head_width=0.1, head_length=0.1, fc='black', ec='black')
    
    # Step 4: Category Grouping
    ax.add_patch(Rectangle((0.5, 5.5), 4, 1, facecolor=process_color, edgecolor='black'))
    ax.text(2.5, 6, 'Category-wise Grouping\n• রাজনীতি, অর্থনীতি, খেলাধুলা\n• Preserve frequency data', 
            ha='center', va='center', fontsize=8)
    
    # Arrow right to LLM
    ax.arrow(4.7, 6, 0.6, 0, head_width=0.1, head_length=0.1, fc='black', ec='black')
    
    # Step 5: Reddit LLM Analysis
    ax.add_patch(Rectangle((5.5, 8.5), 3.5, 1.5, facecolor=llm_color, edgecolor='black'))
    ax.text(7.25, 9.25, 'PROMPT 1: Reddit Analysis\n(Per Subreddit)\n• Extract 2 trending words\n• Bengali analysis', 
            ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Arrow down from Reddit LLM
    ax.arrow(7.25, 8.3, 0, -1.6, head_width=0.1, head_length=0.1, fc='black', ec='black')
    
    # Step 6: Main LLM Selection
    ax.add_patch(Rectangle((5.5, 5.5), 3.5, 1.5, facecolor=llm_color, edgecolor='black'))
    ax.text(7.25, 6.25, 'PROMPT 2: Final Selection\n• Select top 10 per category\n• Quality filtering\n• Context relevance', 
            ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Arrow down
    ax.arrow(7.25, 5.3, 0, -0.6, head_width=0.1, head_length=0.1, fc='black', ec='black')
    
    # Step 7: Frequency Attachment
    ax.add_patch(Rectangle((5.5, 4), 3.5, 1, facecolor=process_color, edgecolor='black'))
    ax.text(7.25, 4.5, 'Frequency Attachment\n• Lookup original frequency\n• Count in articles\n• Default to 1', 
            ha='center', va='center', fontsize=8)
    
    # Arrow down
    ax.arrow(7.25, 3.8, 0, -0.6, head_width=0.1, head_length=0.1, fc='black', ec='black')
    
    # Step 8: Final Data Structure
    ax.add_patch(Rectangle((5.5, 2.5), 3.5, 1, facecolor=process_color, edgecolor='black'))
    ax.text(7.25, 3, 'Final Data Structure\n{word, frequency, category}', 
            ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Arrow down
    ax.arrow(7.25, 2.3, 0, -0.6, head_width=0.1, head_length=0.1, fc='black', ec='black')
    
    # Step 9: Frontend Display
    ax.add_patch(Rectangle((5.5, 1), 3.5, 1, facecolor=frontend_color, edgecolor='black'))
    ax.text(7.25, 1.5, 'Frontend Display\n• Frequency badges\n• Bengali tooltips\n• Hover interactions', 
            ha='center', va='center', fontsize=8)
    
    # Frequency Flow Details (Left side)
    ax.text(0.5, 3.5, 'FREQUENCY CALCULATION METHODS:', fontsize=10, fontweight='bold')
    ax.text(0.5, 3.2, '1. Direct Lookup: From category_wise_trending', fontsize=8)
    ax.text(0.5, 2.9, '2. Article Counting: Count in headlines', fontsize=8)
    ax.text(0.5, 2.6, '3. Default Value: frequency = 1', fontsize=8)
    
    ax.text(0.5, 2.1, 'WHY FREQUENCY = 1:', fontsize=10, fontweight='bold')
    ax.text(0.5, 1.8, '• LLM generates new relevant words', fontsize=8)
    ax.text(0.5, 1.5, '• Better synonyms chosen', fontsize=8)
    ax.text(0.5, 1.2, '• Cross-source data mismatch', fontsize=8)
    ax.text(0.5, 0.9, '• N-gram processing limitations', fontsize=8)
    
    # Legend
    legend_elements = [
        mpatches.Patch(color=data_color, label='Data Sources'),
        mpatches.Patch(color=process_color, label='Processing Steps'),
        mpatches.Patch(color=llm_color, label='LLM Prompts'),
        mpatches.Patch(color=frontend_color, label='Frontend Display')
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.3))
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    fig = create_flow_diagram()
    plt.savefig('/home/bs01127/IMLI-Project/frequency_flow_diagram.png', 
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    print("✅ Flow diagram saved as 'frequency_flow_diagram.png'")
