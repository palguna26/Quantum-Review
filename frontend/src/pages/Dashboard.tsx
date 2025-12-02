import { useEffect, useState } from 'react';
import { Header } from '@/components/Header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp, GitPullRequest, FileText, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '@/lib/api';
import type { User, RepoSummary, GitHubInstallation, GitHubInstallationRepo, PRDetail, Issue } from '@/types/api';
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from '@/components/ui/select';
import { PRCard } from '@/components/PRCard';
import { IssueCard } from '@/components/IssueCard';

const Dashboard = () => {
  const [user, setUser] = useState<User | null>(null);
  const [repos, setRepos] = useState<RepoSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");
  const [installations, setInstallations] = useState<GitHubInstallation[]>([]);
  const [selectedInstallation, setSelectedInstallation] = useState<string>("");
  const [installationRepos, setInstallationRepos] = useState<GitHubInstallationRepo[]>([]);
  const [recentPRs, setRecentPRs] = useState<PRDetail[]>([]);
  const [pendingIssues, setPendingIssues] = useState<Issue[]>([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [userData, reposData] = await Promise.all([
          api.getMe(),
          api.getRepos(filter === 'all' ? undefined : filter),
        ]);
        setUser(userData);
        setRepos(reposData);
        if (reposData.length === 0) {
          try {
            const installs = await api.getGitHubInstallations();
            setInstallations(installs);
          } catch (err) {
            console.error(err);
          }
        }
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [filter]);

  useEffect(() => {
    const loadRecent = async () => {
      if (repos.length === 0) {
        setRecentPRs([]);
        setPendingIssues([]);
        return;
      }
      const { owner, name } = repos[0];
      try {
        const [prs, issues] = await Promise.all([
          api.getRepoPRs(owner, name, { status: 'open', sort: 'created', order: 'desc' }),
          api.getRepoIssues(owner, name),
        ]);
        setRecentPRs(prs.slice(0, 2));
        setPendingIssues(issues.slice(0, 2));
      } catch (err) {
        console.error('Failed to load recent activity:', err);
      }
    };

    loadRecent();
  }, [repos]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container px-4 py-8">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-8">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-48 rounded-lg" />
            ))}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header user={user || undefined} repos={repos} />
      
      <main className="container px-4 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Welcome back, {user?.name || user?.login}!</h1>
          <p className="text-muted-foreground">
            Manage your repositories and track code quality across your projects.
          </p>
        </div>

        {/* Repository Grid */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold mb-6">Your Repositories</h2>
          <div className="mb-4 flex items-center gap-3">
            <Select value={filter} onValueChange={(val) => setFilter(val)}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Filter repositories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="critical">Critical Risk</SelectItem>
                <SelectItem value="needs_review">Needs Review</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          {repos.length === 0 ? (
            <div className="space-y-6">
              {installations.length === 0 ? (
                <Card className="glass-card p-12 text-center">
                  <p className="text-muted-foreground mb-4">No repositories found.</p>
                  <Button asChild>
                    <a href="https://github.com/apps/quantum-review/installations/new" target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="mr-2 h-4 w-4" />
                      Install QuantumReview
                    </a>
                  </Button>
                </Card>
              ) : (
                <Card className="glass-card p-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold">Select Installation</h3>
                      <span className="text-sm text-muted-foreground">{installations.length} available</span>
                    </div>
                    <Select value={selectedInstallation} onValueChange={async (val) => {
                      setSelectedInstallation(val);
                      const id = parseInt(val, 10);
                      const data = await api.getInstallationRepos(id);
                      setInstallationRepos(data.repos);
                    }}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Choose an installation" />
                      </SelectTrigger>
                      <SelectContent>
                        {installations.map((inst) => (
                          <SelectItem key={inst.installation_id} value={String(inst.installation_id)}>
                            Installation #{inst.installation_id} ({inst.repo_count} repos)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {installationRepos.length > 0 && (
                      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 pt-2">
                        {installationRepos.map((r) => (
                          <a key={r.repo_full_name} href={r.html_url} target="_blank" rel="noopener noreferrer">
                            <Card className="glass-card transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 cursor-pointer">
                              <CardHeader>
                                <CardTitle className="flex items-start justify-between gap-4">
                                  <span className="font-mono text-sm truncate">{r.repo_full_name}</span>
                                  <Badge variant="outline" className="text-xs flex-shrink-0">
                                    {r.private ? "Private" : "Public"}
                                  </Badge>
                                </CardTitle>
                              </CardHeader>
                            </Card>
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                </Card>
              )}
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {repos.map((repo) => (
                <Link key={repo.repo_full_name} to={`/repo/${repo.owner}/${repo.name}`}>
                  <Card className="glass-card h-full transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 cursor-pointer">
                    <CardHeader>
                      <CardTitle className="flex items-start justify-between gap-4">
                        <span className="font-mono text-base truncate">{repo.repo_full_name}</span>
                        {!repo.is_installed && (
                          <Badge variant="outline" className="text-xs flex-shrink-0">
                            Not Installed
                          </Badge>
                        )}
                      </CardTitle>
                    </CardHeader>
                    
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5 text-muted-foreground">
                            <TrendingUp className="h-4 w-4 text-primary" />
                            <span className="text-xs">Health Score</span>
                          </div>
                          <span className="text-2xl font-bold text-primary">{repo.health_score}</span>
                        </div>
                        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border/50">
                          <div>
                            <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                              <GitPullRequest className="h-4 w-4" />
                              <span className="text-xs">Pull Requests</span>
                            </div>
                            <p className="text-2xl font-bold">{repo.pr_count}</p>
                            {repo.recent_pr_numbers && repo.recent_pr_numbers.length > 0 && (
                              <p className="text-xs text-muted-foreground font-mono mt-1">
                                #{repo.recent_pr_numbers.slice(0, 5).join(', #')}
                              </p>
                            )}
                          </div>
                          
                          <div>
                            <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                              <FileText className="h-4 w-4" />
                              <span className="text-xs">Issues</span>
                            </div>
                            <p className="text-2xl font-bold">{repo.issue_count}</p>
                            {repo.recent_issue_numbers && repo.recent_issue_numbers.length > 0 && (
                              <p className="text-xs text-muted-foreground font-mono mt-1">
                                #{repo.recent_issue_numbers.slice(0, 5).join(', #')}
                              </p>
                            )}
                          </div>
                        </div>
                        {repo.last_activity && (
                          <p className="text-xs text-muted-foreground">Last activity: {formatRelativeTime(repo.last_activity)}</p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </section>

        {/* Recent Activity */}
        {repos.length > 0 && (
          <section className="grid lg:grid-cols-2 gap-8">
            {/* Open PRs */}
            <div>
              <h2 className="text-2xl font-bold mb-6">Recent Pull Requests</h2>
              <div className="space-y-4">
                {recentPRs.map((pr) => (
                  <PRCard
                    key={pr.pr_number}
                    prNumber={pr.pr_number}
                    title={pr.title}
                    author={pr.author}
                    healthScore={pr.health_score}
                    repoOwner={repos[0].owner}
                    repoName={repos[0].name}
                    validationStatus={pr.validation_status}
                  />
                ))}
              </div>
            </div>

            {/* Pending Issues */}
            <div>
              <h2 className="text-2xl font-bold mb-6">Pending Issues</h2>
              <div className="space-y-4">
                {pendingIssues.map((issue) => (
                  <IssueCard
                    key={issue.issue_number}
                    issue={issue}
                    repoOwner={repos[0].owner}
                    repoName={repos[0].name}
                  />
                ))}
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
};

export default Dashboard;

function formatRelativeTime(dateStr: string) {
  const date = new Date(dateStr);
  const diff = Math.max(0, Date.now() - date.getTime());
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) return `${minutes} minutes ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hours ago`;
  const days = Math.floor(hours / 24);
  return `${days} days ago`;
}
