import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ? process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, '') : '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true'
  },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 401 globally – redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (typeof window !== 'undefined' && error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const documentApi = {
  uploadMultiple: (files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    return api.post('/documents/upload-multiple', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  list: (search?: string, tagId?: number) => {
    return api.get('/documents', {
      params: { search, tag_id: tagId },
    });
  },
  delete: (id: number) => {
    return api.delete(`/documents/${id}`);
  },
  getTags: () => {
    return api.get('/documents/tags');
  },
  createTag: (name: string, color: string) => {
    return api.post('/documents/tags', { name, color });
  },
  assignTag: (docId: number, tagId: number) => {
    return api.post(`/documents/${docId}/tags/${tagId}`);
  },
};

export default api;
