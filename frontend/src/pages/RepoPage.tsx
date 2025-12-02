import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Header } from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ExternalLink, TrendingUp, Settings as SettingsIcon } from 'lucide-react';
import { api } from '@/lib/api';
import { IssueCard } from '@/components/IssueCard';
import { PRCard } from '@/components/PRCard';
import type { User, RepoSummary, Issue, PRDetail } from '@/types/api';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const RepoPage = () => {
  const { owner, repo } = useParams<{ owner: string; repo: string }>();
  const [user, setUser] = useState<User | null>(null);
  const [repoData, setRepoData] = useState<RepoSummary | null>(null);
  const [repos, setRepos] = useState<RepoSummary[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [prs, setPrs] = useState<PRDetail[]>([]);
  const [prStatus, setPrStatus] = useState<string>('');
  const [prSort, setPrSort] = useState<string>('updated');
  const [prOrder, setPrOrder] = useState<string>('desc');
  const [prQuery, setPrQuery] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      if (!owner || !repo) return;

      try {
        const [userData, repoDetails, reposData, issuesData, prsData] = await Promise.all([
          api.getMe(),
          api.getRepo(owner, repo),
          api.getRepos(),
          api.getRepoIssues(owner, repo),
          api.getRepoPRs(owner, repo, { sort: 'updated', order: 'desc' }),
        ]);
        
        setUser(userData);
        setRepoData(repoDetails);
        setRepos(reposData);
        setIssues(issuesData);
        setPrs(prsData);
      } catch (error) {
        console.error('Failed to load repo data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [owner, repo]);

  useEffect(() => {
    const fetchPrs = async () => {
      if (!owner || !repo) return;
      const params: any = {};
      if (prStatus) params.status = prStatus;
      if (prQuery) params.q = prQuery;
      params.sort = prSort;
      params.order = prOrder;
      try {
        const data = await api.getRepoPRs(owner, repo, params);
        setPrs(data);
      } catch (e) {
        // noop
      }
    };
    fetchPrs();
  }, [owner, repo, prStatus, prSort, prOrder, prQuery]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container px-4 py-8">
          <Skeleton className="h-32 rounded-lg mb-8" />
          <Skeleton className="h-96 rounded-lg" />
        </main>
      </div>
    );
  }

  if (!repoData || !owner || !repo) {
    return (
      <div className="min-h-screen bg-background">
        <Header user={user || undefined} repos={repos} />
        <main className="container px-4 py-8">
          <Card className="p-12 text-center">
            <p className="text-muted-foreground">Repository not found</p>
          </Card>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header user={user || undefined} repos={repos} />
      
      <main className="container px-4 py-8">
        {/* Repo Header */}
        <div className="mb-8">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div>
              <h1 className="text-3xl font-bold font-mono mb-2">{repoData.repo_full_name}</h1>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-primary" />
                  <span className="text-2xl font-bold text-primary">{repoData.health_score}</span>
                  <span className="text-sm text-muted-foreground">Health Score</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button asChild variant="outline">
                <a 
                  href={`https://github.com/${owner}/${repo}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  View on GitHub
                </a>
              </Button>

              {!repoData.is_installed && (
                <Button
                  onClick={async () => {
                    try {
                      const resp = await fetch(`/api/repos/${owner}/${repo}/install`, { credentials: 'include' });
                      const data = await resp.json();
                      const url = data.install_url || `https://github.com/apps/${'quantumreview'}/installations/new`;
                      window.open(url, '_blank');
                    } catch (e) {
                      window.open(`https://github.com/apps/${'quantumreview'}/installations/new`, '_blank');
                    }
                  }}
                >
                  Install QuantumReview
                </Button>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>{repoData.pr_count} Pull Requests</span>
            <span>•</span>
            <span>{repoData.issue_count} Issues</span>
            {repoData.last_activity && (
              <>
                <span>•</span>
                <span>Last activity: {repoData.last_activity}</span>
              </>
            )}
          </div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="issues" className="space-y-6">
          <TabsList>
            <TabsTrigger value="issues">Issues</TabsTrigger>
            <TabsTrigger value="prs">Pull Requests</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="issues" className="space-y-4">
            {issues.length === 0 ? (
              <Card className="glass-card p-12 text-center">
                <p className="text-muted-foreground">No issues found</p>
              </Card>
            ) : (
              issues.map((issue) => (
                <IssueCard
                  key={issue.issue_number}
                  issue={issue}
                  repoOwner={owner}
                  repoName={repo}
                />
              ))
            )}
          </TabsContent>

          <TabsContent value="prs" className="space-y-4">
            <div className="flex items-center gap-3">
              <Input
                placeholder="Search PR titles"
                value={prQuery}
                onChange={(e) => setPrQuery(e.target.value)}
                className="w-64"
              />
              <Select value={prStatus} onValueChange={(val) => setPrStatus(val)}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="validated">Validated</SelectItem>
                  <SelectItem value="needs_work">Needs Work</SelectItem>
                </SelectContent>
              </Select>
              <Select value={prSort} onValueChange={(val) => setPrSort(val)}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Sort" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="updated">Updated</SelectItem>
                  <SelectItem value="created">Created</SelectItem>
                  <SelectItem value="health">Health</SelectItem>
                </SelectContent>
              </Select>
              <Select value={prOrder} onValueChange={(val) => setPrOrder(val)}>
                <SelectTrigger className="w-36">
                  <SelectValue placeholder="Order" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="desc">Desc</SelectItem>
                  <SelectItem value="asc">Asc</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {prs.length === 0 ? (
              <Card className="glass-card p-12 text-center">
                <p className="text-muted-foreground">No pull requests found</p>
              </Card>
            ) : (
              prs.map((pr) => (
                <PRCard
                  key={pr.pr_number}
                  prNumber={pr.pr_number}
                  title={pr.title}
                  author={pr.author}
                  healthScore={pr.health_score}
                  repoOwner={owner}
                  repoName={repo}
                  validationStatus={pr.validation_status}
                />
              ))
            )}
          </TabsContent>

          <TabsContent value="settings">
            <Card className="glass-card p-8">
              <div className="flex items-start gap-4 mb-6">
                <SettingsIcon className="h-6 w-6 text-primary mt-1" />
                <div>
                  <h3 className="text-xl font-semibold mb-2">Repository Settings</h3>
                  <p className="text-muted-foreground mb-4">
                    Configure QuantumReview settings for this repository.
                  </p>
                </div>
              </div>
              
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Settings panel coming soon. Configure webhook preferences, checklist templates, 
                  and validation rules.
                </p>
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default RepoPage;
