import { useEffect, useState } from 'react';
import { Header } from '@/components/Header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp, GitPullRequest, FileText, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '@/lib/api';
import type { User, RepoSummary } from '@/types/api';
import { PRCard } from '@/components/PRCard';
import { IssueCard } from '@/components/IssueCard';

const Dashboard = () => {
  const [user, setUser] = useState<User | null>(null);
  const [repos, setRepos] = useState<RepoSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [userData, reposData] = await Promise.all([
          api.getMe(),
          api.getRepos(),
        ]);
        setUser(userData);
        setRepos(reposData);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

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
          
          {repos.length === 0 ? (
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
                        {/* Health Score */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-primary" />
                            <span className="text-sm text-muted-foreground">Health Score</span>
                          </div>
                          <span className="text-2xl font-bold text-primary">{repo.health_score}</span>
                        </div>

                        {/* Stats */}
                        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border/50">
                          <div>
                            <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                              <GitPullRequest className="h-4 w-4" />
                              <span className="text-xs">Pull Requests</span>
                            </div>
                            <p className="text-2xl font-bold">{repo.pr_count}</p>
                          </div>
                          
                          <div>
                            <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                              <FileText className="h-4 w-4" />
                              <span className="text-xs">Issues</span>
                            </div>
                            <p className="text-2xl font-bold">{repo.issue_count}</p>
                          </div>
                        </div>

                        {repo.last_activity && (
                          <p className="text-xs text-muted-foreground">
                            Last activity: {repo.last_activity}
                          </p>
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
                <PRCard
                  prNumber={42}
                  title="Implement user authentication"
                  author="quantum-dev"
                  healthScore={92}
                  repoOwner={repos[0].owner}
                  repoName={repos[0].name}
                  validationStatus="validated"
                />
                <PRCard
                  prNumber={38}
                  title="Add database migration system"
                  author="quantum-dev"
                  healthScore={85}
                  repoOwner={repos[0].owner}
                  repoName={repos[0].name}
                  validationStatus="pending"
                />
              </div>
            </div>

            {/* Pending Issues */}
            <div>
              <h2 className="text-2xl font-bold mb-6">Pending Issues</h2>
              <div className="space-y-4">
                <IssueCard
                  issue={{
                    issue_number: 42,
                    title: 'Add authentication middleware',
                    status: 'completed',
                    created_at: '2024-01-15T10:00:00Z',
                    updated_at: '2024-01-15T14:30:00Z',
                    checklist_summary: { total: 5, passed: 4, failed: 0, pending: 1 },
                    github_url: `https://github.com/${repos[0].owner}/${repos[0].name}/issues/42`,
                  }}
                  repoOwner={repos[0].owner}
                  repoName={repos[0].name}
                />
                <IssueCard
                  issue={{
                    issue_number: 38,
                    title: 'Optimize database queries',
                    status: 'processing',
                    created_at: '2024-01-14T09:00:00Z',
                    updated_at: '2024-01-15T11:00:00Z',
                    checklist_summary: { total: 6, passed: 2, failed: 1, pending: 3 },
                    github_url: `https://github.com/${repos[0].owner}/${repos[0].name}/issues/38`,
                  }}
                  repoOwner={repos[0].owner}
                  repoName={repos[0].name}
                />
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
