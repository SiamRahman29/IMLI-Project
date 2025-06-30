import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';
const API_V2_BASE_URL = 'http://localhost:8000/api/v2';

// Create axios instances
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

const apiV2Client = axios.create({
  baseURL: API_V2_BASE_URL,
  timeout: 2 * 60 * 60 * 1000, // 2 hours
});

// API functions for legacy endpoints
export const api = {
  // Legacy word of the day
  getWordOfTheDay: () => apiClient.get('/'),
  
  // Legacy generate candidates
  generateCandidates: () => apiClient.post('/generate_candidates'),
  
  // Legacy set word of the day
  setWordOfTheDay: (word) => apiClient.post(`/set_word_of_the_day?word=${encodeURIComponent(word)}`),
};

// API functions for v2 endpoints
export const apiV2 = {
  // Get word of the day
  getWordOfTheDay: () => apiV2Client.get('/'),
  
  // Generate candidates and run analysis
  generateCandidates: () => apiV2Client.post('/generate_candidates'),
  
  // Hybrid generate candidates with separate API keys
  hybridGenerateCandidates: (params = {}) => {
    const queryParams = new URLSearchParams();
    
    if (params.sources) {
      params.sources.forEach(source => queryParams.append('sources', source));
    }
    if (params.mode) queryParams.append('mode', params.mode);
    
    return apiV2Client.post(`/api/generate-candidates?${queryParams.toString()}`);
  },
  
  // Get trending phrases with filtering
  getTrendingPhrases: (params = {}) => {
    const queryParams = new URLSearchParams();
    
    if (params.start_date) queryParams.append('start_date', params.start_date);
    if (params.end_date) queryParams.append('end_date', params.end_date);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.source) queryParams.append('source', params.source);
    if (params.phrase_type) queryParams.append('phrase_type', params.phrase_type);
    
    return apiV2Client.get(`/trending-phrases?${queryParams.toString()}`);
  },
  
  // Get daily trending summary
  getDailyTrending: (targetDate = null) => {
    const params = targetDate ? `?target_date=${targetDate}` : '';
    return apiV2Client.get(`/daily-trending${params}`);
  },
  
  // Get weekly trending summary
  getWeeklyTrending: (targetWeek = null) => {
    const params = targetWeek ? `?target_week=${targetWeek}` : '';
    return apiV2Client.get(`/weekly-trending${params}`);
  },
  
  // Get monthly trending summary
  getMonthlyTrending: (targetMonth = null) => {
    const params = targetMonth ? `?target_month=${targetMonth}` : '';
    return apiV2Client.get(`/monthly-trending${params}`);
  },
  
  // Set word of the day (enhanced with category support)
  setWordOfTheDay: (word) => {
    const params = new URLSearchParams({ word });
    return apiV2Client.post(`/set_word_of_the_day?${params.toString()}`);
  },

  // Set category words with full category information
  setCategoryWords: (words) => {
    return apiV2Client.post('/set_category_words', { words });
  },

  // Run trending analysis
  runAnalysis: () => apiV2Client.post('/analyze'),
  
  // Get available sources and metadata (enhanced with detailed stats)
  getSources: () => apiV2Client.get('/sources'),
  
  // Get statistics
  getStats: () => apiV2Client.get('/stats'),
};

// Helper functions
export const formatDate = (date) => {
  return new Date(date).toISOString().split('T')[0];
};

export const getScoreColor = (score) => {
  if (score > 8) return 'error';
  if (score > 5) return 'warning';
  if (score > 3) return 'info';
  return 'default';
};

export const groupPhrasesByType = (phrases) => {
  return phrases.reduce((acc, phrase) => {
    if (!acc[phrase.phrase_type]) {
      acc[phrase.phrase_type] = [];
    }
    acc[phrase.phrase_type].push(phrase);
    return acc;
  }, {});
};

export const groupPhrasesBySource = (phrases) => {
  return phrases.reduce((acc, phrase) => {
    if (!acc[phrase.source]) {
      acc[phrase.source] = [];
    }
    acc[phrase.source].push(phrase);
    return acc;
  }, {});
};

export default { api, apiV2 };