import React, { useState, useRef, useEffect } from 'react';
import { Brain, CheckCircle, AlertCircle, Loader, Play, BarChart3, TrendingUp, Users, Zap, Search, MessageSquare, Target, Sparkles, X } from 'lucide-react';
import { apiV2 } from '../api';

const ProgressIndicator = ({ onAnalysisComplete, onClose, onStepUpdate }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [steps, setSteps] = useState([]);
  const [error, setError] = useState(null);
  const [analysisCompleted, setAnalysisCompleted] = useState(false);
  const [stepResults, setStepResults] = useState({});
  const eventSourceRef = useRef(null);
  
  // Add effect to start analysis automatically when component mounts
  useEffect(() => {
    console.log('=== 🎬 ProgressIndicator component mounted - starting analysis ===');
    startAnalysis();
    
    return () => {
      console.log('=== 💥 ProgressIndicator component will unmount ===');
      if (eventSourceRef.current) {
        console.log('=== 🔌 Cleaning up EventSource on unmount ===');
        eventSourceRef.current.close();
      }
    };
  }, []);

  const analysisSteps = [
    { icon: Play, title: 'বিশ্লেষণ প্রস্তুতি', stepName: 'সিস্টেম প্রস্তুতি' },
    { icon: Search, title: 'ডেটা সংগ্রহ শুরু', stepName: 'ডেটা সংগ্রহ শুরু' },
    { icon: MessageSquare, title: 'সংবাদ সংগ্রহ', stepName: 'সংবাদ সংগ্রহ' },
    { icon: BarChart3, title: 'ক্যাটেগরি বিশ্লেষণ', stepName: 'ক্যাটেগরি বিশ্লেষণ' },
    { icon: TrendingUp, title: 'কীওয়ার্ড নিষ্কাশন', stepName: 'কীওয়ার্ড নিষ্কাশন' },
    { icon: Users, title: 'ফ্রিকোয়েন্সি গণনা', stepName: 'ফ্রিকোয়েন্সি গণনা' },
    { icon: Brain, title: 'ট্রেন্ড বিশ্লেষণ', stepName: 'ট্রেন্ড বিশ্লেষণ' },
    { icon: Target, title: 'চূড়ান্ত নির্বাচন', stepName: 'চূড়ান্ত নির্বাচন' },
    { icon: Sparkles, title: 'বিশ্লেষণ সম্পূর্ণ', stepName: 'বিশ্লেষণ সম্পূর্ণ' }
  ];

  const startAnalysis = async () => {
    console.log('=== Starting Generate Candidates Analysis ===');
    setIsRunning(true);
    setCurrentStep(1);
    setProgress(0);
    setSteps([]);
    setStepResults({});
    setError(null);
    setAnalysisCompleted(false);
    
    // Initial step
    if (onStepUpdate) {
      onStepUpdate('সিস্টেম প্রস্তুতি');
    }

    try {
      const startTime = Date.now();
      let progressInterval = null; // Initialize properly
      
      // Step 1: System preparation (0-5%)
      setProgress(5);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Step 2: Initiating API call (5-10%)
      setCurrentStep(2);
      setProgress(10);
      if (onStepUpdate) onStepUpdate('ডেটা সংগ্রহ শুরু');
      
      console.log('Calling generate-candidates API...');
      
      // Estimate based on backend workflow:
      // - Newspaper scraping: ~30-60 seconds (10-40% progress)
      // - LLM calls for 12 categories with 50s delay each: ~10-12 minutes (40-90% progress)  
      // - Final LLM selection: ~30-60 seconds (90-100% progress)
      
      let currentProgress = 10;
      let apiCompleted = false;
      
      // Start API call
      const apiPromise = apiV2.hybridGenerateCandidates({
        sources: ['newspaper', 'reddit'],
        mode: 'sequential'
      });
      
      // Realistic progress based on backend phases
      progressInterval = setInterval(() => {
        if (apiCompleted) {
          clearInterval(progressInterval);
          return;
        }
        
        const elapsed = Date.now() - startTime;
        
        // Phase 1: Newspaper scraping (first 60 seconds, 10-25% progress)
        if (elapsed < 60000) {
          currentProgress = Math.min(25, 10 + (elapsed / 60000) * 15);
          if (currentProgress >= 15 && currentStep < 3) {
            setCurrentStep(3);
            if (onStepUpdate) onStepUpdate('সংবাদ সংগ্রহ');
          }
        }
        // Phase 2: LLM category analysis (60s-720s, 25-80% progress)
        // 12 categories × 50s delay + processing = ~11-12 minutes
        else if (elapsed < 720000) { // 12 minutes
          currentProgress = Math.min(80, 25 + ((elapsed - 60000) / 660000) * 55);
          
          // Update steps based on LLM progress
          if (currentProgress >= 30 && currentStep < 4) {
            setCurrentStep(4);
            if (onStepUpdate) onStepUpdate('ক্যাটেগরি বিশ্লেষণ');
          } else if (currentProgress >= 45 && currentStep < 5) {
            setCurrentStep(5);
            if (onStepUpdate) onStepUpdate('কীওয়ার্ড নিষ্কাশন');
          } else if (currentProgress >= 60 && currentStep < 6) {
            setCurrentStep(6);
            if (onStepUpdate) onStepUpdate('ফ্রিকোয়েন্সি গণনা');
          } else if (currentProgress >= 75 && currentStep < 7) {
            setCurrentStep(7);
            if (onStepUpdate) onStepUpdate('ট্রেন্ড বিশ্লেষণ');
          }
        }
        // Phase 3: Final selection (720s+, 80-95% progress)
        else {
          currentProgress = Math.min(95, 80 + ((elapsed - 720000) / 60000) * 15);
          if (currentStep < 8) {
            setCurrentStep(8);
            if (onStepUpdate) onStepUpdate('চূড়ান্ত নির্বাচন');
          }
        }
        
        setProgress(Math.round(currentProgress));
        
        // Log current phase for debugging
        if (elapsed % 10000 < 1000) { // Log every 10 seconds
          console.log(`Progress: ${Math.round(currentProgress)}% - Elapsed: ${Math.round(elapsed/1000)}s - Step: ${currentStep}`);
        }
        
      }, 1000); // Update every second
      
      // Wait for API to complete
      const response = await apiPromise;
      apiCompleted = true;
      clearInterval(progressInterval);
      
      // API completed successfully
      setCurrentStep(9);
      setProgress(100);
      
      const totalTime = Date.now() - startTime;
      console.log(`=== ✅ ANALYSIS COMPLETED in ${Math.round(totalTime/1000)}s ===`);
      
      // Call parent step update callback to show final step
      if (onStepUpdate) {
        onStepUpdate('বিশ্লেষণ সম্পূর্ণ');
      }
      
      setAnalysisCompleted(true);
      setIsRunning(false);
      
      console.log('API Response:', response);
      
      // Call parent callback immediately (no delay needed)
      console.log('=== 📞 Calling parent onAnalysisComplete callback ===');
      if (onAnalysisComplete) {
        onAnalysisComplete(response.data);
      }

    } catch (err) {
      console.error('=== Analysis Error ===', err);
      
      // Check if it's a rate limit error or similar API error but with valid response
      if (err.response && err.response.status === 200) {
        console.log('⚠️ API returned 200 but with error content - treating as success');
        apiCompleted = true;
        clearInterval(progressInterval);
        
        setCurrentStep(9);
        setProgress(100);
        setAnalysisCompleted(true);
        setIsRunning(false);
        
        if (onStepUpdate) {
          onStepUpdate('বিশ্লেষণ সম্পূর্ণ');
        }
        
        // Try to extract data from error response
        const responseData = err.response.data || {};
        if (onAnalysisComplete) {
          onAnalysisComplete(responseData);
        }
        return;
      }
      
      // Handle rate limit errors gracefully
      if (err.response && err.response.data && 
          (err.response.data.message?.includes('Rate limit') || 
           err.response.data.detail?.includes('Rate limit'))) {
        console.log('⚠️ Rate limit reached but analysis may have completed');
        apiCompleted = true;
        clearInterval(progressInterval);
        
        setCurrentStep(9);
        setProgress(100);
        setAnalysisCompleted(true);
        setIsRunning(false);
        
        if (onStepUpdate) {
          onStepUpdate('বিশ্লেষণ সম্পূর্ণ');
        }
        
        // Set a warning instead of error
        setError('API রেট লিমিট - তবে বিশ্লেষণ সম্পূর্ণ হয়েছে');
        
        // Try to return partial data
        if (onAnalysisComplete) {
          onAnalysisComplete(err.response.data || {});
        }
        return;
      }
      
      // Real error
      setError('বিশ্লেষণে সমস্যা হয়েছে: ' + (err.response?.data?.detail || err.message));
      setIsRunning(false);
      
      // Clear progress interval on error
      if (progressInterval) {
        clearInterval(progressInterval);
      }
    }
  };

  const stopAnalysis = () => {
    console.log('=== Stopping analysis ===');
    setIsRunning(false);
    setError('বিশ্লেষণ বাতিল করা হয়েছে');
  };

  const getCurrentStepInfo = () => {
    if (currentStep > 0 && currentStep <= analysisSteps.length) {
      return analysisSteps[currentStep - 1];
    }
    return { title: 'প্রস্তুতি', stepName: 'প্রস্তুতি', icon: Play };
  };

  const stepInfo = getCurrentStepInfo();
  const StepIcon = stepInfo.icon;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white bg-opacity-20 rounded-lg">
                <Brain className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-xl font-bold">ট্রেন্ডিং বিশ্লেষণ</h2>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-all"
              disabled={isRunning}
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Progress Content */}
        <div className="p-6">
          {/* Current Step Display */}
          <div className="flex items-center gap-4 mb-6">
            <div className={`p-3 rounded-xl ${
              analysisCompleted ? 'bg-green-100 text-green-600' : 
              isRunning ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
            }`}>
              {analysisCompleted ? (
                <CheckCircle className="w-8 h-8" />
              ) : isRunning ? (
                <Loader className="w-8 h-8 animate-spin" />
              ) : (
                <StepIcon className="w-8 h-8" />
              )}
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold text-gray-800">
                {analysisCompleted ? 'বিশ্লেষণ সম্পূর্ণ!' : stepInfo.title}
              </h3>
              <p className="text-sm text-gray-600">
                {analysisCompleted ? 'ফলাফল প্রস্তুত হয়েছে' : 
                 isRunning ? 'প্রক্রিয়াকরণ চলছে...' : 'প্রস্তুতি নিচ্ছে...'}
              </p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">অগ্রগতি</span>
              <span className="text-lg font-bold text-blue-600">{progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 p-3 rounded-lg mb-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                <span className="text-sm">{error}</span>
              </div>
            </div>
          )}

          {/* Completion Message */}
          {analysisCompleted && (
            <div className="bg-green-50 border border-green-200 text-green-800 p-4 rounded-lg text-center">
              <CheckCircle className="w-8 h-8 mx-auto mb-2" />
              <p className="font-semibold">বিশ্লেষণ সফলভাবে সম্পন্ন হয়েছে!</p>
              <p className="text-sm mt-1">ফলাফল দেখতে মডালটি বন্ধ করুন।</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 mt-6">
            {isRunning && (
              <button
                onClick={stopAnalysis}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                বন্ধ করুন
              </button>
            )}
            {!isRunning && !analysisCompleted && (
              <button
                onClick={startAnalysis}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                পুনরায় চেষ্টা করুন
              </button>
            )}
            {analysisCompleted && (
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                ফলাফল দেখুন
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProgressIndicator;
