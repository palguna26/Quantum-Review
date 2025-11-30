import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Header } from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, RefreshCw, TrendingUp, ArrowLeft, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { api } from '@/lib/api';
import { SuggestedTestCard } from '@/components/SuggestedTestCard';
import { useToast } from '@/hooks/use-toast';
import type { User, RepoSummary, PRDetail } from '@/types/api';

const PRDetailPage = () => {
  const { owner, repo, prNumber } = useParams<{ owner: string; repo: string; prNumber: string }>();
  const [user, setUser] = useState<User | null>(null);
  const [repos, setRepos] = useState<RepoSummary[]>([]);
  const [pr, setPr] = useState<PRDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [revalidating, setRevalidating] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    const loadData = async () => {
      if (!owner || !repo || !prNumber) return;

      try {
        const [userData, reposData, prData] = await Promise.all([
          api.getMe(),
          api.getRepos(),
          api.getPR(owner, repo, parseInt(prNumber)),
        ]);
        
        setUser(userData);
        setRepos(reposData);
        setPr(prData);
      } catch (error) {
        console.error('Failed to load PR data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [owner, repo, prNumber]);

  const handleRevalidate = async () => {
    if (!owner || !repo || !prNumber) return;

    setRevalidating(true);
    try {
      await api.revalidatePR(owner, repo, parseInt(prNumber));
      
      toast({
        title: 'PR Revalidation Started',
        description: 'The PR is being revalidated. This may take a few moments.',
      });

      setTimeout(async () => {
        const updatedPR = await api.getPR(owner, repo, parseInt(prNumber));
        setPr(updatedPR);
      }, 2000);
    } catch (error) {
      toast({
        title: 'Revalidation Failed',
        description: 'Unable to revalidate PR. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setRevalidating(false);
    }
  };

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

  if (!pr || !owner || !repo) {
    return (
      <div className="min-h-screen bg-background">
        <Header user={user || undefined} repos={repos} />
        <main className="container px-4 py-8">
          <Card className="p-12 text-center">
            <p className="text-muted-foreground">Pull request not found</p>
          </Card>
        </main>
      </div>
    );
  }

  const severityColors = {
    critical: 'text-destructive',
    high: 'text-destructive',
    medium: 'text-warning',
    low: 'text-muted-foreground',
  };

  return (
    <div className="min-h-screen bg-background">
      <Header user={user || undefined} repos={repos} />
      
      <main className="container px-4 py-8 max-w-6xl">
        <div className="mb-6">
          <Link 
            to={`/repo/${owner}/${repo}`}
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to {owner}/{repo}
          </Link>
        </div>

        {/* PR Header */}
        <div className="mb-8">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant={pr.validation_status === 'validated' ? 'default' : 'outline'}>
                  {pr.validation_status}
                </Badge>
                <span className="text-sm text-muted-foreground">#{pr.pr_number}</span>
              </div>
              <h1 className="text-3xl font-bold mb-2">{pr.title}</h1>
              <p className="text-muted-foreground">by {pr.author}</p>
            </div>

            <div className="flex flex-col items-end gap-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                <span className="text-3xl font-bold text-primary">{pr.health_score}</span>
              </div>
              <span className="text-xs text-muted-foreground">Quantum Health Score</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button asChild variant="outline">
              <a 
                href={pr.github_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink className="mr-2 h-4 w-4" />
                View on GitHub
              </a>
            </Button>
            
            <Button
              variant="outline"
              onClick={handleRevalidate}
              disabled={revalidating}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${revalidating ? 'animate-spin' : ''}`} />
              Revalidate
            </Button>

            {pr.validation_status === 'validated' && (
              <Button className="btn-hero">
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Recommend Merge
              </Button>
            )}
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column */}
          <div className="space-y-6">
            {/* Checklist Mapping */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>Checklist Coverage</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {pr.manifest?.checklist_items.map((item) => {
                  const linkedTests = pr.test_results.filter(t => 
                    t.checklist_ids.includes(item.id)
                  );
                  const allPassed = linkedTests.every(t => t.status === 'passed');
                  
                  return (
                    <div key={item.id} className="flex items-start gap-3 p-3 rounded-lg bg-muted/30 border border-border/50">
                      {allPassed ? (
                        <CheckCircle2 className="h-5 w-5 text-success mt-0.5 flex-shrink-0" />
                      ) : (
                        <AlertTriangle className="h-5 w-5 text-warning mt-0.5 flex-shrink-0" />
                      )}
                      
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm mb-1">{item.text}</p>
                        <div className="text-xs text-muted-foreground">
                          {linkedTests.length} test{linkedTests.length !== 1 ? 's' : ''} linked
                          {linkedTests.length > 0 && (
                            <span className="ml-2">
                              • {linkedTests.filter(t => t.status === 'passed').length} passed
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            {/* Code Health */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>Code Health Issues</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {pr.code_health.length === 0 ? (
                  <p className="text-center text-muted-foreground py-4">
                    No code health issues detected. Great work!
                  </p>
                ) : (
                  pr.code_health.slice(0, 5).map((issue) => (
                    <div key={issue.id} className="space-y-2 p-3 rounded-lg bg-muted/30 border border-border/50">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className={`h-4 w-4 mt-0.5 flex-shrink-0 ${severityColors[issue.severity]}`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="outline" className="text-xs">
                              {issue.severity}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {issue.category}
                            </Badge>
                          </div>
                          <p className="text-sm font-medium mb-1">{issue.message}</p>
                          <p className="text-xs text-muted-foreground font-mono">
                            {issue.file_path}
                            {issue.line_number && `:${issue.line_number}`}
                          </p>
                          {issue.suggestion && (
                            <p className="text-xs text-muted-foreground mt-2">
                              💡 {issue.suggestion}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {/* Suggested Tests */}
            <div>
              <h2 className="text-2xl font-bold mb-4">Suggested Tests</h2>
              <div className="space-y-4">
                {pr.suggested_tests.length === 0 ? (
                  <Card className="glass-card p-8 text-center">
                    <p className="text-muted-foreground">No test suggestions available</p>
                  </Card>
                ) : (
                  pr.suggested_tests.map((test) => (
                    <SuggestedTestCard key={test.test_id} test={test} />
                  ))
                )}
              </div>
            </div>

            {/* Coverage Advice */}
            {pr.coverage_advice.length > 0 && (
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle>Coverage Gaps</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {pr.coverage_advice.map((advice, idx) => (
                    <div key={idx} className="space-y-2 p-3 rounded-lg bg-muted/30 border border-border/50">
                      <p className="text-sm font-mono">{advice.file_path}</p>
                      <p className="text-xs text-muted-foreground">
                        Lines: {advice.lines.join(', ')}
                      </p>
                      <p className="text-sm">{advice.suggestion}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default PRDetailPage;
