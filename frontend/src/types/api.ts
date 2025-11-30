export interface User {
  id: string;
  login: string;
  avatar_url: string;
  name?: string;
  email?: string;
  managed_repos: string[];
}

export interface RepoSummary {
  repo_full_name: string;
  owner: string;
  name: string;
  health_score: number;
  is_installed: boolean;
  pr_count: number;
  issue_count: number;
  last_activity?: string;
}

export interface ChecklistItem {
  id: string;
  text: string;
  required: boolean;
  status: 'pending' | 'passed' | 'failed' | 'skipped';
  linked_tests: string[];
}

export interface Issue {
  issue_number: number;
  title: string;
  status: 'open' | 'processing' | 'completed';
  created_at: string;
  updated_at: string;
  checklist_summary: {
    total: number;
    passed: number;
    failed: number;
    pending: number;
  };
  checklist?: ChecklistItem[];
  github_url: string;
}

export interface TestResult {
  test_id: string;
  name: string;
  status: 'passed' | 'failed' | 'skipped';
  duration_ms?: number;
  error_message?: string;
  checklist_ids: string[];
}

export interface CodeHealthIssue {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  message: string;
  file_path: string;
  line_number?: number;
  suggestion?: string;
}

export interface SuggestedTest {
  test_id: string;
  name: string;
  framework: string;
  target: string;
  checklist_ids: string[];
  snippet: string;
  reasoning?: string;
}

export interface CoverageAdvice {
  file_path: string;
  lines: number[];
  suggestion: string;
}

export interface PRDetail {
  pr_number: number;
  title: string;
  author: string;
  created_at: string;
  health_score: number;
  validation_status: 'pending' | 'validated' | 'needs_work';
  manifest?: {
    checklist_items: ChecklistItem[];
  };
  test_results: TestResult[];
  code_health: CodeHealthIssue[];
  coverage_advice: CoverageAdvice[];
  suggested_tests: SuggestedTest[];
  github_url: string;
}

export interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  repo_full_name?: string;
  created_at: string;
  read: boolean;
}
