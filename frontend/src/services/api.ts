import axios from 'axios';
import type {
  User,
  Workflow,
  WorkflowCreate,
  WorkflowUpdate,
  Execution,
  APIKey,
  APIKeyCreate,
  Token,
  NodeTypeInfo,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      localStorage.removeItem('access_token');
      window.location.href = '/login';
      return Promise.reject(error);
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data: { email: string; username: string; password: string }): Promise<User> =>
    api.post('/api/auth/register', data).then((res) => res.data),
  login: (username: string, password: string): Promise<Token> =>
    api.post('/api/auth/login', { username, password }).then((res) => res.data),
  getCurrentUser: (): Promise<User> =>
    api.get('/api/auth/me').then((res) => res.data),
};

// Workflows API
export const workflowsAPI = {
  getAll: (skip?: number, limit?: number): Promise<Workflow[]> =>
    api.get(`/api/workflows/?skip=${skip || 0}&limit=${limit || 100}`).then((res) => res.data),
  getById: (id: number): Promise<Workflow> =>
    api.get(`/api/workflows/${id}`).then((res) => res.data),
  create: (data: WorkflowCreate): Promise<Workflow> =>
    api.post('/api/workflows/', data).then((res) => res.data),
  update: (id: number, data: WorkflowUpdate): Promise<Workflow> =>
    api.put(`/api/workflows/${id}`, data).then((res) => res.data),
  delete: (id: number): Promise<void> =>
    api.delete(`/api/workflows/${id}`).then(() => {}),
  run: (workflow_id: number, input_data?: Record<string, any>): Promise<Execution> =>
    executionAPI.run(workflow_id, input_data),
};

// Execution API
export const executionAPI = {
  run: (workflow_id: number, input_data?: Record<string, any>): Promise<Execution> =>
    api.post('/api/execution/run', { workflow_id, input_data }).then((res) => res.data),
  getAll: (workflow_id?: number, skip?: number, limit?: number): Promise<Execution[]> => {
    const params = new URLSearchParams();
    if (workflow_id) params.append('workflow_id', workflow_id.toString());
    params.append('skip', (skip || 0).toString());
    params.append('limit', (limit || 100).toString());
    return api.get(`/api/execution/executions?${params.toString()}`).then((res) => res.data);
  },
  getById: (id: number): Promise<Execution> =>
    api.get(`/api/execution/executions/${id}`).then((res) => res.data),
};

// Nodes API
export const nodesAPI = {
  getTypes: (): Promise<Record<string, NodeTypeInfo>> =>
    api.get('/api/nodes/types').then((res) => res.data),
};

// API Keys API
export const apiKeysAPI = {
  getAll: (): Promise<APIKey[]> =>
    api.get('/api/keys/').then((res) => res.data),
  create: (data: APIKeyCreate): Promise<APIKey> =>
    api.post('/api/keys/', data).then((res) => res.data),
  delete: (id: number): Promise<void> =>
    api.delete(`/api/keys/${id}`).then(() => {}),
};

export default api;