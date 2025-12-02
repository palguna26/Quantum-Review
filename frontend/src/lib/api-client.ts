/**
 * API client with authentication and error handling.
 */
import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  User,
  RepoSummary,
  Issue,
  PRDetail,
  Notification,
  GitHubInstallation,
  GitHubInstallationReposResponse,
} from '@/types/api';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';
const AUTH_TOKEN_KEY = 'quantum_auth_token';

// Create axios instance
const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies for CORS
});

// Request interceptor to add auth token
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('[API] Request with token:', config.url, 'Headers:', config.headers);
    } else {
      console.log('[API] Request without token:', config.url);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
axiosInstance.interceptors.response.use(
  (response) => {
    console.log('[API] Response success:', response.config.url, response.status);
    return response;
  },
  (error: AxiosError) => {
    console.error('[API] Response error:', error.config?.url, error.response?.status, error.response?.data);
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem(AUTH_TOKEN_KEY);
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// Auth token management
export const auth = {
  setToken(token: string) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  },
  
  getToken(): string | null {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  },
  
  clearToken() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
  },
};

// API functions
export const api = {
  async getMe(): Promise<User> {
    const response = await axiosInstance.get<User>('/api/me');
    return response.data;
  },

  async getRepos(filter?: string): Promise<RepoSummary[]> {
    const url = filter ? `/api/repos?filter=${encodeURIComponent(filter)}` : '/api/repos';
    const response = await axiosInstance.get<RepoSummary[]>(url);
    return response.data;
  },

  async getRepo(owner: string, repo: string): Promise<RepoSummary> {
    const response = await axiosInstance.get<RepoSummary>(`/api/repos/${owner}/${repo}`);
    return response.data;
  },

  async getRepoIssues(owner: string, repo: string): Promise<Issue[]> {
    const response = await axiosInstance.get<Issue[]>(`/api/repos/${owner}/${repo}/issues`);
    return response.data;
  },

  async getRepoPRs(owner: string, repo: string, params?: { status?: string; q?: string; sort?: string; order?: string; }): Promise<PRDetail[]> {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.q) query.set('q', params.q);
    if (params?.sort) query.set('sort', params.sort);
    if (params?.order) query.set('order', params.order);
    const url = `/api/repos/${owner}/${repo}/prs${query.toString() ? `?${query.toString()}` : ''}`;
    const response = await axiosInstance.get<PRDetail[]>(url);
    return response.data;
  },

  async getIssue(owner: string, repo: string, issueNumber: number): Promise<Issue> {
    const response = await axiosInstance.get<Issue>(`/api/repos/${owner}/${repo}/issues/${issueNumber}`);
    return response.data;
  },

  async updateChecklistItem(
    owner: string,
    repo: string,
    issueNumber: number,
    itemId: string,
    status: 'pending' | 'passed' | 'failed' | 'skipped'
  ): Promise<void> {
    await axiosInstance.patch(
      `/api/repos/${owner}/${repo}/issues/${issueNumber}/checklist/${itemId}`,
      { status }
    );
  },

  async regenerateChecklist(owner: string, repo: string, issueNumber: number): Promise<{ status: string; job_id?: string }> {
    const response = await axiosInstance.post<{ status: string; job_id?: string }>(
      `/api/repos/${owner}/${repo}/issues/${issueNumber}/regenerate`
    );
    return response.data;
  },

  async getPR(owner: string, repo: string, prNumber: number): Promise<PRDetail> {
    const response = await axiosInstance.get<PRDetail>(`/api/repos/${owner}/${repo}/prs/${prNumber}`);
    return response.data;
  },

  async revalidatePR(owner: string, repo: string, prNumber: number): Promise<void> {
    await axiosInstance.post(`/api/repos/${owner}/${repo}/prs/${prNumber}/revalidate`);
  },

  async flagForMerge(owner: string, repo: string, prNumber: number): Promise<void> {
    await axiosInstance.post(`/api/repos/${owner}/${repo}/prs/${prNumber}/flag_for_merge`);
  },

  async getNotifications(): Promise<Notification[]> {
    const response = await axiosInstance.get<Notification[]>('/api/notifications');
    return response.data;
  },

  async markNotificationRead(notificationId: string): Promise<void> {
    await axiosInstance.post(`/api/notifications/${notificationId}/read`);
  },

  async getGitHubInstallations(): Promise<GitHubInstallation[]> {
    const response = await axiosInstance.get<{ installations: GitHubInstallation[] }>(
      '/api/github/installations'
    );
    return response.data.installations;
  },

  async getInstallationRepos(installationId: number): Promise<GitHubInstallationReposResponse> {
    const response = await axiosInstance.get<GitHubInstallationReposResponse>(
      `/api/github/installations/${installationId}/repos`
    );
    return response.data;
  },
};

// Export for use in other files
export default api;

