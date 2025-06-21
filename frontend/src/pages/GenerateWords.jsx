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
  const [candidateHeight, setCandidateHeight] = useState(500); // Increased default height
  const [isResizing, setIsResizing] = useState(false);
  const navigate = useNavigate();
  const resizeRef = useRef(null);

  const runAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      // Run the comprehensive analysis
      const response = await apiV2.generateCandidates();
      setAnalysisComplete(true);
      setAiCandidates(response.data.ai_candidates || 'কোনো AI প্রার্থী পাওয়া যায়নি');
    } catch (err) {
      let msg = 'বিশ্লেষণ চালাতে ব্যর্থ';
      if (err.response && err.response.data && err.response.data.detail) {
        msg += `: ${err.response.data.detail}`;
      }
      setError(msg);
      setAnalysisComplete(false);
      setAiCandidates('');
      console.error('Analysis error:', err);
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
    
    // Extract only the NLP keywords that start with 🔸
    const keywords = [];
    const lines = candidatesText.split('\n');
    
    for (const line of lines) {
      const trimmed = line.trim();
      // Look for lines that contain 🔸 (NLP keywords)
      if (trimmed.includes('🔸')) {
        const match = trimmed.match(/🔸\s*([^:]+):/);
        if (match) {
          const keyword = match[1].trim();
          if (keyword && keyword.length > 1) {
            keywords.push(keyword);
          }
        }
      }
    }
    
    return keywords.slice(0, 10); // Limit to 10 candidates
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
          <Sparkles className="w-8 h-8 text-pink-500" /> ট্রেন্ডিং শব্দ উৎপাদন
        </h1>
        <p className="text-lg text-gray-600">AI এবং NLP বিশ্লেষণ ব্যবহার করে বর্তমান ট্রেন্ডিং শব্দ খুঁজে বের করুন</p>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-300 text-red-800 px-4 py-3 rounded mb-6 text-center max-w-md mx-auto">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto">
        <div className="bg-white shadow-md rounded-lg p-8 flex flex-col justify-between items-center text-center">
          <h2 className="text-xl font-semibold mb-2">১. বিশ্লেষণ চালান</h2>
          <p className="text-gray-600 mb-4">সংবাদ ও সোশ্যাল মিডিয়া ডেটা থেকে ট্রেন্ডিং শব্দ বিশ্লেষণ করুন</p>
          <button
            className={`w-full flex items-center justify-center gap-2 px-6 py-2 rounded font-semibold text-white transition ${loading ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'} shadow`}
            onClick={runAnalysis}
            disabled={loading}
          >
            {loading ? (
              <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
            ) : (
              <RefreshCw className="w-5 h-5" />
            )}
            {loading ? 'বিশ্লেষণ চলছে...' : 'বিশ্লেষণ শুরু করুন'}
          </button>
          {analysisComplete && (
            <div className="bg-green-100 border border-green-300 text-green-800 px-4 py-2 rounded mt-4 text-center w-full">
              <span className="mr-2">✅</span> বিশ্লেষণ সম্পূর্ণ! AI প্রার্থী তৈরি হয়েছে।
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
              <p className="text-gray-700 mb-3 font-medium">দ্রুত নির্বাচনের জন্য প্রস্তাবিত শব্দসমূহ:</p>
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
                <p className="text-yellow-800 font-medium text-sm">📋 সম্পূর্ণ AI প্রার্থিতালিকা</p>
                {/* <p className="text-yellow-600 text-xs mt-1">💡 নিচের নীল resize bar টি টেনে area বড় করে সব content দেখুন</p> */}
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
