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

// Add auth interceptor to include JWT token
apiV2Client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle token expiration
apiV2Client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_data');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

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
    if (params.offset) queryParams.append('offset', params.offset);
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
  
  // Authentication endpoints
  login: (credentials) => apiV2Client.post('/auth/login', credentials),
  forgotPassword: (email) => apiV2Client.post('/auth/forgot-password', { email }),
  resetPassword: (resetData) => apiV2Client.post('/auth/reset-password', resetData),
  getCurrentUser: () => apiV2Client.get('/auth/me'),
  inviteUser: (inviteData) => apiV2Client.post('/auth/invite', inviteData),
  getUsers: () => apiV2Client.get('/auth/users'),
  deactivateUser: (userId) => apiV2Client.post(`/auth/users/${userId}/deactivate`),
  activateUser: (userId) => apiV2Client.post(`/auth/users/${userId}/activate`),
  updateProfile: (profileData) => apiV2Client.put('/auth/profile', profileData),
  deleteUser: (userId) => apiV2Client.delete(`/auth/users/${userId}`),
  
  // Trending phrases management
  deleteTrendingPhrase: (phraseId) => apiV2Client.delete(`/trending-phrases/${phraseId}`),
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

export default { api, apiV2};

// Named exports for commonly used functions
export const login = apiV2.login;
export const forgotPassword = apiV2.forgotPassword;
export const resetPassword = apiV2.resetPassword;
export const getCurrentUser = apiV2.getCurrentUser;

// Auth helper functions
export const authUtils = {
  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  },
  
  getUser: () => {
    const userData = localStorage.getItem('user_data');
    return userData ? JSON.parse(userData) : null;
  },
  
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    window.location.href = '/login';
  },
  
  hasPermission: (permission) => {
    const user = authUtils.getUser();
    return user?.permissions?.includes(permission) || user?.role === 'admin';
  },
  
  isAdmin: () => {
    const user = authUtils.getUser();
    return user?.role === 'admin';
  }
};