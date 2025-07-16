import React, { useState, useEffect } from 'react';
import './WordDisplay.css'; // CSS file for styling

const CategoryWordDisplay = ({ categoryData }) => {
  const [hoveredWord, setHoveredWord] = useState(null);
  const [wordDetails, setWordDetails] = useState({});

  useEffect(() => {
    // Parse the category data if it comes as objects with frequency info
    if (categoryData) {
      const parsedDetails = {};
      Object.keys(categoryData).forEach(category => {
        parsedDetails[category] = categoryData[category].map(wordInfo => {
          if (typeof wordInfo === 'object' && wordInfo.word) {
            return {
              word: wordInfo.word,
              frequency: wordInfo.frequency || 1,
              category: wordInfo.category || category,
              source: wordInfo.source || 'unknown'
            };
          } else {
            // Fallback for string-only data
            return {
              word: typeof wordInfo === 'string' ? wordInfo : String(wordInfo),
              frequency: 1,
              category: category,
              source: 'fallback'
            };
          }
        });
      });
      setWordDetails(parsedDetails);
    }
  }, [categoryData]);

  const handleWordHover = (word, category, wordData) => {
    setHoveredWord({
      word: word,
      category: category,
      frequency: wordData.frequency,
      source: wordData.source
    });
  };

  const handleWordLeave = () => {
    setHoveredWord(null);
  };

  const getCategoryColor = (category) => {
    const colors = {
      'জাতীয়': '#2196F3',
      'আন্তর্জাতিক': '#4CAF50',
      'অর্থনীতি': '#FF9800',
      'রাজনীতি': '#9C27B0',
      'বিনোদন': '#E91E63',
      'খেলাধুলা': '#00BCD4',
      'শিক্ষা': '#795548',
      'স্বাস্থ্য': '#8BC34A',
      'বিজ্ঞান': '#3F51B5',
      'প্রযুক্তি': '#607D8B',
      'সাহিত্য-সংস্কৃতি': '#FF5722',
      'ক্ষুদ্র নৃগোষ্ঠী': '#009688'
    };
    return colors[category] || '#666666';
  };

  const getFrequencyBadgeColor = (frequency) => {
    if (frequency >= 10) return '#4CAF50'; // Green for high frequency
    if (frequency >= 5) return '#FF9800';  // Orange for medium frequency
    return '#F44336'; // Red for low frequency
  };

  return (
    <div className="category-word-display">
      <h2 className="display-title">আজকের ট্রেন্ডিং শব্দসমূহ</h2>
      
      {Object.keys(wordDetails).map((category, categoryIndex) => (
        <div key={categoryIndex} className="category-section">
          <h3 
            className="category-title"
            style={{ borderColor: getCategoryColor(category) }}
          >
            {category}
            <span className="word-count">({wordDetails[category].length}টি শব্দ)</span>
          </h3>
          
          <div className="words-grid">
            {wordDetails[category].map((wordData, wordIndex) => (
              <div
                key={wordIndex}
                className="word-item"
                onMouseEnter={() => handleWordHover(wordData.word, category, wordData)}
                onMouseLeave={handleWordLeave}
                style={{ borderLeftColor: getCategoryColor(category) }}
              >
                <span className="word-text">{wordData.word}</span>
                
                <div className="word-meta">
                  <span 
                    className="frequency-badge"
                    style={{ backgroundColor: getFrequencyBadgeColor(wordData.frequency) }}
                  >
                    {wordData.frequency}
                  </span>
                  {wordData.source === 'llm_selection' && (
                    <span className="source-badge llm">LLM</span>
                  )}
                  {wordData.source === 'fallback' && (
                    <span className="source-badge fallback">Auto</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Hover Tooltip */}
      {hoveredWord && (
        <div className="hover-tooltip">
          <div className="tooltip-header">
            <strong>{hoveredWord.word}</strong>
            <span className="tooltip-category">({hoveredWord.category})</span>
          </div>
          <div className="tooltip-body">
            <div className="tooltip-row">
              <span className="tooltip-label">আবৃত্তি:</span>
              <span className="tooltip-value">{hoveredWord.frequency} বার</span>
            </div>
            <div className="tooltip-row">
              <span className="tooltip-label">উৎস:</span>
              <span className="tooltip-value">
                {hoveredWord.source === 'llm_selection' ? 'এআই নির্বাচিত' : 
                 hoveredWord.source === 'fallback' ? 'স্বয়ংক্রিয়' : 
                 hoveredWord.source}
              </span>
            </div>
            <div className="tooltip-row">
              <span className="tooltip-label">জনপ্রিয়তা:</span>
              <span className="tooltip-value">
                {hoveredWord.frequency >= 10 ? 'অত্যন্ত জনপ্রিয়' :
                 hoveredWord.frequency >= 5 ? 'মাঝারি জনপ্রিয়' : 'কম জনপ্রিয়'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Usage Example
const App = () => {
  const [trendingData, setTrendingData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrendingWords();
  }, []);

  const fetchTrendingWords = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/generate_candidates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Add authentication headers if needed
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // The data should contain category_wise_final with frequency info
      if (data.category_wise_final) {
        setTrendingData(data.category_wise_final);
      } else {
        console.error('No category_wise_final data found in response');
      }
    } catch (error) {
      console.error('Error fetching trending words:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>ট্রেন্ডিং শব্দ লোড হচ্ছে...</p>
      </div>
    );
  }

  if (!trendingData) {
    return (
      <div className="error-container">
        <p>ট্রেন্ডিং শব্দ লোড করতে সমস্যা হয়েছে।</p>
        <button onClick={fetchTrendingWords}>পুনরায় চেষ্টা করুন</button>
      </div>
    );
  }

  return (
    <div className="app">
      <CategoryWordDisplay categoryData={trendingData} />
    </div>
  );
};

export default App;
