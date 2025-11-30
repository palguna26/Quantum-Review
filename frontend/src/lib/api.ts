// Re-export API client (switching from mocks to real implementation)
export { api, auth } from './api-client';
export type { User, RepoSummary, Issue, PRDetail, Notification } from '@/types/api';
