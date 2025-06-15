import { useEffect, useState } from 'react';
import { apiV2, formatDate, getScoreColor, groupPhrasesByType, groupPhrasesBySource } from '../api';
import { TrendingUp, Globe, Newspaper, Users, RefreshCw, Filter } from 'lucide-react';

function TrendingAnalysis() {
  const [trendingData, setTrendingData] = useState(null);
  const [dailyData, setDailyData] = useState(null);
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
    limit: 50,
    search: ''
  });
  const [searchInput, setSearchInput] = useState('');
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
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
    if (tabValue === 0) {
      fetchTrendingData();
    } else if (tabValue === 1) {
      fetchDailyData();
    } else if (tabValue === 2) {
      fetchStats();
    }
  }, [filters, tabValue]);

  const fetchAllData = async () => {
    await Promise.all([
      fetchTrendingData(),
      fetchDailyData(),
      fetchStats()
    ]);
  };

  const fetchTrendingData = async () => {
    try {
      setLoading(true);
      const response = await apiV2.getTrendingPhrases(filters);
      setTrendingData(response.data);
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

  const runNewAnalysis = async () => {
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
      await fetchStats();
    }
  };

  const exportData = () => {
    let dataToExport = [];
    let filename = '';
    
    if (tabValue === 0 && trendingData?.phrases) {
      dataToExport = trendingData.phrases.map(phrase => ({
        'ফ্রেজ': phrase.phrase,
        'স্কোর': phrase.score,
        'ফ্রিকোয়েন্সি': phrase.frequency,
        'ধরণ': phrase.phrase_type,
        'উৎস': phrase.source,
        'তারিখ': phrase.date
      }));
      filename = `trending-phrases-${filters.start_date}-to-${filters.end_date}.csv`;
    } else if (tabValue === 1 && dailyData?.top_phrases) {
      dataToExport = dailyData.top_phrases.map(phrase => ({
        'ফ্রেজ': phrase.phrase,
        'স্কোর': phrase.score,
        'ফ্রিকোয়েন্সি': phrase.frequency,
        'ধরণ': phrase.phrase_type,
        'উৎস': phrase.source
      }));
      filename = `daily-summary-${dailyData.date}.csv`;
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
          <span className="font-black text-gray-900 text-lg tracking-tight">ফিল্টার অপশন</span>
        </div>
        
        {/* New Analysis Button - Top Right */}
        <button 
          onClick={runNewAnalysis} 
          disabled={loading} 
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all duration-300 shadow-lg focus:outline-none focus:ring-4 focus:ring-offset-2 transform hover:scale-105 active:scale-95 ${
            loading 
              ? 'bg-gradient-to-r from-gray-400 to-gray-500 text-gray-200 cursor-not-allowed' 
              : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white focus:ring-blue-400 hover:shadow-xl'
          }`}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> 
          <span className="text-sm tracking-wide">{loading ? 'বিশ্লেষণ চলছে...' : 'নতুন বিশ্লেষণ'}</span>
        </button>
      </div>

      {/* Search at the top */}
      <div className="mb-6">
        <label className="block text-sm font-bold text-gray-800 mb-3 tracking-wide">ফ্রেজ খুঁজুন</label>
        <div className="relative">
          <input 
            type="text" 
            placeholder="ফ্রেজ বা শব্দ দিয়ে খুঁজুন... (Enter চেপে খুঁজুন)" 
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
              খুঁজুন
            </button>
            <kbd className="hidden sm:inline-block px-2 py-1 text-xs font-semibold text-gray-500 bg-gray-100 border border-gray-300 rounded">
              Enter
            </kbd>
          </div>
        </div>
        {filters.search && (
          <div className="mt-2 flex items-center gap-2">
            <span className="text-sm text-blue-600 font-medium">খুঁজছেন: "{filters.search}"</span>
            <button
              onClick={() => {
                setSearchInput('');
                setFilters(prev => ({ ...prev, search: '' }));
              }}
              className="text-xs text-red-600 hover:text-red-800 underline"
            >
              মুছে ফেলুন
            </button>
          </div>
        )}
      </div>
      
      {/* Quick Date Selection above date inputs */}
      <div className="mb-6">
        <label className="block text-sm font-bold text-gray-800 mb-3 tracking-wide">দ্রুত তারিখ নির্বাচন</label>
        <div className="flex flex-wrap gap-2">
          <button 
            onClick={() => setDateRange(1)} 
            className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg text-sm font-semibold shadow-md hover:shadow-lg transition-all hover:scale-105"
          >
            আজ
          </button>
          <button 
            onClick={() => setDateRange(7)} 
            className="px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg text-sm font-semibold shadow-md hover:shadow-lg transition-all hover:scale-105"
          >
            গত ৭ দিন
          </button>
          <button 
            onClick={() => setDateRange(30)} 
            className="px-4 py-2 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg text-sm font-semibold shadow-md hover:shadow-lg transition-all hover:scale-105"
          >
            গত ৩০ দিন
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <div className="relative">
          <label className="block text-sm font-bold text-gray-800 mb-3 tracking-wide">শুরুর তারিখ</label>
          <input 
            type="date" 
            value={filters.start_date} 
            onChange={e => handleFilterChange('start_date', e.target.value)} 
            max={filters.end_date || formatDate(new Date())}
            className="w-full border-2 border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-4 focus:ring-blue-400/50 focus:border-blue-500 transition-all duration-300 bg-white text-slate-800 shadow-lg hover:shadow-xl font-medium"
          />
        </div>
        <div className="relative">
          <label className="block text-sm font-bold text-gray-800 mb-3 tracking-wide">শেষ তারিখ</label>
          <input 
            type="date" 
            value={filters.end_date} 
            onChange={e => handleFilterChange('end_date', e.target.value)} 
            min={filters.start_date}
            max={formatDate(new Date())}
            className="w-full border-2 border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-4 focus:ring-blue-400/50 focus:border-blue-500 transition-all duration-300 bg-white text-slate-800 shadow-lg hover:shadow-xl font-medium"
          />
        </div>
        <div>
          <label className="block text-sm font-bold text-gray-800 mb-3 tracking-wide">উৎস</label>
          <select 
            value={filters.source} 
            onChange={e => handleFilterChange('source', e.target.value)} 
            className="w-full border-2 border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-4 focus:ring-blue-400/50 focus:border-blue-500 transition-all duration-300 bg-white text-slate-800 shadow-lg hover:shadow-xl font-medium cursor-pointer"
          >
            <option value="" className="text-slate-600 font-medium">সব</option>
            {sources.sources.map(source => <option key={source} value={source} className="text-slate-800 font-medium">{source}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-bold text-gray-800 mb-3 tracking-wide">ধরণ</label>
          <select 
            value={filters.phrase_type} 
            onChange={e => handleFilterChange('phrase_type', e.target.value)} 
            className="w-full border-2 border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-4 focus:ring-blue-400/50 focus:border-blue-500 transition-all duration-300 bg-white text-slate-800 shadow-lg hover:shadow-xl font-medium cursor-pointer"
          >
            <option value="" className="text-slate-600 font-medium">সব</option>
            {sources.phrase_types.map(type => <option key={type} value={type} className="text-slate-800 font-medium">{type}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-bold text-gray-800 mb-3 tracking-wide">সীমা</label>
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
    const phrasesByType = groupPhrasesByType(trendingData.phrases);
    const phrasesBySource = groupPhrasesBySource(trendingData.phrases);
    
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
            <h2 className="text-2xl font-black text-gray-900 tracking-tight">শীর্ষ ট্রেন্ডিং ফ্রেজ</h2>
            <button
              onClick={exportData}
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
              <span>Export CSV</span>
            </button>
          </div>
          <div className="text-slate-600 mb-4 font-semibold">
            {trendingData.start_date} থেকে {trendingData.end_date} | 
            মোট: {trendingData.total_count}টি | 
            {filters.search && (
              <span className="text-blue-600">ফিল্টার করা: {filteredPhrases.length}টি</span>
            )}
          </div>
          <div className="space-y-0">
            {filteredPhrases.slice(0, 20).map((phrase, idx) => (
              <div key={idx} className="phrase-separator py-5 px-4 flex flex-col gap-3 hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 rounded-xl transition-all duration-300 group hover:shadow-lg hover:scale-[1.01] hover:z-10 relative">
                <div className="flex items-center gap-3">
                  <span className="text-xl font-bold text-gray-900 group-hover:text-blue-900 transition-colors">{phrase.phrase}</span>
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-bold shadow-lg transition-all group-hover:scale-105 ${getScoreColor(phrase.score) === 'primary' ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white' : getScoreColor(phrase.score) === 'secondary' ? 'bg-gradient-to-r from-pink-500 to-pink-600 text-white' : 'bg-gradient-to-r from-gray-500 to-gray-600 text-white'}`}>{phrase.score.toFixed(2)}</span>
                </div>
                <div className="flex flex-wrap gap-2 mt-1">
                  <span className="inline-block bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 px-3 py-1 rounded-full text-sm font-semibold shadow-md hover:shadow-lg transition-all group-hover:scale-105">ফ্রিকোয়েন্সি: {phrase.frequency}</span>
                  <span className="inline-block bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold shadow-md hover:shadow-lg transition-all group-hover:scale-105">{phrase.phrase_type}</span>
                  <span className="inline-block bg-gradient-to-r from-pink-100 to-pink-200 text-pink-800 px-3 py-1 rounded-full text-sm font-semibold shadow-md hover:shadow-lg transition-all group-hover:scale-105">{phrase.source}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="flex flex-col gap-8">
          <div className="bg-gradient-to-br from-white to-blue-50 shadow-2xl rounded-2xl p-6 border border-blue-200">
            <h3 className="font-black mb-4 flex items-center gap-3 text-gray-900"><Globe className="w-6 h-6 text-blue-600" /> ধরণ অনুযায়ী</h3>
            <div className="flex flex-wrap gap-3">
              {Object.entries(phrasesByType).map(([type, phrases]) => (
                <span key={type} className="inline-block border-2 border-blue-400 text-blue-800 bg-gradient-to-r from-blue-50 to-blue-100 px-4 py-2 rounded-full text-sm font-bold shadow-lg hover:shadow-xl transition-all duration-200">{type}: {phrases.length}</span>
              ))}
            </div>
          </div>
          <div className="bg-gradient-to-br from-white to-pink-50 shadow-2xl rounded-2xl p-6 border border-pink-200">
            <h3 className="font-black mb-4 flex items-center gap-3 text-gray-900"><Newspaper className="w-6 h-6 text-pink-600" /> উৎস অনুযায়ী</h3>
            <div className="flex flex-wrap gap-3">
              {Object.entries(phrasesBySource).map(([source, phrases]) => (
                <span key={source} className="inline-block border-2 border-pink-400 text-pink-800 bg-gradient-to-r from-pink-50 to-pink-100 px-4 py-2 rounded-full text-sm font-bold shadow-lg hover:shadow-xl transition-all duration-200">{source}: {phrases.length}</span>
              ))}
            </div>
          </div>
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
                <span className="text-xs text-gray-500">স্কোর: {phrase.score.toFixed(2)} | ফ্রিকোয়েন্সি: {phrase.frequency}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="flex flex-col gap-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="font-semibold mb-2">উৎস অনুযায়ী</h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(dailyData.by_source).map(([source, phrases]) => (
                <span key={source} className="inline-block border border-pink-300 text-pink-700 px-3 py-1 rounded-full text-xs font-medium">{source}: {phrases.length}</span>
              ))}
            </div>
          </div>
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="font-semibold mb-2">ধরণ অনুযায়ী</h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(dailyData.by_phrase_type).map(([type, phrases]) => (
                <span key={type} className="inline-block border border-blue-300 text-blue-700 px-3 py-1 rounded-full text-xs font-medium">{type}: {phrases.length}</span>
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
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="font-semibold mb-2">উৎস অনুযায়ী পরিসংখ্যান</h3>
          <ul className="divide-y divide-gray-200">
            {stats.by_source.map((sourceStat, idx) => (
              <li key={idx} className="py-2">
                <div className="font-medium">{sourceStat.source}</div>
                <div className="text-xs text-gray-500">সংখ্যা: {sourceStat.count} | গড় স্কোর: {sourceStat.avg_score}</div>
              </li>
            ))}
          </ul>
        </div>
        <div className="md:col-span-2 bg-white shadow rounded-lg p-6">
          <h3 className="font-semibold mb-2">ধরণ অনুযায়ী পরিসংখ্যান</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {stats.by_phrase_type.map((typeStat, idx) => (
              <div key={idx} className="bg-blue-50 rounded p-4 text-center">
                <div className="font-semibold text-blue-700">{typeStat.phrase_type}</div>
                <div className="text-2xl font-bold text-blue-600">{typeStat.count}</div>
                <div className="text-xs text-gray-500">গড় স্কোর: {typeStat.avg_score}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  if (loading && tabValue === 0) {
    return (
      <div className="max-w-5xl mx-auto mt-16 text-center">
        <div className="flex flex-col items-center justify-center">
          <svg className="animate-spin h-16 w-16 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
          <p className="mt-4 text-lg font-medium text-gray-700">বিশ্লেষণ চলছে...</p>
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
          ট্রেন্ডিং বিশ্লেষণ
        </h1>
        <p className="text-sm text-gray-600 font-medium">বাংলা সংবাদ ও সোশ্যাল মিডিয়া থেকে ট্রেন্ডিং শব্দ ও বাক্যাংশ</p>
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
                  চেষ্টা #{retryCount}
                </span>
              )}
            </div>
            <button
              onClick={retryAction}
              className="px-4 py-2 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-lg text-sm font-semibold shadow-md hover:shadow-lg transition-all hover:scale-105 focus:outline-none focus:ring-2 focus:ring-red-400"
            >
              পুনরায় চেষ্টা
            </button>
          </div>
        </div>
      )}
      <div className="flex border border-gray-200 mb-8 max-w-5xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden backdrop-blur-sm">
        {[
          { label: "ট্রেন্ডিং ফ্রেজ", icon: TrendingUp },
          { label: "দৈনিক সারসংক্ষেপ", icon: Globe },
          { label: "পরিসংখ্যান", icon: Users }
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
          {tabValue === 2 && renderStatsTab()}
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
    </div>
  );
}

export default TrendingAnalysis;
