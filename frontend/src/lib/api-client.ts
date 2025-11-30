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
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
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
    const response = await axiosInstance.get<User>('/me');
    return response.data;
  },

  async getRepos(): Promise<RepoSummary[]> {
    const response = await axiosInstance.get<RepoSummary[]>('/repos');
    return response.data;
  },

  async getRepo(owner: string, repo: string): Promise<RepoSummary> {
    const response = await axiosInstance.get<RepoSummary>(`/repos/${owner}/${repo}`);
    return response.data;
  },

  async getIssues(owner: string, repo: string): Promise<Issue[]> {
    const response = await axiosInstance.get<Issue[]>(`/repos/${owner}/${repo}/issues`);
    return response.data;
  },

  async getIssue(owner: string, repo: string, issueNumber: number): Promise<Issue> {
    const response = await axiosInstance.get<Issue>(`/repos/${owner}/${repo}/issues/${issueNumber}`);
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
      `/repos/${owner}/${repo}/issues/${issueNumber}/checklist/${itemId}`,
      { status }
    );
  },

  async regenerateChecklist(owner: string, repo: string, issueNumber: number): Promise<{ status: string; job_id?: string }> {
    const response = await axiosInstance.post<{ status: string; job_id?: string }>(
      `/repos/${owner}/${repo}/issues/${issueNumber}/regenerate`
    );
    return response.data;
  },

  async getPR(owner: string, repo: string, prNumber: number): Promise<PRDetail> {
    const response = await axiosInstance.get<PRDetail>(`/repos/${owner}/${repo}/prs/${prNumber}`);
    return response.data;
  },

  async revalidatePR(owner: string, repo: string, prNumber: number): Promise<void> {
    await axiosInstance.post(`/repos/${owner}/${repo}/prs/${prNumber}/revalidate`);
  },

  async getNotifications(): Promise<Notification[]> {
    const response = await axiosInstance.get<Notification[]>('/notifications');
    return response.data;
  },

  async markNotificationRead(notificationId: string): Promise<void> {
    await axiosInstance.post(`/notifications/${notificationId}/read`);
  },

  async getGitHubInstallations(): Promise<GitHubInstallation[]> {
    const response = await axiosInstance.get<{ installations: GitHubInstallation[] }>(
      '/github/installations'
    );
    return response.data.installations;
  },

  async getInstallationRepos(installationId: number): Promise<GitHubInstallationReposResponse> {
    const response = await axiosInstance.get<GitHubInstallationReposResponse>(
      `/github/installations/${installationId}/repos`
    );
    return response.data;
  },
};

// Export for use in other files
export default api;

