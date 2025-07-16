import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiV2, api } from '../api';
import { RefreshCw, Sparkles, Check, GripVertical } from 'lucide-react';

function GenerateWords() {
  const [loading, setLoading] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [aiCandidates, setAiCandidates] = useState('');
  const [selectedWord, setSelectedWord] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [candidateHeight, setCandidateHeight] = useState(500);
  const [isResizing, setIsResizing] = useState(false);
  
  // Hybrid approach states
  const [sources, setSources] = useState(['newspaper', 'reddit']);
  const [mode, setMode] = useState('sequential'); // Default to sequential
  const [hybridResults, setHybridResults] = useState(null);
  const [showMergePrompt, setShowMergePrompt] = useState(false);
  
  // Category-wise selection states
  const [categoryWiseWords, setCategoryWiseWords] = useState({});
  const [selectedCategoryWords, setSelectedCategoryWords] = useState({});
  const [finalSelectedWords, setFinalSelectedWords] = useState([]);
  
  // Frequency hover states
  const [hoveredWord, setHoveredWord] = useState(null);
  const [hoveredWordData, setHoveredWordData] = useState(null);
  
  // Source selection handlers
  const handleSourceChange = (source) => {
    setSources(prev => 
      prev.includes(source) 
        ? prev.filter(s => s !== source)
        : [...prev, source]
    );
  };
  
  // Frequency hover handlers
  const handleWordHover = (word, category, wordData) => {
    setHoveredWord(`${category}_${word}`);
    setHoveredWordData({
      word: word,
      category: category,
      frequency: wordData?.frequency || 1,
      source: wordData?.source || 'unknown'
    });
  };

  const handleWordLeave = () => {
    setHoveredWord(null);
    setHoveredWordData(null);
  };

  const getFrequencyBadgeColor = (frequency) => {
    if (frequency >= 10) return '#4CAF50'; // Green for high frequency
    if (frequency >= 5) return '#FF9800';  // Orange for medium frequency
    return '#F44336'; // Red for low frequency
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
      'ক্ষুদ্র নৃগোষ্ঠী': '#009688',
      'trivia': '#9E9E9E',
      'sports': '#00BCD4',
      'web-stories': '#E91E63',
      'islam': '#8BC34A',
      'job': '#795548',
      'picture': '#FF5722',
      'op-ed': '#9C27B0',
      'adda': '#607D8B',
      'women': '#E91E63',
      'science': '#3F51B5',
      'environment': '#4CAF50',
      'analysis': '#9C27B0',
      'education': '#795548',
      'health': '#8BC34A',
      'technology': '#607D8B'
    };
    return colors[category] || '#666666';
  };
  
  const navigate = useNavigate();
  const resizeRef = useRef(null);

  const runAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Use hybrid approach but maintain original response format
      const response = await apiV2.hybridGenerateCandidates({
        sources: sources,
        mode: mode
      });
      
      setAnalysisComplete(true);
      setHybridResults(response.data);
      
      // Debug log to check response structure
      console.log("=== Backend Response Debug ===");
      console.log("Full response:", response);
      console.log("Response status:", response.status);
      console.log("Response data exists:", !!response.data);
      console.log("Full response.data:", response.data);
      
      // Safe property access with null checks
      if (response.data) {
        console.log("merge_prompt:", response.data.merge_prompt || 'N/A');
        console.log("final_llm_response:", response.data.final_llm_response || 'N/A');
        console.log("merge_statistics:", response.data.merge_statistics || 'N/A');
      } else {
        console.log("⚠️ response.data is null or undefined!");
      }
      console.log("=== End Debug ===");
      
      // Create comprehensive response including individual source responses
      let candidatesText = '';
      
      // Add individual source responses with null checks
      if (response.data && response.data.results) {
        candidatesText += "🔍 উৎস-ভিত্তিক বিশ্লেষণ:\n";
        candidatesText += "=" + "=".repeat(50) + "\n\n";
        
        for (const [source, result] of Object.entries(response.data.results)) {
          if (source === 'newspaper') {
            candidatesText += "📰 সংবাদপত্র বিশ্লেষণ (ক্যাটেগরি-ভিত্তিক):\n";
            candidatesText += "-".repeat(40) + "\n";
            
            // Show category-wise analysis
            if (result.category_wise_trending) {
              candidatesText += "📂 ক্যাটেগরি-ভিত্তিক ট্রেন্ডিং শব্দ:\n\n";
              
              for (const [category, words] of Object.entries(result.category_wise_trending)) {
                if (words && words.length > 0) {
                  candidatesText += `🔸 ${category}:\n`;
                  words.forEach((word, idx) => {
                    candidatesText += `   ${idx + 1}. ${word}\n`;
                  });
                  candidatesText += "\n";
                } else {
                  candidatesText += `⚠️ ${category}: কোনো শব্দ পাওয়া যায়নি\n\n`;
                }
              }
            }
            
            // Summary statistics
            if (result.scraping_info) {
              candidatesText += "📊 সংবাদপত্র পরিসংখ্যান:\n";
              candidatesText += `   - মোট স্ক্র্যাপ করা আর্টিকেল: ${result.scraping_info.total_articles}\n`;
              candidatesText += `   - মোট ট্রেন্ডিং শব্দ: ${result.trending_words ? result.trending_words.length : 0}\n\n`;
            }
            
          } else if (source === 'reddit') {
            candidatesText += "📡 Reddit বিশ্লেষণ:\n";
            candidatesText += "-".repeat(30) + "\n";
            
            // Show Reddit trending words
            if (result.trending_words && result.trending_words.length > 0) {
              candidatesText += "🔥 Reddit ট্রেন্ডিং শব্দ:\n";
              result.trending_words.forEach((word, idx) => {
                candidatesText += `   ${idx + 1}. ${word}\n`;
              });
              candidatesText += "\n";
            }
            
            // Show subreddit results if available
            if (result.subreddit_results && result.subreddit_results.length > 0) {
              candidatesText += "📋 সাবরেডিট-ভিত্তিক বিশ্লেষণ:\n";
              result.subreddit_results.forEach((subResult, idx) => {
                if (subResult.status === 'success' && subResult.emerging_word) {
                  candidatesText += `   r/${subResult.subreddit}: ${subResult.emerging_word}\n`;
                }
              });
              candidatesText += "\n";
            }
          }
          candidatesText += "=".repeat(60) + "\n\n";
        }
      }
      
      // Add final merged analysis with category-wise display
      if (response.data && response.data.category_wise_final && Object.keys(response.data.category_wise_final).length > 0) {
        candidatesText += "🎯 ক্যাটেগরি অনুযায়ী চূড়ান্ত ট্রেন্ডিং শব্দ (৫টি করে):\n";
        candidatesText += "=" + "=".repeat(50) + "\n\n";
        
        // Show LLM selection statistics if available  
        if (response.data.llm_selection) {
          candidatesText += "📊 LLM নির্বাচন পরিসংখ্যান:\n";
          candidatesText += `   - মোট ইনপুট ক্যাটেগরি: ${response.data.llm_selection.total_input_categories || 0}\n`;
          candidatesText += `   - মোট ইনপুট শব্দ: ${response.data.llm_selection.total_input_words || 0}\n`;
          candidatesText += `   - চূড়ান্ত নির্বাচিত শব্দ: ${response.data.llm_selection.selected_words || 0}\n`;
          candidatesText += `   - প্রক্রিয়াকৃত ক্যাটেগরি: ${response.data.llm_selection.categories_processed || 0}\n`;
          candidatesText += `   - নির্বাচন পদ্ধতি: ${response.data.llm_selection.selection_method || 'N/A'}\n`;
          candidatesText += "\n";
        }
        
        // Display category-wise results
        Object.entries(response.data.category_wise_final).forEach(([category, words]) => {
          if (words && words.length > 0) {
            candidatesText += `🏷️ ${category}:\n`;
            words.forEach((word, index) => {
              candidatesText += `   ${index + 1}. ${word}\n`;
            });
            candidatesText += "\n";
          }
        });
        
        // Show raw LLM response if available for debugging
        if (response.data && response.data.llm_response) {
          candidatesText += "\n" + "=".repeat(50) + "\n";
          candidatesText += "🤖 LLM চূড়ান্ত প্রতিক্রিয়া:\n";
          candidatesText += "-".repeat(30) + "\n";
          candidatesText += response.data.llm_response;
        }
        
      } else if (response.data && response.data.final_trending_words && response.data.final_trending_words.length > 0) {
        candidatesText += "🎯 চূড়ান্ত সমন্বিত ট্রেন্ডিং শব্দ:\n";
        candidatesText += "=" + "=".repeat(45) + "\n\n";
        
        candidatesText += "🏆 ট্রেন্ডিং শব্দ/বাক্যাংশ:\n";
        candidatesText += "-".repeat(40) + "\n";
        response.data.final_trending_words.forEach((word, index) => {
          candidatesText += `${index + 1}. ${word}\n`;
        });
        
        // Show raw LLM response if available for debugging
        if (response.data && response.data.llm_response) {
          candidatesText += "\n" + "=".repeat(50) + "\n";
          candidatesText += "🤖 LLM চূড়ান্ত প্রতিক্রিয়া:\n";
          candidatesText += "-".repeat(30) + "\n";
          candidatesText += response.data.llm_response;
        }
        
      } else if (response.data && response.data.llm_response) {
        candidatesText += "🎯 চূড়ান্ত LLM প্রতিক্রিয়া:\n";
        candidatesText += "-".repeat(25) + "\n";
        candidatesText += response.data.llm_response;
      } else {
        candidatesText = 'কোনো ট্রেন্ডিং শব্দ পাওয়া যায়নি';
      }
      
      setAiCandidates(candidatesText);
      
      // Parse category-wise words for selection
      const categoryWords = parseCategoryWiseWords(candidatesText);
      setCategoryWiseWords(categoryWords);
      
    } catch (err) {
      let msg = 'বিশ্লেষণ চালাতে ব্যর্থ';
      if (err.response && err.response.data && err.response.data.detail) {
        msg += `: ${err.response.data.detail}`;
      }
      setError(msg);
      setAnalysisComplete(false);
      setAiCandidates('');
      setHybridResults(null);
      console.error('Hybrid analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Utility to clean candidates - only remove excessive formatting, preserve meaningful text
  const cleanCandidate = (candidate) => {
    // Convert object to string if needed
    if (typeof candidate === 'object' && candidate.word) {
      candidate = candidate.word;
    }
    
    // Only remove excessive formatting, preserve the actual content
    let cleaned = candidate
      .replace(/^[\d\u09E6-\u09EF]+[.)]\s*/u, '') // Remove only the number prefix (1. 2. etc.)
      .replace(/^(\u09a1\.|\u09a1\u0983|\u09a1:)[\s\-–—]*/u, '') // Remove Bengali "Dr." titles  
      .trim();
    
    return cleaned;
  };

  // Handle resize functionality
  const handleMouseDown = (e) => {
    setIsResizing(true);
    e.preventDefault();
  };

  const handleMouseMove = (e) => {
    if (!isResizing) return;
    
    const newHeight = e.clientY - resizeRef.current.offsetTop;
    if (newHeight >= 300 && newHeight <= 1200) { // Min 300px, Max 1200px for better content viewing
      setCandidateHeight(newHeight);
    }
  };

  const handleMouseUp = () => {
    setIsResizing(false);
  };

  // Add global event listeners for resize
  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'ns-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const finalWords = generateFinalWordsList();
    
    if (finalWords.length === 0 && !selectedWord.trim()) {
      setError('অন্তত একটি শব্দ নির্বাচন করুন');
      return;
    }
    
    try {
      setSubmitting(true);
      setError(null);
      
      // If category words are selected, use them; otherwise use the manual input
      if (finalWords.length > 0) {
        // Use the existing setCategoryWords method
        const response = await apiV2.setCategoryWords(finalWords);
        
        console.log('Category words saved successfully:', response.data);
        setFinalSelectedWords(finalWords);
      } else if (selectedWord.trim()) {
        const sanitizedWord = cleanCandidate(selectedWord);
        await api.setWordOfTheDay(sanitizedWord);
        // Create single word info for manual selection
        setFinalSelectedWords([{ word: sanitizedWord, category: 'ম্যানুয়াল নির্বাচন', originalText: selectedWord }]);
      }
      
      setSuccess(true);
      setTimeout(() => {
        navigate('/');
      }, 2000);
      
    } catch (err) {
      setError('শব্দ সেট করতে ব্যর্থ হয়েছে');
      console.error('Submit error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  // Parse category-wise words from AI response - prioritize direct dictionary approach
  const parseCategoryWiseWords = (candidatesText) => {
    if (!candidatesText) return {};
    
    // FIRST PRIORITY: Use direct category_wise_final dictionary from backend (as requested)
    if (hybridResults && hybridResults.category_wise_final) {
      console.log("✅ Using category_wise_final dictionary from backend:", hybridResults.category_wise_final);
      return hybridResults.category_wise_final;
    }
    
    // FALLBACK: Parse from text if dictionary not available
    console.log("⚠️ Falling back to text parsing...");
    let categoryWords = {};
    const lines = candidatesText.split('\n');
    
    console.log("=== Parsing Category-wise Words ===");
    
    // Look for category-wise final results section
    let inCategorySection = false;
    let currentCategory = null;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();
      
      // Look for category-wise section
      if (trimmed.includes('ক্যাটেগরি অনুযায়ী চূড়ান্ত ট্রেন্ডিং শব্দ')) {
        inCategorySection = true;
        console.log("Found category section at line:", i);
        continue;
      }
      
      // If in category section, look for category headers (🏷️ format)
      if (inCategorySection && trimmed.includes('🏷️')) {
        const categoryMatch = trimmed.match(/🏷️\s*(.+?):/);
        if (categoryMatch) {
          currentCategory = categoryMatch[1].trim();
          categoryWords[currentCategory] = [];
          console.log("Found category:", currentCategory);
        }
        continue;
      }
      
      // If in category section and we have a current category, extract numbered items
      if (inCategorySection && currentCategory && (/^\s*\d+\.\s/.test(trimmed) || /^\s*[১-৯০]+\.\s/.test(trimmed))) {
        let cleanedLine = trimmed
          .replace(/^\s*\d+\.\s*/, '') // Remove English numbers
          .replace(/^\s*[১-৯০]+\.\s*/, '') // Remove Bengali numbers  
          .replace(/^\[/, '').replace(/\]$/, '') // Remove brackets
          .trim();
          
        if (cleanedLine.length > 1 && /[\u0980-\u09FF]/.test(cleanedLine)) {
          categoryWords[currentCategory].push(cleanedLine);
          console.log(`Added to ${currentCategory}:`, cleanedLine);
        }
      }
      
      // Stop if we hit another major section
      if (inCategorySection && (trimmed.includes('📊 LLM') || trimmed.includes('🤖 LLM'))) {
        break;
      }
    }
    
    console.log("Final category-wise words from text parsing:", categoryWords);
    console.log("=== End Category Parsing ===");
    
    return categoryWords;
  };

  // Helper to count total selected words
  const getTotalSelectedWords = () => {
    return Object.values(selectedCategoryWords).reduce((total, words) => {
      return total + (Array.isArray(words) ? words.length : (words ? 1 : 0));
    }, 0);
  };

  // Helper to count selected categories
  const getSelectedCategoriesCount = () => {
    return Object.keys(selectedCategoryWords).filter(category => {
      const words = selectedCategoryWords[category];
      return Array.isArray(words) ? words.length > 0 : !!words;
    }).length;
  };

  // Handle category word selection - supports multiple words per category
  const handleCategoryWordSelect = (category, word) => {
    setSelectedCategoryWords(prev => {
      const currentWords = prev[category] || [];
      
      // If word is already selected, remove it (toggle off)
      if (currentWords.includes(word)) {
        const updatedWords = currentWords.filter(w => w !== word);
        if (updatedWords.length === 0) {
          const { [category]: _, ...rest } = prev;
          return rest;
        }
        return { ...prev, [category]: updatedWords };
      } else {
        // Add word to category (toggle on)
        return { ...prev, [category]: [...currentWords, word] };
      }
    });
    // Clear manual input when category selection is made
    setSelectedWord('');
  };

  // Generate final selected words list with category tracking - supports multiple words
  const generateFinalWordsList = () => {
    const selectedWords = [];
    Object.entries(selectedCategoryWords).forEach(([category, words]) => {
      // Handle both single word and array of words
      const wordArray = Array.isArray(words) ? words : [words];
      wordArray.forEach(word => {
        selectedWords.push({
          word: cleanCandidate(word),
          category: category,
          originalText: word
        });
      });
    });
    setFinalSelectedWords(selectedWords);
    return selectedWords;
  };

  const parseCandidates = (candidatesText) => {
    if (!candidatesText) return [];
    
    let keywords = [];
    const lines = candidatesText.split('\n');
    
    // Debug log
    console.log("=== Parsing Candidates for Quick Selection ===");
    console.log("Total lines:", lines.length);
    
    // Priority 1: Try to extract from category-wise final results (🏷️ format)
    let inCategorySection = false;
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();
      
      // Look for category-wise section
      if (trimmed.includes('🏷️') || (trimmed.includes('ক্যাটেগরি অনুযায়ী') && trimmed.includes('চূড়ান্ত'))) {
        inCategorySection = true;
        console.log("Found category section at line:", i, "->", trimmed);
        continue;
      }
      
      // If in category section, extract numbered items
      if (inCategorySection && (/^\s*\d+\.\s/.test(trimmed) || /^\s*[১-৯০]+\.\s/.test(trimmed))) {
        let cleanedLine = trimmed
          .replace(/^\s*\d+\.\s*/, '') // Remove English numbers
          .replace(/^\s*[১-৯০]+\.\s*/, '') // Remove Bengali numbers  
          .replace(/^\[/, '').replace(/\]$/, '') // Remove brackets
          .trim();
          
        if (cleanedLine.length > 1 && /[\u0980-\u09FF]/.test(cleanedLine)) {
          keywords.push(cleanedLine);
          console.log("Added from category section:", cleanedLine);
        }
      }
      
      // Stop if we hit another major section or reach end of category section
      if (inCategorySection && (trimmed.includes('='*10) || trimmed.includes('📊 LLM') || trimmed.includes('🤖 LLM'))) {
        break;
      }
    }
    
    // Priority 2: If no category-wise results, look for final trending words section
    if (keywords.length === 0) {
      console.log("No category results found, looking for final trending words...");
      let inFinalSection = false;
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();
        
        // Look for final trending words section
        if (trimmed.includes('চূড়ান্ত ট্রেন্ডিং শব্দ') || trimmed.includes('🎯') || trimmed.includes('🏆 ট্রেন্ডিং শব্দ')) {
          inFinalSection = true;
          console.log("Found final section at line:", i, "->", trimmed);
          continue;
        }
        
        // Extract numbered items from final section
        if (inFinalSection && (/^\d+\.\s/.test(trimmed) || /^[১-৯০]+\.\s/.test(trimmed))) {
          let cleanedLine = trimmed
            .replace(/^\d+\.\s*/, '') // Remove English numbers
            .replace(/^[১-৯০]+\.\s*/, '') // Remove Bengali numbers  
            .replace(/^\[/, '').replace(/\]$/, '') // Remove brackets
            .trim();
            
          if (cleanedLine.length > 1 && /[\u0980-\u09FF]/.test(cleanedLine)) {
            keywords.push(cleanedLine);
            console.log("Added from final section:", cleanedLine);
          }
        }
        
        // Stop if we hit another major section  
        if (inFinalSection && (trimmed.includes('='*10) || trimmed.includes('🤖 LLM'))) {
          break;
        }
      }
    }
    
    // Priority 3: Look for any numbered Bengali words (fallback)
    if (keywords.length === 0) {
      console.log("No final section found, trying fallback parsing...");
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();
        
        // Look for numbered items that contain Bengali words
        if ((/^\d+\.\s*/.test(trimmed) || /^[১-৯০]+\.\s*/.test(trimmed)) && /[\u0980-\u09FF]/.test(trimmed)) {
          let cleanedLine = trimmed
            .replace(/^\d+\.\s*/, '')
            .replace(/^[১-৯০]+\.\s*/, '')
            .replace(/^["'](.+)["']$/, '$1')
            .trim();
          
          console.log("Fallback found:", trimmed, "-> cleaned:", cleanedLine);
          
          if (cleanedLine.length > 1 && 
              !cleanedLine.includes('❌') && 
              !cleanedLine.includes('Error') &&
              !cleanedLine.includes('Saved LLM trending word')) {
            keywords.push(cleanedLine);
            console.log("Added fallback keyword:", cleanedLine);
          }
        }
      }
    }
    
    // Priority 4: Use direct results from API response if parsing failed
    if (keywords.length === 0 && hybridResults) {
      if (hybridResults.final_trending_words && hybridResults.final_trending_words.length > 0) {
        console.log("Using fallback from hybridResults.final_trending_words");
        keywords = hybridResults.final_trending_words.slice(0, 15);
      } else if (hybridResults.category_wise_final) {
        console.log("Using fallback from hybridResults.category_wise_final");
        Object.values(hybridResults.category_wise_final).forEach(words => {
          if (Array.isArray(words)) {
            keywords.push(...words);
          }
        });
      }
    }
    
    // Remove duplicates and limit to 15
    keywords = [...new Set(keywords)];
    console.log("Final parsed candidates:", keywords);
    console.log("=== End Debug ===");
    return keywords.slice(0, 15); // Show max 15 words for quick selection
  };

  if (success) {
    const finalWords = finalSelectedWords.length > 0 ? finalSelectedWords : [{ word: selectedWord, category: 'ম্যানুয়াল নির্বাচন' }];
    
    return (
      <div className="container mx-auto px-4 py-12 bg-white min-h-[calc(100vh-4rem)] flex flex-col justify-center items-center">
        <div className="bg-green-100 border border-green-300 text-green-800 px-4 py-6 rounded mb-6 text-center max-w-2xl w-full">
          <h2 className="text-xl font-bold mb-2">সফলভাবে সম্পন্ন!</h2>
          <p className="mb-3">আজকের শব্দ নির্ধারণ করা হয়েছে:</p>
          <div className="space-y-2">
            {finalWords.map((wordInfo, idx) => (
              <div key={idx} className="bg-white p-3 rounded border border-green-200">
                <span className="font-semibold text-lg">{wordInfo.word}</span>
                <div className="text-sm text-gray-600 mt-1">
                  ক্যাটেগরি: <span className="font-medium">{wordInfo.category}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        <svg className="animate-spin h-12 w-12 text-green-500 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
        <p className="mt-4 text-gray-700">হোম পেজে ফিরে যাচ্ছি...</p>
      </div>
    );
  }

  return (
    <div className={`container mx-auto px-4 py-12 bg-white min-h-[calc(100vh-4rem)] flex flex-col justify-center ${isResizing ? 'select-none' : ''}`}>
      <div className="text-center mb-10">
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-gray-900 mb-2 flex items-center justify-center gap-2">
          <Sparkles className="w-8 h-8 text-pink-500" /> ট্রেন্ডিং শব্দ উৎপাদন
        </h1>
      </div>

     

      {error && (
        <div className="bg-red-100 border border-red-300 text-red-800 px-4 py-3 rounded mb-6 text-center max-w-md mx-auto">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto">
        <div className="bg-white shadow-md rounded-lg p-8 flex flex-col justify-between items-center text-center">
          <h2 className="text-xl font-semibold mb-2">১. বিশ্লেষণ চালান</h2>
          <p className="text-gray-600 mb-4">
            Newspaper এবং Social Media থেকে ট্রেন্ডিং শব্দ বিশ্লেষণ করুন
          </p>
          <button
            className={`w-full flex items-center justify-center gap-2 px-6 py-2 rounded font-semibold text-white transition ${loading || sources.length === 0 ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'} shadow`}
            onClick={runAnalysis}
            disabled={loading || sources.length === 0}
          >
            {loading ? (
              <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
            ) : (
              <RefreshCw className="w-5 h-5" />
            )}
            {loading ? 'বিশ্লেষণ চলছে...' : 'বিশ্লেষণ শুরু করুন'}
          </button>
          {sources.length === 0 && (
            <div className="bg-yellow-100 border border-yellow-300 text-yellow-800 px-4 py-2 rounded mt-4 text-center w-full">
              ⚠️ অন্তত একটি সোর্স নির্বাচন করুন
            </div>
          )}
          {analysisComplete && (
            <div className="bg-green-100 border border-green-300 text-green-800 px-4 py-2 rounded mt-4 text-center w-full">
              <span className="mr-2">✅</span> ফাইনাল ট্রেন্ডিং শব্দ তৈরি হয়েছে।
            </div>
          )}
        </div>
        
        {/* Test Button for Category Display */}
        
        
        <div className="bg-white shadow-md rounded-lg p-8 flex flex-col justify-between items-center text-center">
          <h2 className="text-xl font-semibold mb-2">২. শব্দ নির্বাচন</h2>
          <p className="text-gray-600 mb-4">
            ক্যাটেগরি অনুযায়ী শব্দ নির্বাচন করুন অথবা ম্যানুয়ালি একটি শব্দ টাইপ করুন
          </p>
          {getTotalSelectedWords() > 0 && (
            <div className="bg-green-100 border border-green-300 text-green-800 px-3 py-2 rounded mb-4 text-center w-full text-sm">
              ✅ {getSelectedCategoriesCount()}টি ক্যাটেগরি থেকে মোট {getTotalSelectedWords()}টি শব্দ নির্বাচিত
            </div>
          )}
          <form onSubmit={handleSubmit} className="w-full">
            <input
              type="text"
              className="w-full border border-gray-300 rounded px-4 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-pink-400"
              placeholder="অথবা ম্যানুয়ালি একটি শব্দ টাইপ করুন..."
              value={selectedWord}
              onChange={e => {
                setSelectedWord(e.target.value);
                // Clear category selections if manual input is used
                if (e.target.value.trim()) {
                  setSelectedCategoryWords({});
                }
              }}
              disabled={submitting}
            />
            <button
              type="submit"
              className={`w-full flex items-center justify-center gap-2 px-6 py-2 rounded font-semibold text-white transition ${
                (getTotalSelectedWords() === 0 && !selectedWord.trim()) || submitting 
                  ? 'bg-gray-400' 
                  : 'bg-pink-600 hover:bg-pink-700'
              } shadow`}
              disabled={(getTotalSelectedWords() === 0 && !selectedWord.trim()) || submitting}
            >
              {submitting ? (
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
              ) : (
                <Check className="w-5 h-5" />
              )}
              {submitting ? 'সেট করা হচ্ছে...' : 
                getTotalSelectedWords() > 0 
                  ? `নির্বাচিত শব্দ সেট করুন (${getTotalSelectedWords()}টি)`
                  : 'আজকের শব্দ নির্ধারণ করুন'
              }
            </button>
          </form>
        </div>
      </div>

      {analysisComplete && aiCandidates && (
        <div className="mt-10 max-w-6xl mx-auto">
          {/* Category-wise word selection */}
          {Object.keys(categoryWiseWords).length > 0 ? (
            <div className="bg-white shadow-lg rounded-lg p-6 mb-6 border-2 border-gray-200">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold flex items-center gap-2">
                  <Sparkles className="w-6 h-6 text-yellow-500" />
                  দ্রুত শব্দ নির্বাচন - প্রতি ক্যাটেগরি থেকে ১০টি শব্দ
                </h2>
                <div className="text-sm text-gray-500 bg-green-100 px-3 py-1 rounded-full">
                  নির্বাচিত: {getSelectedCategoriesCount()}/{Object.keys(categoryWiseWords).length} (মোট {getTotalSelectedWords()}টি শব্দ)
                </div>
              </div>
              
              <div className="mb-4 p-4 bg-blue-50 border-l-4 border-blue-400 rounded">
                <p className="text-blue-800 font-medium text-sm">
                  📋 প্রতিটি ক্যাটেগরি থেকে একটি করে শব্দ নির্বাচন করুন (প্রতি কলামে ১০টি শব্দ থেকে নির্বাচন)
                </p>
                <p className="text-blue-600 text-xs mt-1">
                  💡 নির্বাচিত শব্দগুলো ক্যাটেগরি তথ্যসহ সংরক্ষিত হবে
                </p>
              </div>

              {/* Category columns - Each category in separate column with 5 words */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                {Object.entries(categoryWiseWords).map(([category, words]) => (
                  <div key={category} className="bg-gradient-to-b from-gray-50 to-gray-100 rounded-lg p-4 border-2 border-gray-200 shadow-lg hover:shadow-xl transition-all duration-200">
                    {/* Category Header */}
                    <div className="text-center mb-4 pb-3 border-b-2 border-blue-300">
                      <h3 className="font-bold text-lg text-gray-800">{category}</h3>
                      <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full">১০টি শব্দ</span>
                    </div>
                    
                    {/* 10 Words for this category */}
                    <div className="space-y-3">
                      {words.slice(0, 10).map((word, idx) => {
                        const isSelected = selectedCategoryWords[category] && 
                          (Array.isArray(selectedCategoryWords[category]) 
                            ? selectedCategoryWords[category].includes(word)
                            : selectedCategoryWords[category] === word);
                        
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
                            onMouseEnter={() => handleWordHover(wordText, category, wordData)}
                            onMouseLeave={handleWordLeave}
                            title={`"${category}" ক্যাটেগরি থেকে "${cleanCandidate(wordText)}" ${isSelected ? 'অপসারণ' : 'নির্বাচন'} করুন`}
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
                              {wordData.source === 'llm_selection' && (
                                <span className="text-xs px-2 py-1 rounded-full bg-purple-600 text-white font-bold">
                                  LLM
                                </span>
                              )}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                    
                    {/* Selection status */}
                    <div className="mt-4 text-center">
                      {selectedCategoryWords[category] && 
                       ((Array.isArray(selectedCategoryWords[category]) && selectedCategoryWords[category].length > 0) ||
                        (!Array.isArray(selectedCategoryWords[category]) && selectedCategoryWords[category])) ? (
                        <div className="bg-green-100 border border-green-300 rounded-lg p-2">
                          <span className="text-xs bg-green-200 text-green-700 px-2 py-1 rounded-full font-medium">
                            ✓ নির্বাচিত ({Array.isArray(selectedCategoryWords[category]) 
                              ? selectedCategoryWords[category].length 
                              : 1})
                          </span>
                          <div className="text-xs text-green-800 mt-1 font-semibold max-h-16 overflow-y-auto">
                            {Array.isArray(selectedCategoryWords[category]) 
                              ? selectedCategoryWords[category].map(word => cleanCandidate(word)).join(', ')
                              : cleanCandidate(selectedCategoryWords[category])
                            }
                          </div>
                        </div>
                      ) : (
                        <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                          একাধিক শব্দ নির্বাচন করুন
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Selected words summary */}
              {getTotalSelectedWords() > 0 && (
                <div className="mt-6 p-4 bg-green-50 border border-green-300 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-green-800">✅ নির্বাচিত শব্দসমূহ:</h4>
                    <button
                      type="button"
                      onClick={() => setSelectedCategoryWords({})}
                      className="text-sm text-red-600 hover:text-red-800 border border-red-300 hover:border-red-500 px-3 py-1 rounded transition"
                    >
                      🗑️ সব মুছুন
                    </button>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {Object.entries(selectedCategoryWords).map(([category, words]) => {
                      const wordArray = Array.isArray(words) ? words : [words];
                      return (
                        <div key={category} className="bg-white p-3 rounded border border-green-200">
                          <div className="text-sm text-gray-600 font-medium">{category} ({wordArray.length}টি)</div>
                          <div className="text-sm font-medium text-gray-800 max-h-20 overflow-y-auto">
                            {wordArray.map(word => cleanCandidate(word)).join(', ')}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Fallback: Original quick selection if no categories found */
            parseCandidates(aiCandidates).length > 0 && (
              <div className="bg-white shadow-lg rounded-lg p-6 mb-6 border-2 border-gray-200">
                <h2 className="text-2xl font-bold flex items-center gap-2 mb-4">
                  <Sparkles className="w-6 h-6 text-yellow-500" />
                  দ্রুত শব্দ নির্বাচন
                </h2>
                <p className="text-gray-700 mb-3 font-medium">প্রস্তাবিত শব্দসমূহ ({parseCandidates(aiCandidates).length}টি):</p>
                <div className="flex flex-wrap gap-2 mb-4">
                  {parseCandidates(aiCandidates).map((candidate, idx) => {
                    const cleanedCandidate = cleanCandidate(candidate);
                    return (
                      <button
                        key={idx}
                        type="button"
                        className={`px-4 py-2 rounded-full border text-sm font-medium transition-all duration-200 relative ${
                          selectedWord === cleanedCandidate 
                            ? 'bg-blue-600 text-white border-blue-600 shadow-md' 
                            : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-blue-50 hover:border-blue-300'
                        }`}
                        onClick={() => setSelectedWord(cleanedCandidate)}
                        onMouseEnter={() => handleWordHover(cleanedCandidate, 'ম্যানুয়াল নির্বাচন', { frequency: 1, source: 'fallback' })}
                        onMouseLeave={handleWordLeave}
                        title={`"${cleanedCandidate}" নির্বাচন করুন`}
                      >
                        {candidate}
                      </button>
                    );
                  })}
                </div>
              </div>
            )
          )}

          
        </div>
      )}

      {/* Frequency Hover Tooltip */}
      {hoveredWordData && (
        <div className="fixed top-1/2 right-5 transform -translate-y-1/2 z-50 bg-gray-900 bg-opacity-95 text-white p-4 rounded-lg shadow-xl max-w-xs backdrop-blur-sm border border-gray-600">
          <div className="border-b border-gray-600 pb-2 mb-2">
            <strong className="text-blue-300 text-lg">{hoveredWordData.word}</strong>
            <span className="text-gray-300 text-sm ml-2">({hoveredWordData.category})</span>
          </div>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between items-center">
              <span className="text-gray-300">আবৃত্তি:</span>
              <span className="text-blue-300 font-bold">{hoveredWordData.frequency} বার</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-300">উৎস:</span>
              <span className="text-blue-300 font-bold">
                {hoveredWordData.source === 'llm_selection' ? 'এআই নির্বাচিত' : 
                 hoveredWordData.source === 'fallback' ? 'স্বয়ংক্রিয়' : 
                 hoveredWordData.source}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-300">জনপ্রিয়তা:</span>
              <span className="text-blue-300 font-bold">
                {hoveredWordData.frequency >= 10 ? 'অত্যন্ত জনপ্রিয়' :
                 hoveredWordData.frequency >= 5 ? 'মাঝারি জনপ্রিয়' : 'কম জনপ্রিয়'}
              </span>
            </div>
          </div>
        </div>
      )}

      <div className="text-center mt-16">
        <button
          className="inline-block border border-gray-400 text-gray-700 hover:bg-gray-100 font-semibold px-6 py-2 rounded transition"
          onClick={() => navigate('/')}
        >
          হোম পেজে ফিরে যান
        </button>
      </div>
    </div>
  );
}

export default GenerateWords;
