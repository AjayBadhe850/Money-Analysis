import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for attaching auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('money_analysis_token') || localStorage.getItem('costwise_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for centralized error response handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // If unauthorized, clear local session if token is expired
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        localStorage.removeItem('money_analysis_token');
        localStorage.removeItem('money_analysis_user');
        localStorage.removeItem('costwise_token');
        localStorage.removeItem('costwise_user');
      }
    }
    return Promise.reject(error);
  }
);

export default api;
