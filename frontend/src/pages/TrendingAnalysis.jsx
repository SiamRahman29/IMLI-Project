import { useEffect, useState } from 'react';
import { apiV2, formatDate, getScoreColor, groupPhrasesByType, groupPhrasesBySource, authUtils } from '../api';
import { TrendingUp, Globe, Newspaper, Users, RefreshCw, Filter, Zap, Calendar, Trash2, BarChart3, X } from 'lucide-react';
import ProgressiveAnalysis from '../components/ProgressiveAnalysis';
import ConfirmationModal from '../components/ConfirmationModal';
import { useLanguage } from '../hooks/useLanguage';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

function TrendingAnalysis() {
  const { isBengali, translate } = useLanguage();

  // Translation function for phrase types and sources
  const translateLabel = (label) => {
    const translations = {
      // Phrase types
      'selected': 'নির্বাচিত',
      'unigram': 'একক শব্দ',
      'bigram': 'দ্বিত্ব শব্দ',
      'trigram': 'ত্রিগুণ শব্দ',
      // Sources
      'user_selection': 'ব্যবহারকারী নির্বাচন',
      'news': 'সংবাদ',
      'social_media': 'সামাজিক মাধ্যম',
      'newspaper': 'সংবাদপত্র',
      'reddit': 'রেডিট',
    };
    return translations[label] || label;
  };

  const [trendingData, setTrendingData] = useState(null);
  const [dailyData, setDailyData] = useState(null);
  const [weeklyData, setWeeklyData] = useState(null);
  const [stats, setStats] = useState(null);
  const [sources, setSources] = useState({ sources: [], phrase_types: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const [tabValue, setTabValue] = useState(0);
  const [filters, setFilters] = useState({
    start_date: formatDate(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)),
    end_date: formatDate(new Date()),
    source: '',
    phrase_type: '',
    limit: 10,
    search: ''
  });
  const [searchInput, setSearchInput] = useState('');
  const [toast, setToast] = useState(null);
  const [showProgressiveAnalysis, setShowProgressiveAnalysis] = useState(false);
  const [progressiveAnalysisCompleted, setProgressiveAnalysisCompleted] = useState(false);
  const [preventModalClose, setPreventModalClose] = useState(false); // Add protection flag
  const [deleteModal, setDeleteModal] = useState({ isOpen: false, phraseId: null, phraseName: '', frequency: 0 });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [phraseGraphModal, setPhraseGraphModal] = useState({ isOpen: false, phrase: null, data: [] });
  const [phraseGraphLoading, setPhraseGraphLoading] = useState(false);

  // Check if user is admin
  const isAdmin = authUtils.isAdmin();

  // Add debugging for modal state changes
  useEffect(() => {
    console.log('=== 📊 showProgressiveAnalysis state changed:', showProgressiveAnalysis);
  }, [showProgressiveAnalysis]);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleDeletePhrase = async (phraseId) => {
    try {
      const response = await apiV2.deleteTrendingPhrase(phraseId);
      
      // Handle different delete actions
      if (response.action === 'frequency_decreased') {
        showToast(`ফ্রিকোয়েন্সি কমে গেছে ${response.remaining_frequency} এ`, 'success');
      } else {
        showToast('ট্রেন্ডিং ফ্রেজ সম্পূর্ণভাবে মুছে ফেলা হয়েছে', 'success');
      }
      
      setDeleteModal({ isOpen: false, phraseId: null, phraseName: '' });
      // Refresh the data
      fetchTrendingData();
    } catch (error) {
      showToast('ফ্রেজ মুছতে সমস্যা হয়েছে', 'error');
      console.error('Error deleting phrase:', error);
    }
  };

  const openDeleteModal = (phraseId, phraseName, frequency) => {
    setDeleteModal({ isOpen: true, phraseId, phraseName, frequency });
  };

  const closeDeleteModal = () => {
    setDeleteModal({ isOpen: false, phraseId: null, phraseName: '', frequency: 0 });
  };

  // Function to fetch phrase frequency data over time
  const fetchPhraseFrequencyData = async (phrase) => {
    setPhraseGraphLoading(true);
    try {
      // Call API to get phrase frequency over time (without date restrictions to show all data)
      const response = await apiV2.getPhraseFrequencyData(phrase, null, null);
      console.log('🔍 API response for phrase frequency:', { phrase, response });
      // Backend returns { data: { phrase, start_date, end_date, total_records, data: [...] } }
      // So we need response.data.data
      return response.data?.data || [];
    } catch (error) {
      console.error('Error fetching phrase frequency data:', error);
      showToast('ফ্রেজ ডেটা লোড করতে ব্যর্থ', 'error');
      return [];
    } finally {
      setPhraseGraphLoading(false);
    }
  };

  const openPhraseGraphModal = async (phrase) => {
    setPhraseGraphModal({ isOpen: true, phrase, data: [] });
    const data = await fetchPhraseFrequencyData(phrase);
    console.log('🔍 Phrase frequency data received:', { phrase, data, dataLength: data?.length });
    
    // Ensure data is properly formatted and sorted by date
    const sortedData = Array.isArray(data) ? data.sort((a, b) => new Date(a.date) - new Date(b.date)) : [];
    console.log('📊 Sorted data for graph:', sortedData);
    
    setPhraseGraphModal(prev => ({ ...prev, data: sortedData }));
  };

  const closePhraseGraphModal = () => {
    setPhraseGraphModal({ isOpen: false, phrase: null, data: [] });
  };

  useEffect(() => {
    fetchAllData();
    fetchSources();
  }, []);

  useEffect(() => {
    const handleKeyDown = (event) => {
      // Ctrl/Cmd + K to focus search
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        const searchInput = document.querySelector('input[placeholder*="ফ্রেজ বা শব্দ দিয়ে খুঁজুন"]');
        if (searchInput) {
          searchInput.focus();
        }
      }
      // Enter key to trigger search
      if (event.key === 'Enter' && document.activeElement.placeholder?.includes('ফ্রেজ বা শব্দ দিয়ে খুঁজুন')) {
        event.preventDefault();
        handleSearchSubmit();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [searchInput]);

  useEffect(() => {
    // Reset to page 1 when filters change
    setCurrentPage(1);
  }, [filters]);

  useEffect(() => {
    // Fetch data when page changes
    if (tabValue === 0) {
      fetchTrendingData();
    }
  }, [currentPage]);

  useEffect(() => {
    if (tabValue === 0) {
      fetchTrendingData();
    } else if (tabValue === 1) {
      fetchDailyData();
    } else if (tabValue === 2) {
      fetchWeeklyData();
    } else if (tabValue === 3) {
      fetchStats();
    }
  }, [filters, tabValue]);

  const fetchAllData = async () => {
    await Promise.all([
      fetchTrendingData(),
      fetchDailyData(),
      fetchWeeklyData(),
      fetchStats()
    ]);
  };

  const fetchTrendingData = async () => {
    try {
      setLoading(true);
      const offset = (currentPage - 1) * filters.limit;
      const requestFilters = { ...filters, offset };
      const response = await apiV2.getTrendingPhrases(requestFilters);
      setTrendingData(response.data);
      
      // Calculate total pages
      if (response.data.pagination) {
        const pages = Math.ceil(response.data.pagination.total / filters.limit);
        setTotalPages(pages);
      }
    } catch (err) {
      let msg = 'ট্রেন্ডিং ডেটা লোড করতে ব্যর্থ';
      if (err.response && err.response.data && err.response.data.detail) {
        msg += `: ${err.response.data.detail}`;
      }
      setError(msg);
      console.error('Trending data error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDailyData = async () => {
    try {
      setLoading(true);
      const response = await apiV2.getDailyTrending(filters.end_date);
      setDailyData(response.data);
    } catch (err) {
      let msg = 'দৈনিক ডেটা লোড করতে ব্যর্থ';
      if (err.response && err.response.data && err.response.data.detail) {
        msg += `: ${err.response.data.detail}`;
      }
      setError(msg);
      console.error('Daily data error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchWeeklyData = async () => {
    try {
      setLoading(true);
      const response = await apiV2.getWeeklyTrending();
      setWeeklyData(response.data);
    } catch (err) {
      let msg = 'সাপ্তাহিক ডেটা লোড করতে ব্যর্থ';
      if (err.response && err.response.data && err.response.data.detail) {
        msg += `: ${err.response.data.detail}`;
      }
      setError(msg);
      console.error('Weekly data error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      setLoading(true);
      const response = await apiV2.getStats();
      setStats(response.data);
    } catch (err) {
      let msg = 'পরিসংখ্যান লোড করতে ব্যর্থ';
      if (err.response && err.response.data && err.response.data.detail) {
        msg += `: ${err.response.data.detail}`;
      }
      setError(msg);
      console.error('Stats error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSources = async () => {
    try {
      const response = await apiV2.getSources();
      setSources(response.data);
    } catch (err) {
      console.error('Sources error:', err);
    }
  };

  const runSimpleAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      await apiV2.runAnalysis();
      await fetchAllData();
      setRetryCount(0);
      showToast('বিশ্লেষণ সফলভাবে সম্পন্ন হয়েছে!', 'success');
    } catch (err) {
      const errorMessage = 'নতুন বিশ্লেষণ চালাতে ব্যর্থ';
      setError(errorMessage);
      setRetryCount(prev => prev + 1);
      showToast(errorMessage, 'error');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const retryAction = async () => {
    if (tabValue === 0) {
      await fetchTrendingData();
    } else if (tabValue === 1) {
      await fetchDailyData();
    } else if (tabValue === 2) {
      await fetchWeeklyData();
    } else if (tabValue === 3) {
      await fetchStats();
    }
  };

  const handleProgressiveAnalysisComplete = () => {
    setShowProgressiveAnalysis(false);
    setProgressiveAnalysisCompleted(true);
    fetchAllData(); // Refresh all data after analysis
    showToast('বিশ্লেষণ সফলভাবে সম্পন্ন হয়েছে!', 'success');
  };

  const handleProgressiveAnalysisClose = () => {
    setShowProgressiveAnalysis(false);
  };

  const exportData = () => {
    let dataToExport = [];
    let filename = '';
    
    if (tabValue === 0 && trendingData?.phrases) {
      dataToExport = trendingData.phrases.map(phrase => ({
        'ফ্রেজ': phrase.phrase,
        'ফ্রিকোয়েন্সি': phrase.frequency,
        'ধরণ': phrase.phrase_type,
        'উৎস': phrase.source,
        'তারিখ': phrase.date
      }));
      filename = `trending-phrases-${filters.start_date}-to-${filters.end_date}.csv`;
    } else if (tabValue === 1 && dailyData?.top_phrases) {
      dataToExport = dailyData.top_phrases.map(phrase => ({
        'ফ্রেজ': phrase.phrase,
        'ফ্রিকোয়েন্সি': phrase.frequency,
        'ধরণ': phrase.phrase_type,
        'উৎস': phrase.source
      }));
      filename = `daily-summary-${dailyData.date}.csv`;
    } else if (tabValue === 2 && weeklyData?.top_weekly_phrases) {
      dataToExport = weeklyData.top_weekly_phrases.map(phrase => ({
        'ফ্রেজ': phrase.phrase,
        'ফ্রিকোয়েন্সি': phrase.frequency,
        'ধরণ': phrase.phrase_type,
        'উৎস': phrase.source,
        'তারিখ': phrase.date
      }));
      filename = `weekly-summary-${weeklyData.week_start}-to-${weeklyData.week_end}.csv`;
    }
    
    if (dataToExport.length === 0) {
      showToast('কোনো ডেটা রপ্তানি করার জন্য উপলব্ধ নেই', 'error');
      return;
    }
    
    // Convert to CSV
    const headers = Object.keys(dataToExport[0]).join(',');
    const csvContent = dataToExport.map(row => 
      Object.values(row).map(value => 
        typeof value === 'string' ? `"${value.replace(/"/g, '""')}"` : value
      ).join(',')
    ).join('\n');
    
    const csv = headers + '\n' + csvContent;
    
    // Download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    
    showToast(`${dataToExport.length}টি রেকর্ড সফলভাবে রপ্তানি করা হয়েছে`, 'success');
  };

  const handleTabChange = (idx) => {
    setTabValue(idx);
    setError(null);
  };

  const handleFilterChange = (field, value) => {
    const newFilters = { ...filters, [field]: value };
    
    // Date validation
    if (field === 'start_date' || field === 'end_date') {
      const startDate = new Date(field === 'start_date' ? value : filters.start_date);
      const endDate = new Date(field === 'end_date' ? value : filters.end_date);
      
      // Ensure start date is not after end date
      if (startDate > endDate) {
        if (field === 'start_date') {
          newFilters.end_date = value;
        } else {
          newFilters.start_date = value;
        }
      }
      
      // Ensure dates are not in the future
      const today = new Date();
      today.setHours(23, 59, 59, 999); // End of today
      
      if (startDate > today) {
        newFilters.start_date = formatDate(today);
      }
      if (endDate > today) {
        newFilters.end_date = formatDate(today);
      }
    }
    
    setFilters(newFilters);
  };

  const setDateRange = (days) => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - days);
    
    setFilters(prev => ({
      ...prev,
      start_date: formatDate(startDate),
      end_date: formatDate(endDate)
    }));
  };

  const handleSearchSubmit = () => {
    setFilters(prev => ({
      ...prev,
      search: searchInput
    }));
  };

  const handleSearchInputChange = (value) => {
    setSearchInput(value);
    // Clear search if input is empty
    if (value === '') {
      setFilters(prev => ({
        ...prev,
        search: ''
      }));
    }
  };

  const renderFilters = () => (
    <div className="bg-gradient-to-br from-white to-gray-50 shadow-2xl rounded-2xl mb-8 p-6 border border-gray-200 backdrop-blur-lg">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg">
            <Filter className="w-5 h-5 text-white" />
          </div>
          <span className="font-black text-gray-900 text-lg tracking-tight">{translate('ফিল্টার অপশন')}</span>
        </div>
      </div>

      {/* Search at the top */}
      <div className="mb-6">
        <label className="block text-sm font-bold text-gray-800 mb-3 tracking-wide">{translate('ট্রেন্ডিং শব্দ খুঁজুন')}</label>
        <div className="relative">
          <input 
            type="text" 
            placeholder="ফ্রেজ বা শব্দ দিয়ে খুঁজুন... (Ctrl+K চেপে খুঁজুন)" 
            value={searchInput} 
            onChange={e => handleSearchInputChange(e.target.value)} 
            className="w-full border-2 border-gray-300 rounded-xl px-4 py-3 pl-12 pr-32 focus:outline-none focus:ring-4 focus:ring-blue-400/50 focus:border-blue-500 transition-all duration-300 bg-white text-slate-800 shadow-lg hover:shadow-xl font-medium"
          />
          <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 gap-2">
            <button
              onClick={handleSearchSubmit}
              disabled={!searchInput.trim()}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                searchInput.trim() 
                  ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg' 
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              {translate('খুঁজুন')}
            </button>
            <kbd className="hidden sm:inline-block px-2 py-1 text-xs font-semibold text-gray-500 bg-gray-100 border border-gray-300 rounded">
              {translate('Enter')}
            </kbd>
          </div>
        </div>
        {filters.search && (
          <div className="mt-2 flex items-center gap-2">
            <span className="text-sm text-blue-600 font-medium">Searched: "{filters.search}"</span>
            <button
              onClick={() => {
                setSearchInput('');
                setFilters(prev => ({ ...prev, search: '' }));
              }}
              className="text-xs text-red-600 hover:text-red-800 underline"
            >
              Clear Search
            </button>
          </div>
        )}
      </div>
      
      {/* Quick Date Selection above date inputs */}
      <div className="mb-6">
        <label className="block text-sm font-bold text-gray-800 mb-3 tracking-wide">{translate('সর্ব তারিখ নির্বাচন')}</label>
        <div className="flex flex-wrap gap-2">
           <button 
             onClick={() => setFilters(prev => ({ ...prev, start_date: 'all', end_date: 'all' }))} 
             className="px-4 py-2 bg-gradient-to-r from-gray-500 to-gray-600 text-white rounded-lg text-sm font-semibold shadow-md hover:shadow-lg transition-all hover:scale-105"
           >
             {translate('সব')}
           </button>
          <button 
            onClick={() => setDateRange(1)} 
            className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg text-sm font-semibold shadow-md hover:shadow-lg transition-all hover:scale-105"
          >
            {translate('আজ')}
          </button>
          <button 
            onClick={() => setDateRange(7)} 
            className="px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg text-sm font-semibold shadow-md hover:shadow-lg transition-all hover:scale-105"
          >
            {translate('গত ৭ দিন')}
          </button>
          <button 
            onClick={() => setDateRange(30)} 
            className="px-4 py-2 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg text-sm font-semibold shadow-md hover:shadow-lg transition-all hover:scale-105"
          >
            {translate('গত ৩০ দিন')}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <div className="relative">
          <label className="block text-sm font-bold text-gray-800 mb-3 tracking-wide">{translate('ভর তারিখ')}</label>
          <input 
            type="date" 
            value={filters.start_date === 'all' ? '' : filters.start_date} 
            onChange={e => handleFilterChange('start_date', e.target.value)} 
            max={filters.end_date && filters.end_date !== 'all' ? filters.end_date : formatDate(new Date())}
            className="w-full border-2 border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-4 focus:ring-blue-400/50 focus:border-blue-500 transition-all duration-300 bg-white text-slate-800 shadow-lg hover:shadow-xl font-medium"
          />
        </div>
        <div className="relative">
          <label className="block text-sm font-bold text-gray-800 mb-3 tracking-wide">{translate('শেষ তারিখ')}</label>
          <input 
            type="date" 
            value={filters.end_date === 'all' ? '' : filters.end_date} 
            onChange={e => handleFilterChange('end_date', e.target.value)} 
            min={filters.start_date && filters.start_date !== 'all' ? filters.start_date : undefined}
            max={formatDate(new Date())}
            className="w-full border-2 border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-4 focus:ring-blue-400/50 focus:border-blue-500 transition-all duration-300 bg-white text-slate-800 shadow-lg hover:shadow-xl font-medium"
          />
        </div>
        <div>
          <label className="block text-sm font-bold text-gray-800 mb-3 tracking-wide">{translate('উৎস')}</label>
          <select 
            value={filters.source} 
            onChange={e => handleFilterChange('source', e.target.value)} 
            className="w-full border-2 border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-4 focus:ring-blue-400/50 focus:border-blue-500 transition-all duration-300 bg-white text-slate-800 shadow-lg hover:shadow-xl font-medium cursor-pointer"
          >
            <option value="" className="text-slate-600 font-medium">{translate('সব')}</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-bold text-gray-800 mb-3 tracking-wide">{translate('ধরন')}</label>
          <select 
            value={filters.phrase_type} 
            onChange={e => handleFilterChange('phrase_type', e.target.value)} 
            className="w-full border-2 border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-4 focus:ring-blue-400/50 focus:border-blue-500 transition-all duration-300 bg-white text-slate-800 shadow-lg hover:shadow-xl font-medium cursor-pointer"
          >
            <option value="" className="text-slate-600 font-medium">{translate('সব')}</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-bold text-gray-800 mb-3 tracking-wide">{translate('সীমা')}</label>
          <input 
            type="number" 
            min={10} 
            max={200} 
            value={filters.limit} 
            onChange={e => handleFilterChange('limit', parseInt(e.target.value))} 
            className="w-full border-2 border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-4 focus:ring-blue-400/50 focus:border-blue-500 transition-all duration-300 bg-white text-slate-800 shadow-lg hover:shadow-xl font-medium" 
          />
        </div>
      </div>
    </div>
  );

  const LoadingSkeleton = () => (
    <div className="space-y-4 animate-pulse">
      {[...Array(5)].map((_, idx) => (
        <div key={idx} className="bg-gradient-to-r from-gray-200 to-gray-300 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="h-6 bg-gray-300 rounded-md w-2/3"></div>
            <div className="h-6 bg-blue-300 rounded-full w-16"></div>
          </div>
          <div className="flex gap-2">
            <div className="h-4 bg-gray-200 rounded-full w-20"></div>
            <div className="h-4 bg-blue-200 rounded-full w-16"></div>
            <div className="h-4 bg-pink-200 rounded-full w-18"></div>
          </div>
        </div>
      ))}
    </div>
  );

  // Function to get frequency-based color
  const getFrequencyColor = (frequency) => {
    if (frequency >= 10) return 'bg-gradient-to-r from-red-500 to-red-600 text-white';
    if (frequency >= 5) return 'bg-gradient-to-r from-orange-500 to-orange-600 text-white';
    if (frequency >= 3) return 'bg-gradient-to-r from-yellow-500 to-yellow-600 text-white';
    if (frequency >= 2) return 'bg-gradient-to-r from-blue-500 to-blue-600 text-white';
    return 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800';
  };

  const renderTrendingTab = () => {
    if (loading && (!trendingData || !trendingData.phrases)) {
      return <LoadingSkeleton />;
    }
    
    if (!trendingData || !trendingData.phrases) {
      return <div className="bg-gradient-to-r from-blue-100 to-blue-200 border-2 border-blue-300 text-blue-900 px-8 py-6 rounded-2xl text-center shadow-2xl">
        <div className="flex items-center justify-center gap-3">
          <TrendingUp className="w-6 h-6 drop-shadow-sm" />
          <span className="font-bold text-lg">কোনো ট্রেন্ডিং ডেটা পাওয়া যায়নি। প্রথমে বিশ্লেষণ চালান।</span>
        </div>
      </div>;
    }
  // ...existing code...
    
    // Filter phrases based on search term
    const filteredPhrases = trendingData.phrases.filter(phrase => 
      filters.search === '' || 
      phrase.phrase.toLowerCase().includes(filters.search.toLowerCase()) ||
      phrase.phrase_type.toLowerCase().includes(filters.search.toLowerCase()) ||
      phrase.source.toLowerCase().includes(filters.search.toLowerCase())
    );
    
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2 bg-gradient-to-br from-white to-gray-50 shadow-2xl rounded-2xl p-8 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-black text-gray-900 tracking-tight">{translate('শীর্ষ ট্রেন্ডিং ক্রেজ')}</h2>
            <button
              onClick={() => {
                // Export only phrase, frequency, date
                const csvRows = [
                  ['phrase', 'frequency', 'date'],
                  ...filteredPhrases.map(p => [p.phrase, p.frequency, p.date])
                ];
                const csvContent = csvRows.map(e => e.join(",")).join("\n");
                const blob = new Blob([csvContent], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'trending_phrases.csv';
                a.click();
                URL.revokeObjectURL(url);
              }}
              disabled={!filteredPhrases.length || loading}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 shadow-md focus:outline-none focus:ring-2 transform hover:scale-105 ${
                !filteredPhrases.length || loading
                  ? 'bg-gray-200 text-gray-500 cursor-not-allowed' 
                  : 'bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white focus:ring-green-400 hover:shadow-lg'
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>{translate('Export CSV')}</span>
            </button>
          </div>
          <div className="text-slate-600 mb-4 font-semibold">
            {trendingData.start_date} থেকে {trendingData.end_date} | 
            মোট: {trendingData.pagination?.total || 0}টি | 
            {filters.search && (
              <span className="text-blue-600">ফিল্টার করা: {filteredPhrases.length}টি</span>
            )}
          </div>
          <div className="space-y-0">
            {filteredPhrases.map((phrase, idx) => (
              <div key={idx} className="phrase-separator py-5 px-4 flex flex-col gap-3 hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 rounded-xl transition-all duration-300 group hover:shadow-lg hover:scale-[1.01] hover:z-10 relative">
                <div className="flex items-center gap-3">
                  <span 
                    className="text-xl font-bold text-gray-900 group-hover:text-blue-900 transition-colors cursor-pointer hover:underline flex items-center gap-2"
                    onClick={() => openPhraseGraphModal(phrase.phrase)}
                    title={`ফ্রিকোয়েন্সি গ্রাফ দেখুন | তারিখ: ${phrase.date}`}
                  >
                    {phrase.phrase}
                    <BarChart3 className="w-4 h-4 text-blue-500 opacity-60 group-hover:opacity-100 transition-opacity" />
                    <span className="text-xs text-gray-500 font-medium opacity-0 group-hover:opacity-100 transition-opacity bg-gray-100 px-2 py-1 rounded">
                      {phrase.date}
                    </span>
                  </span>
                  {/* <span className={`inline-block px-3 py-1 rounded-full text-sm font-bold shadow-lg transition-all group-hover:scale-105 ${getScoreColor(phrase.score) === 'primary' ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white' : getScoreColor(phrase.score) === 'secondary' ? 'bg-gradient-to-r from-pink-500 to-pink-600 text-white' : 'bg-gradient-to-r from-gray-500 to-gray-600 text-white'}`}>{phrase.score.toFixed(2)}</span> */}
                </div>
                <div className="flex flex-wrap gap-2 mt-1">
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold shadow-md hover:shadow-lg transition-all group-hover:scale-105 ${getFrequencyColor(phrase.frequency)}`}>
                    ফ্রিকোয়েন্সি: {phrase.frequency}
                    {phrase.frequency > 1 && (
                      <span className="ml-1 text-xs"></span>
                    )}
                    {phrase.frequency >= 5 && (
                      <span className="ml-1 text-xs"></span>
                    )}
                    {phrase.frequency >= 10 && (
                      <span className="ml-1 text-xs"></span>
                    )}
                  </span>
                </div>
                {/* Admin delete button */}
                {isAdmin && (
                  <button
                    onClick={() => openDeleteModal(phrase.id, phrase.phrase, phrase.frequency)}
                    className="absolute top-3 right-3 p-2 rounded-full bg-red-500 text-white shadow-md hover:bg-red-600 transition-all duration-300"
                    title="মুছে ফেলুন"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
          
          {/* Enhanced Pagination Controls */}
          {trendingData?.pagination && totalPages > 1 && (
            <div className="flex justify-center items-center gap-2 mt-8 p-4 flex-wrap">
              {/* Previous Button */}
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className={`px-3 py-2 rounded-lg font-semibold transition-all ${
                  currentPage === 1 
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed' 
                    : 'bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg'
                }`}
              >
                ← পূর্ববর্তী
              </button>
              
              {/* Page Numbers with Improved Logic */}
              <div className="flex gap-1 mx-2">
                {/* Always show page 1 */}
                <button
                  onClick={() => setCurrentPage(1)}
                  className={`px-3 py-2 rounded-lg font-semibold transition-all ${
                    currentPage === 1 
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'bg-gray-100 text-gray-700 hover:bg-blue-100'
                  }`}
                >
                  1
                </button>
                
                {/* Show dots if needed after page 1 */}
                {currentPage > 3 && (
                  <span className="px-2 py-2 text-gray-500">...</span>
                )}
                
                {/* Show pages around current page */}
                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter(page => {
                    // Show pages around current page (but not 1 or last page)
                    return page > 1 && page < totalPages && Math.abs(page - currentPage) <= 1;
                  })
                  .map(page => (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`px-3 py-2 rounded-lg font-semibold transition-all ${
                        page === currentPage 
                          ? 'bg-blue-600 text-white shadow-lg' 
                          : 'bg-gray-100 text-gray-700 hover:bg-blue-100'
                      }`}
                    >
                      {page}
                    </button>
                  ))
                }
                
                {/* Show dots if needed before last page */}
                {currentPage < totalPages - 2 && totalPages > 2 && (
                  <span className="px-2 py-2 text-gray-500">...</span>
                )}
                
                {/* Always show last page (if more than 1 page) */}
                {totalPages > 1 && (
                  <button
                    onClick={() => setCurrentPage(totalPages)}
                    className={`px-3 py-2 rounded-lg font-semibold transition-all ${
                      currentPage === totalPages 
                        ? 'bg-blue-600 text-white shadow-lg' 
                        : 'bg-gray-100 text-gray-700 hover:bg-blue-100'
                    }`}
                  >
                    {totalPages}
                  </button>
                )}
              </div>
              
              {/* Next Button */}
              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className={`px-3 py-2 rounded-lg font-semibold transition-all ${
                  currentPage === totalPages 
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed' 
                    : 'bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg'
                }`}
              >
                পরবর্তী →
              </button>
              
              {/* Page Info */}
              <div className="text-sm text-gray-600 ml-4">
                মোট {trendingData.pagination.total}টি | পৃষ্ঠা {currentPage}/{totalPages}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderDailyTab = () => {
    if (loading && !dailyData) {
      return <LoadingSkeleton />;
    }
    
    if (!dailyData) {
      return <div className="bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 text-blue-800 px-6 py-4 rounded-xl text-center shadow-sm">
        <div className="flex items-center justify-center gap-2">
          <Globe className="w-5 h-5 animate-pulse" />
          <span>দৈনিক ডেটা লোড করা হচ্ছে...</span>
        </div>
      </div>;
    }
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-bold mb-2">দৈনিক সারসংক্ষেপ - {dailyData.date}</h2>
          <div className="text-gray-500 mb-2">মোট ফ্রেজ: {dailyData.total_phrases}টি</div>
          <ul className="divide-y divide-gray-200">
            {dailyData.top_phrases.map((phrase, idx) => (
              <li key={idx} className="py-2 flex flex-col gap-1">
                <span className="font-medium">{phrase.phrase}</span>
                <span className="text-xs text-gray-500">ফ্রিকোয়েন্সি: {phrase.frequency}</span>
              </li>
            ))}
          </ul>
        </div>
      
      </div>
    );
  };

  const renderWeeklyTab = () => {
    if (loading && !weeklyData) {
      return <LoadingSkeleton />;
    }
    
    if (!weeklyData || weeklyData.total_phrases === 0) {
      return <div className="bg-gradient-to-r from-yellow-50 to-yellow-100 border border-yellow-200 text-yellow-800 px-6 py-4 rounded-xl text-center shadow-sm">
        <div className="flex items-center justify-center gap-2">
          <Calendar className="w-5 h-5" />
          <span>কোনো সাপ্তাহিক ডেটা পাওয়া যায়নি। প্রথমে বিশ্লেষণ চালান।</span>
        </div>
      </div>;
    }
    
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="mb-4">
          <h2 className="text-lg font-bold mb-2">সাপ্তাহিক সারসংক্ষেপ - {weeklyData.week_start} থেকে {weeklyData.week_end}</h2>          
          <div className="text-gray-500 mb-2">মোট ফ্রেজ: {weeklyData.total_phrases}টি</div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Top Weekly Phrases */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="font-semibold mb-4">শীর্ষ সাপ্তাহিক ফ্রেজ</h3>
            <ul className="divide-y divide-gray-200">
              {weeklyData.top_weekly_phrases.slice(0, 10).map((phrase, idx) => (
                <li key={idx} className="py-2 flex flex-col gap-1">
                  <span className="font-medium">{phrase.phrase}</span>
                  <div className="flex gap-2 text-xs text-gray-500">
                    <span>তারিখ: {phrase.date}</span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
          
          {/* Daily Breakdown */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="font-semibold mb-4">Daily Breakdown</h3>
            <div className="space-y-3">
              {Object.entries(weeklyData.daily_breakdown).map(([date, phrases]) => (
                <div key={date} className="border-l-4 border-blue-400 pl-3">
                  <div className="font-medium">{date}</div>
                  <div className="text-sm text-gray-500">{phrases.length}টি ফ্রেজ</div>
                  <div className="text-xs text-gray-400 mt-1">
                    {phrases.slice(0, 3).map(p => p.phrase).join(', ')}
                    {phrases.length > 3 && '...'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderStatsTab = () => {
    if (loading && !stats) {
      return <LoadingSkeleton />;
    }
    
    if (!stats) {
      return <div className="bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 text-blue-800 px-6 py-4 rounded-xl text-center shadow-sm">
        <div className="flex items-center justify-center gap-2">
          <Users className="w-5 h-5 animate-pulse" />
          <span>পরিসংখ্যান লোড করা হচ্ছে...</span>
        </div>
      </div>;
    }
    if (stats.total_phrases === 0) {
      return <div className="bg-gradient-to-r from-yellow-50 to-yellow-100 border border-yellow-200 text-yellow-800 px-6 py-4 rounded-xl text-center shadow-sm">
        <div className="flex items-center justify-center gap-2">
          <Users className="w-5 h-5" />
          <span>{stats.message || 'কোনো পরিসংখ্যান পাওয়া যায়নি। প্রথমে বিশ্লেষণ চালান।'}</span>
        </div>
      </div>;
    }
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-bold mb-2">সামগ্রিক পরিসংখ্যান</h2>
          <div className="text-3xl font-extrabold text-blue-600">{stats.total_phrases}</div>
          <div className="text-gray-500 mb-2">মোট ট্রেন্ডিং ফ্রেজ</div>
          <div className="text-2xl font-bold text-pink-600 mt-4">{stats.recent_phrases_7_days}</div>
          <div className="text-gray-500">গত ৭ দিনের ফ্রেজ</div>
        </div>
        
      </div>
    );
  };

  if (loading && tabValue === 0) {
    return (
      <div className="max-w-5xl mx-auto mt-16 text-center">
        <div className="flex flex-col items-center justify-center">
          <svg className="animate-spin h-16 w-16 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
          <p className="mt-4 text-lg font-medium text-gray-700">Analysis running...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-6 py-8 bg-gradient-to-br from-gray-50 to-white min-h-[calc(100vh-4rem)]">
      <div className="text-center mb-6">
        <h1 className="text-3xl font-black tracking-tight text-gray-900 mb-2 flex items-center justify-center gap-3">
          <div className="p-2 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl shadow-lg">
            <TrendingUp className="w-6 h-6 text-white" />
          </div>
          {translate('ট্রেন্ডিং বিশ্লেষণ')}
        </h1>
        {/* <p className="text-sm text-gray-600 font-medium">বাংলা সংবাদ ও সোশ্যাল মিডিয়া থেকে ট্রেন্ডিং শব্দ ও বাক্যাংশ</p> */}
      </div>
      {error && (
        <div className="bg-gradient-to-r from-red-50 to-red-100 border-2 border-red-300 text-red-800 px-6 py-4 rounded-2xl mb-6 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="font-semibold">{error}</span>
              {retryCount > 0 && (
                <span className="text-sm text-red-600 bg-red-200 px-2 py-1 rounded-full">
                  Attempt #{retryCount}
                </span>
              )}
            </div>
            <button
              onClick={retryAction}
              className="px-4 py-2 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-lg text-sm font-semibold shadow-md hover:shadow-lg transition-all hover:scale-105 focus:outline-none focus:ring-2 focus:ring-red-400"
            >
              Retry Again
            </button>
          </div>
        </div>
      )}
      <div className="flex border border-gray-200 mb-8 max-w-5xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden backdrop-blur-sm">
        {[
          { label: translate("ট্রেন্ডিং ক্রেজ"), icon: TrendingUp },
          { label: translate("দৈনিক সারসংক্ষেপ"), icon: Globe },
          { label: translate("সাপ্তাহিক সারসংক্ষেপ"), icon: Calendar },
          { label: translate("পরিসংখ্যান"), icon: Users }
        ].map(({ label, icon: Icon }, idx) => (
          <button
            key={idx}
            className={`flex-1 py-4 px-6 text-center font-bold transition-all duration-300 border-b-4 flex items-center justify-center gap-3 cursor-pointer relative overflow-hidden ${
              tabValue === idx 
                ? 'border-blue-600 text-blue-800 bg-gradient-to-br from-blue-50 to-blue-100 shadow-inner transform scale-[0.98]' 
                : 'border-transparent text-slate-700 bg-gradient-to-br from-slate-200 to-slate-300 hover:from-blue-50 hover:to-blue-100 hover:text-blue-700 hover:border-blue-300 shadow-md hover:shadow-lg hover:scale-[1.02] active:scale-[0.98]'
            }`}
            onClick={() => handleTabChange(idx)}
          >
            <Icon className="w-5 h-5 drop-shadow-sm" />
            <span className="text-sm font-semibold tracking-wide">{label}</span>
          </button>
        ))}
      </div>
      {renderFilters()}
      {loading ? (
        <div className="flex justify-center p-8"><svg className="animate-spin h-8 w-8 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg></div>
      ) : (
        <>
          {tabValue === 0 && renderTrendingTab()}
          {tabValue === 1 && renderDailyTab()}
          {tabValue === 2 && renderWeeklyTab()}
          {tabValue === 3 && renderStatsTab()}
        </>
      )}
      
      {/* Toast Notification */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg transition-all duration-300 transform ${
          toast.type === 'success' 
            ? 'bg-gradient-to-r from-green-500 to-green-600 text-white' 
            : 'bg-gradient-to-r from-red-500 to-red-600 text-white'
        }`}>
          <div className="flex items-center gap-3">
            {toast.type === 'success' ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
            <span className="font-semibold">{toast.message}</span>
          </div>
        </div>
      )}
      
      {/* Progressive Analysis Modal */}
      {showProgressiveAnalysis && (
        <ProgressiveAnalysis
          key="progressive-analysis-modal" // Add stable key to prevent remounting
          onAnalysisComplete={handleProgressiveAnalysisComplete}
          onClose={handleProgressiveAnalysisClose}
        />
      )}

      {/* Phrase Graph Modal */}
      {phraseGraphModal.isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl">
                    <BarChart3 className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">ফ্রিকোয়েন্সি গ্রাফ</h2>
                    <p className="text-sm text-gray-600">"{phraseGraphModal.phrase}"</p>
                  </div>
                </div>
                <button
                  onClick={closePhraseGraphModal}
                  className="p-2 rounded-full hover:bg-gray-100 transition-colors"
                >
                  <X className="w-6 h-6 text-gray-500" />
                </button>
              </div>
            </div>
            
            <div className="p-6">
              {phraseGraphLoading ? (
                <div className="flex items-center justify-center py-20">
                  <div className="flex flex-col items-center gap-4">
                    <svg className="animate-spin h-12 w-12 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                    </svg>
                    <p className="text-gray-600 font-medium">ডেটা লোড হচ্ছে...</p>
                  </div>
                </div>
              ) : phraseGraphModal.data.length > 0 ? (
                <div className="space-y-6">
                  {/* Chart */}
                  <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">তারিখ অনুযায়ী ফ্রিকোয়েন্সি</h3>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={phraseGraphModal.data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                          <XAxis 
                            dataKey="date" 
                            tick={{ fontSize: 12 }}
                            tickFormatter={(value) => {
                              const date = new Date(value);
                              return `${date.getMonth() + 1}/${date.getDate()}`;
                            }}
                          />
                          <YAxis 
                            tick={{ fontSize: 12 }} 
                            allowDecimals={false}
                            domain={[0, 'dataMax + 1']}
                            tickCount={6}
                          />
                          <Tooltip 
                            formatter={(value, name) => [value, name === 'frequency' ? 'ফ্রিকোয়েন্সি' : 'অন্যান্য']}
                            labelFormatter={(label) => `তারিখ: ${label}`}
                            contentStyle={{
                              backgroundColor: '#f9fafb',
                              border: '1px solid #e5e7eb',
                              borderRadius: '8px',
                              fontSize: '14px'
                            }}
                          />
                          <Line 
                            type="monotone" 
                            dataKey="frequency" 
                            stroke="#3b82f6" 
                            strokeWidth={3}
                            dot={{ fill: '#3b82f6', strokeWidth: 2, r: 6 }}
                            activeDot={{ r: 8, fill: '#1d4ed8' }}
                            connectNulls={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                  
                  {/* Data Table */}
                  {/* <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                    <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-b">
                      <h3 className="text-lg font-semibold text-gray-900">বিস্তারিত ডেটা</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">তারিখ</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ফ্রিকোয়েন্সি</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">স্কোর</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">উৎস</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ধরন</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {phraseGraphModal.data.map((item, idx) => (
                            <tr key={idx} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.date}</td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getFrequencyColor(item.frequency)}`}>
                                  {item.frequency}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.score}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.source}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.phrase_type}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div> */}
                </div>
              ) : (
                <div className="text-center py-20">
                  <div className="flex flex-col items-center gap-4">
                    <div className="p-4 bg-gray-100 rounded-full">
                      <BarChart3 className="w-12 h-12 text-gray-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">There is no frequency data available for this phrase.</h3>
                      <p className="text-gray-600">No frequency data found for this phrase.</p>
                      <p className="text-sm text-gray-500 mt-2">Please try again later.</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Delete Confirmation Modal */}
      {deleteModal.isOpen && (
        <ConfirmationModal
          isOpen={deleteModal.isOpen}
          title="Remove the phrase"
          message={`Are you sure you want to remove the phrase "${deleteModal.phraseName}"?

Current frequency: ${deleteModal.frequency}

${deleteModal.frequency > 1
  ? `⚠️ Since the frequency is ${deleteModal.frequency}, it will not be completely removed, but rather the frequency will be decreased to ${deleteModal.frequency - 1}.`
  : '⚠️ It will be completely removed.'
}

Please proceed with caution.`}
          confirmText={deleteModal.frequency > 1 ? "Decrease Frequency" : "Remove Completely"}
          cancelText="Cancel"
          type="danger"
          onClose={() => setDeleteModal({ isOpen: false, phraseId: null, phraseName: '', frequency: 0 })}
          onConfirm={async () => {
            // Handle delete action
            try {
              setLoading(true);
              const response = await apiV2.deleteTrendingPhrase(deleteModal.phraseId);
              
              if (response.action === 'frequency_decreased') {
                showToast(`'${deleteModal.phraseName}' frequency has been decreased to ${response.remaining_frequency}`, 'success');
              } else {
                showToast(`'${deleteModal.phraseName}' has been completely removed`, 'success');
              }
              
              setDeleteModal({ isOpen: false, phraseId: null, phraseName: '', frequency: 0 });
              // Refetch data
              if (tabValue === 0) {
                await fetchTrendingData();
              } else if (tabValue === 1) {
                await fetchDailyData();
              } else if (tabValue === 2) {
                await fetchWeeklyData();
              } else if (tabValue === 3) {
                await fetchStats();
              }
            } catch (err) {
              console.error('Delete phrase error:', err);
              showToast('Failed to delete phrase', 'error');
            } finally {
              setLoading(false);
            }
          }}
        />
      )}
    </div>
  );
}

export default TrendingAnalysis;
