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
  
  // Source selection handlers
  const handleSourceChange = (source) => {
    setSources(prev => 
      prev.includes(source) 
        ? prev.filter(s => s !== source)
        : [...prev, source]
    );
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
      console.log("Full response.data:", response.data);
      console.log("merge_prompt:", response.data.merge_prompt);
      console.log("final_llm_response:", response.data.final_llm_response);
      console.log("merge_statistics:", response.data.merge_statistics);
      console.log("=== End Debug ===");
      
      // Create comprehensive response including individual source responses
      let candidatesText = '';
      
      // Add individual source responses
      if (response.data.results) {
        candidatesText += "🔍 উৎস-ভিত্তিক LLM বিশ্লেষণ:\n";
        candidatesText += "=" + "=".repeat(50) + "\n\n";
        
        for (const [source, result] of Object.entries(response.data.results)) {
          if (source === 'newspaper') {
            candidatesText += "📰 সংবাদপত্র থেকে LLM বিশ্লেষণ:\n";
            candidatesText += "-".repeat(30) + "\n";
            candidatesText += result.raw_response || 'কোনো প্রতিক্রিয়া পাওয়া যায়নি';
          } else if (source === 'reddit') {
            candidatesText += "📡 Reddit থেকে LLM বিশ্লেষণ:\n";
            candidatesText += "-".repeat(30) + "\n";
            
            // Show subreddit-wise responses
            if (result.subreddit_results && result.subreddit_results.length > 0) {
              candidatesText += "🔥 সাবরেডিট-ভিত্তিক ইমার্জিং শব্দ:\n";
              result.subreddit_results.forEach((subResult, idx) => {
                if (subResult.status === 'success' && subResult.emerging_word) {
                  candidatesText += `  ${idx + 1}. r/${subResult.subreddit}: ${subResult.emerging_word}\n`;
                }
              });
              candidatesText += "\n";
              
              // Show individual subreddit responses
              candidatesText += "📋 সাবরেডিট LLM প্রতিক্রিয়া:\n";
              result.subreddit_results.forEach((subResult, idx) => {
                if (subResult.status === 'success' && subResult.raw_response) {
                  candidatesText += `\n🔸 r/${subResult.subreddit}:\n`;
                  candidatesText += subResult.raw_response + "\n";
                }
              });
            }
          }
          candidatesText += "\n" + "=".repeat(60) + "\n\n";
        }
      }
      
      // Add merge analysis
      if (response.data.final_llm_response) {
        console.log("=== Adding Merge Analysis ===");
        console.log("Has merge_prompt:", !!response.data.merge_prompt);
        console.log("merge_prompt content:", response.data.merge_prompt);
        
        candidatesText += "🔀 চূড়ান্ত সমন্বিত বিশ্লেষণ:\n";
        candidatesText += "=" + "=".repeat(50) + "\n\n";
        
        // Show merge statistics if available  
        if (response.data.merge_statistics) {
          candidatesText += "📊 মার্জ পরিসংখ্যান:\n";
          candidatesText += `-  মোট ইনপুট শব্দ: ${response.data.merge_statistics.total_input_words}\n`;
          candidatesText += `-  চূড়ান্ত আউটপুট শব্দ: ${response.data.merge_statistics.final_output_words}\n`;
          candidatesText += `-  সোর্স সংখ্যা: ${response.data.merge_statistics.sources_merged}\n\n`;
        }
        
        candidatesText += "🤖 মার্জ প্রম্পট:\n";
        candidatesText += "-".repeat(20) + "\n";
        if (response.data.merge_prompt) {
          candidatesText += response.data.merge_prompt + "\n\n";
          console.log("✅ Added merge prompt to display");
        } else {
          candidatesText += "❌ কোনো মার্জ প্রম্পট পাওয়া যায়নি\n\n";
          console.log("❌ No merge prompt found in response");
        }
        candidatesText += "🎯 চূড়ান্ত LLM প্রতিক্রিয়া:\n";
        candidatesText += "-".repeat(25) + "\n";
        candidatesText += response.data.final_llm_response;
      } else if (response.data.final_trending_words && response.data.final_trending_words.length > 0) {
        candidatesText += "🎯 চূড়ান্ত ট্রেন্ডিং শব্দ:\n";
        candidatesText += "=" + "=".repeat(30) + "\n\n";
        candidatesText += response.data.final_trending_words.map((word, index) => `${index + 1}. ${word}`).join('\n');
      } else {
        candidatesText = 'কোনো ট্রেন্ডিং শব্দ পাওয়া যায়নি';
      }
      
      setAiCandidates(candidatesText);
      
    } catch (err) {
      let msg = 'হাইব্রিড বিশ্লেষণ চালাতে ব্যর্থ';
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

  // Utility to strip leading numbers, dots, and titles (like ড., ডঃ, ড:)
  const cleanCandidate = (candidate) => {
    let cleaned = candidate
      .replace(/^\d+[.:][\s\-–—]*/u, '') // Remove leading numbers and dot/colon
      .replace(/^[\d\u09E6-\u09EF]+[.:][\s\-–—]*/u, '') // Bengali digits
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
    if (!selectedWord.trim()) return;
    const sanitizedWord = cleanCandidate(selectedWord);
    try {
      setSubmitting(true);
      setError(null);
      
      // Use legacy API for setting word of the day
      await api.setWordOfTheDay(sanitizedWord);
      
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

  const parseCandidates = (candidatesText) => {
    if (!candidatesText) return [];
    
    let keywords = [];
    const lines = candidatesText.split('\n');
    let inFinalSection = false;
    let inTrendingSection = false;
    
    // Debug log
    console.log("=== Parsing Candidates for Quick Selection ===");
    console.log("Total lines:", lines.length);
    
    // First, try to find the final merged trending words section
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();
      
      // Look for final trending words section
      if (trimmed.includes('চূড়ান্ত ট্রেন্ডিং শব্দ') || trimmed.includes('চূড়ান্ত LLM প্রতিক্রিয়া') || trimmed.includes('🎯')) {
        inFinalSection = true;
        console.log("Found final section at line:", i, "->", trimmed);
        continue;
      }
      
      // Look for numbered trending words pattern in final section
      if (inFinalSection && (trimmed.includes('ট্রেন্ডিং শব্দ') || trimmed.includes('(১৫টি)') || /^\d+\.\s/.test(trimmed) || /^[১-৯০]/.test(trimmed))) {
        inTrendingSection = true;
        console.log("Found trending words section at line:", i, "->", trimmed);
        
        // If this line itself has a numbered item, process it
        if (/^\d+\.\s/.test(trimmed) || /^[১-৯০]/.test(trimmed)) {
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
        continue;
      }
      
      // If we're in trending section, look for numbered items (IMPROVED BENGALI PARSING)
      if (inTrendingSection && (
        /^\d+\.\s/.test(trimmed) || // English numbers: 1. 2. etc.
        /^[১-৯০]+\.\s/.test(trimmed) || // Bengali numbers
        /^\d+\s*[\.\:]/.test(trimmed) // Numbers with dots or colons
      )) {
        let cleanedLine = trimmed
          .replace(/^\d+\s*[\.\:]\s*/, '') // Remove English numbers
          .replace(/^[১-৯০]+\s*[\.\:]\s*/, '') // Remove Bengali numbers (FIXED)
          .replace(/^\[/, '').replace(/\]$/, '') // Remove brackets
          .replace(/^["'](.+)["']$/, '$1') // Remove quotes
          .replace(/^r\/[a-zA-Z0-9_]+:\s*/, '') // Remove subreddit prefixes like "r/bangladesh: "
          .trim();
        
        if (cleanedLine.length > 1 && 
            /[\u0980-\u09FF]/.test(cleanedLine) &&
            !cleanedLine.includes('❌') && 
            !cleanedLine.includes('Error') &&
            !cleanedLine.includes('emerging word') &&
            !cleanedLine.includes('সাবরেডিট')) {
          keywords.push(cleanedLine);
          console.log("Added trending word:", cleanedLine);
        }
      }
      
      // Stop if we hit another major section  
      if (inFinalSection && (trimmed.includes('='*10) || trimmed.includes('---'))) {
        break;
      }
    }
    
    // Fallback 1: If no final section found, look for any numbered Bengali words
    if (keywords.length === 0) {
      console.log("No final section found, trying fallback parsing...");
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();
        
        // Look for numbered items (1. 2. etc.) that contain Bengali words
        if (/^\d+\.\s*/.test(trimmed) && /[\u0980-\u09FF]/.test(trimmed)) {
          let cleanedLine = trimmed.replace(/^\d+\.\s*/, '').trim();
          cleanedLine = cleanedLine.replace(/^["'](.+)["']$/, '$1');
          cleanedLine = cleanedLine.trim();
          
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
    
    // Fallback 2: Try to get from hybridResults final_trending_words if parsing failed
    if (keywords.length === 0 && hybridResults && hybridResults.final_trending_words) {
      console.log("Using fallback from hybridResults.final_trending_words");
      keywords = hybridResults.final_trending_words.slice(0, 15);
    }
    
    console.log("Final parsed candidates:", keywords);
    console.log("=== End Debug ===");
    return keywords.slice(0, 15); // Show max 15 words for quick selection
  };

  if (success) {
    return (
      <div className="container mx-auto px-4 py-12 bg-white min-h-[calc(100vh-4rem)] flex flex-col justify-center items-center">
        <div className="bg-green-100 border border-green-300 text-green-800 px-4 py-6 rounded mb-6 text-center max-w-md w-full">
          <h2 className="text-xl font-bold mb-2">সফলভাবে সম্পন্ন!</h2>
          <p>আজকের শব্দ নির্ধারণ করা হয়েছে: <span className="font-semibold">{selectedWord}</span></p>
        </div>
        <svg className="animate-spin h-12 w-12 text-green-500 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
        <p className="mt-4 text-gray-700">হোম পেজে ফিরে যাচ্ছি...</p>
      </div>
    );
  }

  return (
    <div className={`container mx-auto px-4 py-12 bg-white min-h-[calc(100vh-4rem)] flex flex-col justify-center ${isResizing ? 'no-select' : ''}`}>
      <div className="text-center mb-10">
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-gray-900 mb-2 flex items-center justify-center gap-2">
          <Sparkles className="w-8 h-8 text-pink-500" /> হাইব্রিড ট্রেন্ডিং শব্দ উৎপাদন
        </h1>
        <p className="text-lg text-gray-600">সংবাদ ও Reddit থেকে AI ও NLP বিশ্লেষণ ব্যবহার করে বর্তমান ট্রেন্ডিং শব্দ খুঁজে বের করুন</p>
      </div>

      {/* Source and Mode Selection */}
      <div className="max-w-4xl mx-auto mb-8">
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-center">বিশ্লেষণ কনফিগারেশন</h2>
          
          {/* Source Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">ডেটা সোর্স নির্বাচন করুন:</label>
            <div className="flex flex-wrap gap-4 justify-center">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={sources.includes('newspaper')}
                  onChange={() => handleSourceChange('newspaper')}
                  className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-sm font-medium text-gray-700">📰 সংবাদপত্র</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={sources.includes('reddit')}
                  onChange={() => handleSourceChange('reddit')}
                  className="mr-2 h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                />
                <span className="text-sm font-medium text-gray-700">📡 Reddit</span>
              </label>
            </div>
          </div>

          {/* Mode Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-3">প্রক্রিয়াকরণ মোড:</label>
            <div className="flex gap-4 justify-center">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="mode"
                  value="sequential"
                  checked={mode === 'sequential'}
                  onChange={(e) => setMode(e.target.value)}
                  className="mr-2 h-4 w-4 text-green-600 focus:ring-green-500"
                />
                <span className="text-sm font-medium text-gray-700">⏭️ ক্রমানুসারে (Sequential)</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="mode"
                  value="parallel"
                  checked={mode === 'parallel'}
                  onChange={(e) => setMode(e.target.value)}
                  className="mr-2 h-4 w-4 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm font-medium text-gray-700">🔄 সমান্তরাল (Parallel)</span>
              </label>
            </div>
            <p className="text-xs text-gray-500 text-center mt-2">
              ক্রমানুসারে: একে একে প্রক্রিয়া (ডিফল্ট) | সমান্তরাল: একসাথে প্রক্রিয়া (দ্রুততর)
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-300 text-red-800 px-4 py-3 rounded mb-6 text-center max-w-md mx-auto">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto">
        <div className="bg-white shadow-md rounded-lg p-8 flex flex-col justify-between items-center text-center">
          <h2 className="text-xl font-semibold mb-2">১. হাইব্রিড বিশ্লেষণ চালান</h2>
          <p className="text-gray-600 mb-4">
            নির্বাচিত সোর্স ({sources.join(', ')}) থেকে {mode === 'sequential' ? 'ক্রমানুসারে' : 'সমান্তরালে'} ট্রেন্ডিং শব্দ বিশ্লেষণ করুন
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
            {loading ? 'বিশ্লেষণ চলছে...' : 'হাইব্রিড বিশ্লেষণ শুরু করুন'}
          </button>
          {sources.length === 0 && (
            <div className="bg-yellow-100 border border-yellow-300 text-yellow-800 px-4 py-2 rounded mt-4 text-center w-full">
              ⚠️ অন্তত একটি সোর্স নির্বাচন করুন
            </div>
          )}
          {analysisComplete && (
            <div className="bg-green-100 border border-green-300 text-green-800 px-4 py-2 rounded mt-4 text-center w-full">
              <span className="mr-2">✅</span> হাইব্রিড বিশ্লেষণ সম্পূর্ণ! ফাইনাল ট্রেন্ডিং শব্দ তৈরি হয়েছে।
            </div>
          )}
        </div>
        <div className="bg-white shadow-md rounded-lg p-8 flex flex-col justify-between items-center text-center">
          <h2 className="text-xl font-semibold mb-2">২. শব্দ নির্বাচন</h2>
          <p className="text-gray-600 mb-4">AI দ্বারা প্রস্তাবিত শব্দ থেকে আজকের শব্দ নির্ধারণ করুন</p>
          <form onSubmit={handleSubmit} className="w-full">
            <input
              type="text"
              className="w-full border border-gray-300 rounded px-4 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-pink-400"
              placeholder="একটি শব্দ টাইপ করুন..."
              value={selectedWord}
              onChange={e => setSelectedWord(e.target.value)}
              disabled={submitting}
            />
            <button
              type="submit"
              className={`w-full flex items-center justify-center gap-2 px-6 py-2 rounded font-semibold text-white transition ${!selectedWord.trim() || submitting ? 'bg-gray-400' : 'bg-pink-600 hover:bg-pink-700'} shadow`}
              disabled={!selectedWord.trim() || submitting}
            >
              {submitting ? (
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
              ) : (
                <Check className="w-5 h-5" />
              )}
              {submitting ? 'সেট করা হচ্ছে...' : 'আজকের শব্দ নির্ধারণ করুন'}
            </button>
          </form>
        </div>
      </div>

      {analysisComplete && aiCandidates && (
        <div 
          ref={resizeRef}
          className="bg-white shadow-lg rounded-lg mt-10 p-6 max-w-5xl mx-auto relative border-2 border-gray-200"
          style={{ minHeight: `${candidateHeight}px` }}
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-yellow-500" />
              AI প্রার্থীর তালিকা
            </h2>
            <div className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
              উচ্চতা: {candidateHeight}px
            </div>
          </div>
          
          <hr className="mb-6 border-gray-300" />
          
          {parseCandidates(aiCandidates).length > 0 ? (
            <div className="mb-6">
              <p className="text-gray-700 mb-3 font-medium">দ্রুত নির্বাচনের জন্য প্রস্তাবিত শব্দসমূহ ({parseCandidates(aiCandidates).length}টি):</p>
              <div className="flex flex-wrap gap-2 mb-6">
                {parseCandidates(aiCandidates).map((candidate, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className={`px-4 py-2 rounded-full border text-sm font-medium transition-all duration-200 ${selectedWord === cleanCandidate(candidate) ? 'bg-blue-600 text-white border-blue-600 shadow-md' : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-blue-50 hover:border-blue-300'}`}
                    onClick={() => setSelectedWord(cleanCandidate(candidate))}
                  >
                    {candidate}
                  </button>
                ))}
              </div>
              <hr className="mb-4 border-gray-200" />
              <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4">
                <p className="text-blue-800 font-medium text-sm">📋 সম্পূর্ণ AI প্রার্থিতালিকা</p>
                {/* <p className="text-blue-600 text-xs mt-1">💡 নিচের নীল resize bar টি টেনে area বড় করে সব content দেখুন</p> */}
              </div>
            </div>
          ) : (
            <div className="mb-6">
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
                <p className="text-yellow-800 font-medium text-sm">⚠️ কোনো নির্বাচনযোগ্য শব্দ পাওয়া যায়নি</p>
                <p className="text-yellow-600 text-xs mt-1">💡 সম্পূর্ণ AI প্রার্থিতালিকা নিচে দেখুন</p>
              </div>
            </div>
          )}
          
          {/* Resizable content area with better styling */}
          <div 
            className="bg-gray-50 rounded-lg border-2 border-gray-200 overflow-auto candidate-content shadow-inner"
            style={{ 
              height: `${candidateHeight - 220}px`, // More space for content
              minHeight: '250px'
            }}
          >
            <div className="p-6">
              <pre className="text-gray-800 whitespace-pre-wrap text-sm leading-relaxed font-mono bg-white p-4 rounded border shadow-sm">{aiCandidates}</pre>
            </div>
          </div>
          
          {/* Enhanced resize handle */}
          <div 
            className={`resize-handle absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-r from-blue-100 to-indigo-100 border-t-2 border-blue-300 rounded-b-lg cursor-ns-resize flex items-center justify-center transition-all duration-200 ${isResizing ? 'bg-gradient-to-r from-blue-200 to-indigo-200 shadow-lg' : 'hover:from-blue-150 hover:to-indigo-150'}`}
            onMouseDown={handleMouseDown}
            title="Drag to resize - টেনে আকার পরিবর্তন করুন"
          >
            <div className="flex items-center gap-1">
              <GripVertical className="w-4 h-4 text-blue-600" />
              <span className="text-xs text-blue-600 font-medium">Resize</span>
              <GripVertical className="w-4 h-4 text-blue-600" />
            </div>
          </div>
          
          {/* Enhanced size indicator during resize */}
          {isResizing && (
            <div className="absolute top-4 right-4 bg-blue-600 text-white text-sm px-4 py-2 rounded-lg shadow-lg border-2 border-blue-700 font-mono">
              📏 {candidateHeight}px
            </div>
          )}
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
