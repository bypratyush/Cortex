import axios from 'axios';
import { useAuthStore } from '../store/useAuthStore';

// Create an Axios instance
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach the X-User-Id header for every request
api.interceptors.request.use(
  (config) => {
    // We fetch the latest userId from the Zustand store
    const userId = useAuthStore.getState().userId;
    if (userId) {
      config.headers['X-User-Id'] = userId;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;
