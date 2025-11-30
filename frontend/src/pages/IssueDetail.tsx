import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Header } from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, RefreshCw, MessageSquare, ArrowLeft } from 'lucide-react';
import { api } from '@/lib/api';
import { ChecklistItem } from '@/components/ChecklistItem';
import { useToast } from '@/hooks/use-toast';
import type { User, RepoSummary, Issue } from '@/types/api';

const IssueDetail = () => {
  const { owner, repo, issueNumber } = useParams<{ owner: string; repo: string; issueNumber: string }>();
  const [user, setUser] = useState<User | null>(null);
  const [repos, setRepos] = useState<RepoSummary[]>([]);
  const [issue, setIssue] = useState<Issue | null>(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    const loadData = async () => {
      if (!owner || !repo || !issueNumber) return;

      try {
        const [userData, reposData, issueData] = await Promise.all([
          api.getMe(),
          api.getRepos(),
          api.getIssue(owner, repo, parseInt(issueNumber)),
        ]);
        
        setUser(userData);
        setRepos(reposData);
        setIssue(issueData);
      } catch (error) {
        console.error('Failed to load issue data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [owner, repo, issueNumber]);

  const handleRegenerate = async () => {
    if (!owner || !repo || !issueNumber) return;

    setRegenerating(true);
    try {
      await api.regenerateChecklist(owner, repo, parseInt(issueNumber));
      
      toast({
        title: 'Checklist Regeneration Started',
        description: 'The checklist is being regenerated. This may take a few moments.',
      });

      // Reload issue data after a delay
      setTimeout(async () => {
        const updatedIssue = await api.getIssue(owner, repo, parseInt(issueNumber));
        setIssue(updatedIssue);
      }, 2000);
    } catch (error) {
      toast({
        title: 'Regeneration Failed',
        description: 'Unable to regenerate checklist. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setRegenerating(false);
    }
  };

  const handleChecklistStatusChange = async (
    itemId: string,
    newStatus: 'pending' | 'passed' | 'failed' | 'skipped'
  ) => {
    if (!owner || !repo || !issueNumber || !issue) return;

    try {
      // Optimistically update UI
      const updatedChecklist = issue.checklist?.map((item) =>
        item.id === itemId ? { ...item, status: newStatus } : item
      );
      if (updatedChecklist) {
        setIssue({ ...issue, checklist: updatedChecklist });
      }

      // Update on backend
      await api.updateChecklistItem(owner, repo, parseInt(issueNumber), itemId, newStatus);
      
      // Reload issue to get updated summary
      const updatedIssue = await api.getIssue(owner, repo, parseInt(issueNumber));
      setIssue(updatedIssue);
      
      toast({
        title: 'Status Updated',
        description: 'Checklist item status has been updated.',
      });
    } catch (error) {
      console.error('Failed to update checklist item:', error);
      // Revert optimistic update
      const updatedIssue = await api.getIssue(owner, repo, parseInt(issueNumber));
      setIssue(updatedIssue);
      
      toast({
        title: 'Update Failed',
        description: 'Unable to update checklist item status. Please try again.',
        variant: 'destructive',
      });
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

  if (!issue || !owner || !repo) {
    return (
      <div className="min-h-screen bg-background">
        <Header user={user || undefined} repos={repos} />
        <main className="container px-4 py-8">
          <Card className="p-12 text-center">
            <p className="text-muted-foreground">Issue not found</p>
          </Card>
        </main>
      </div>
    );
  }

  const { passed, failed, pending, total } = issue.checklist_summary;
  const completionPercentage = total > 0 ? Math.round((passed / total) * 100) : 0;

  return (
    <div className="min-h-screen bg-background">
      <Header user={user || undefined} repos={repos} />
      
      <main className="container px-4 py-8 max-w-5xl">
        {/* Breadcrumb */}
        <div className="mb-6">
          <Link 
            to={`/repo/${owner}/${repo}`}
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to {owner}/{repo}
          </Link>
        </div>

        {/* Issue Header */}
        <div className="mb-8">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant={issue.status === 'completed' ? 'default' : 'outline'}>
                  {issue.status}
                </Badge>
                <span className="text-sm text-muted-foreground">#{issue.issue_number}</span>
              </div>
              <h1 className="text-3xl font-bold mb-2">{issue.title}</h1>
            </div>

            <Button asChild variant="outline">
              <a 
                href={issue.github_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink className="mr-2 h-4 w-4" />
                GitHub
              </a>
            </Button>
          </div>

          {/* Progress Summary */}
          <Card className="glass-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium">Checklist Progress</span>
                <span className="text-2xl font-bold text-primary">{completionPercentage}%</span>
              </div>
              
              <div className="w-full bg-muted rounded-full h-2 mb-4">
                <div 
                  className="bg-primary h-2 rounded-full transition-all"
                  style={{ width: `${completionPercentage}%` }}
                />
              </div>

              <div className="flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-success" />
                  <span>{passed} Passed</span>
                </div>
                {failed > 0 && (
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-destructive" />
                    <span>{failed} Failed</span>
                  </div>
                )}
                {pending > 0 && (
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-warning" />
                    <span>{pending} Pending</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Checklist */}
        <Card className="glass-card mb-8">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Quality Checklist</CardTitle>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRegenerate}
                  disabled={regenerating}
                >
                  <RefreshCw className={`mr-2 h-4 w-4 ${regenerating ? 'animate-spin' : ''}`} />
                  Regenerate
                </Button>
                <Button variant="outline" size="sm" asChild>
                  <a href={`${issue.github_url}#issuecomment-new`} target="_blank" rel="noopener noreferrer">
                    <MessageSquare className="mr-2 h-4 w-4" />
                    Comment
                  </a>
                </Button>
              </div>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-3">
            {issue.checklist && issue.checklist.length > 0 ? (
              issue.checklist.map((item) => (
                <ChecklistItem 
                  key={item.id} 
                  item={item}
                  onStatusChange={handleChecklistStatusChange}
                />
              ))
            ) : (
              <p className="text-center text-muted-foreground py-8">
                No checklist items generated yet.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Metadata */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Issue Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Created</span>
              <span>{new Date(issue.created_at).toLocaleDateString()}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Last Updated</span>
              <span>{new Date(issue.updated_at).toLocaleDateString()}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Total Items</span>
              <span>{total}</span>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default IssueDetail;
