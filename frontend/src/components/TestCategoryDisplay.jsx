import React, { useState } from 'react';

// Mock data for testing
const mockBackendResponse = {
  category_wise_final: {
    "জাতীয়": [
      {"word": "জাতীয় সংবিধান", "frequency": 8, "category": "জাতীয়", "source": "llm_frequency_scoring"},
      {"word": "বাংলাদেশের আনন্দ", "frequency": 7, "category": "জাতীয়", "source": "llm_frequency_scoring"},
      {"word": "সারাদেশে বন্যা", "frequency": 9, "category": "জাতীয়", "source": "llm_frequency_scoring"}
    ],
    "ক্ষুদ্র নৃগোষ্ঠী": [
      {"word": "ক্ষুদ্র নৃগোষ্ঠী", "frequency": 8, "category": "ক্ষুদ্র নৃগোষ্ঠী", "source": "llm_frequency_scoring"},
      {"word": "আদিবাসী সম্প্রদায়", "frequency": 9, "category": "ক্ষুদ্র নৃগোষ্ঠী", "source": "llm_frequency_scoring"},
      {"word": "পার্বত্য জেলা", "frequency": 7, "category": "ক্ষুদ্র নৃগোষ্ঠী", "source": "llm_frequency_scoring"}
    ]
  }
};

function TestCategoryDisplay() {
  const [categoryWiseWords, setCategoryWiseWords] = useState({});
  const [selectedCategoryWords, setSelectedCategoryWords] = useState({});

  const loadMockData = () => {
    console.log("🧪 Loading mock data:", mockBackendResponse.category_wise_final);
    setCategoryWiseWords(mockBackendResponse.category_wise_final);
  };

  const handleCategoryWordSelect = (category, word) => {
    console.log(`🎯 Selected word "${word.word || word}" from category "${category}"`);
    
    setSelectedCategoryWords(prev => {
      const updated = { ...prev };
      
      if (!updated[category]) {
        updated[category] = [];
      }
      
      const wordText = typeof word === 'object' ? word.word : word;
      
      if (Array.isArray(updated[category])) {
        const index = updated[category].findIndex(w => 
          (typeof w === 'object' ? w.word : w) === wordText
        );
        
        if (index >= 0) {
          updated[category].splice(index, 1);
          if (updated[category].length === 0) {
            delete updated[category];
          }
        } else {
          updated[category].push(word);
        }
      }
      
      return updated;
    });
  };

  const getFrequencyBadgeColor = (frequency) => {
    if (frequency >= 8) return '#4CAF50'; // Green for high frequency
    if (frequency >= 6) return '#FF9800';  // Orange for medium frequency
    return '#F44336'; // Red for low frequency
  };

  const cleanCandidate = (candidate) => {
    if (typeof candidate === 'object' && candidate.word) {
      return candidate.word;
    }
    return String(candidate);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-4">Category Display Test</h1>
      
      <button 
        onClick={loadMockData}
        className="bg-blue-500 text-white px-4 py-2 rounded mb-6 hover:bg-blue-600"
      >
        Load Mock Data
      </button>

      <div className="mb-4 p-3 bg-gray-100 rounded">
        <p><strong>Categories loaded:</strong> {Object.keys(categoryWiseWords).length}</p>
        <p><strong>Selected categories:</strong> {Object.keys(selectedCategoryWords).length}</p>
      </div>

      {Object.keys(categoryWiseWords).length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.entries(categoryWiseWords).map(([category, words]) => (
            <div key={category} className="bg-white rounded-lg p-4 border-2 border-gray-200 shadow-lg">
              {/* Category Header */}
              <div className="text-center mb-4 pb-3 border-b-2 border-blue-300">
                <h3 className="font-bold text-lg text-gray-800">{category}</h3>
                <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full">{words.length}টি শব্দ</span>
              </div>
              
              {/* Words for this category */}
              <div className="space-y-3">
                {words.map((word, idx) => {
                  const isSelected = selectedCategoryWords[category] && 
                    selectedCategoryWords[category].some(selectedWord => 
                      (typeof selectedWord === 'object' ? selectedWord.word : selectedWord) === 
                      (typeof word === 'object' ? word.word : word)
                    );
                  
                  // Extract word data if it's an object with frequency info
                  let wordText = word;
                  let wordData = { frequency: 1, source: 'unknown' };
                  
                  if (typeof word === 'object' && word.word) {
                    wordText = word.word;
                    wordData = {
                      frequency: word.frequency || 1,
                      source: word.source || 'unknown'
                    };
                  } else if (typeof word === 'string') {
                    wordText = word;
                  }
                  
                  return (
                    <button
                      key={idx}
                      type="button"
                      className={`w-full text-left px-4 py-3 rounded-lg border-2 text-sm transition-all duration-300 transform relative ${
                        isSelected
                          ? 'bg-blue-600 text-white border-blue-600 shadow-lg scale-105'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-blue-50 hover:border-blue-400 hover:scale-102'
                      }`}
                      onClick={() => handleCategoryWordSelect(category, word)}
                    >
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center ${
                          isSelected ? 'bg-white text-blue-600' : 'bg-gray-200 text-gray-600'
                        }`}>
                          {isSelected ? '✓' : idx + 1}
                        </span>
                        <span className="font-medium flex-1">{cleanCandidate(wordText)}</span>
                        
                        {/* Frequency Badge */}
                        {wordData.frequency > 1 && (
                          <span 
                            className="text-xs font-bold px-2 py-1 rounded-full text-white"
                            style={{ backgroundColor: getFrequencyBadgeColor(wordData.frequency) }}
                          >
                            {wordData.frequency}
                          </span>
                        )}
                        
                        {/* Source Badge */}
                        {wordData.source === 'llm_frequency_scoring' && (
                          <span className="text-xs px-2 py-1 rounded-full bg-purple-600 text-white font-bold">
                            LLM
                          </span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center text-gray-500">
          No category data loaded. Click "Load Mock Data" to test.
        </div>
      )}

      {Object.keys(selectedCategoryWords).length > 0 && (
        <div className="mt-6 p-4 bg-green-50 border border-green-300 rounded-lg">
          <h4 className="font-semibold text-green-800 mb-3">✅ Selected Words:</h4>
          <div className="space-y-2">
            {Object.entries(selectedCategoryWords).map(([category, words]) => (
              <div key={category} className="flex items-center gap-3">
                <span className="font-medium text-green-700">{category}:</span>
                <div className="flex flex-wrap gap-2">
                  {words.map((word, idx) => (
                    <span 
                      key={idx}
                      className="bg-green-200 text-green-800 px-2 py-1 rounded text-sm"
                    >
                      {cleanCandidate(word)}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default TestCategoryDisplay;
