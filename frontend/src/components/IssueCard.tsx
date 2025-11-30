import { Link } from 'react-router-dom';
import { CheckCircle2, Clock, XCircle, Circle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Issue } from '@/types/api';

interface IssueCardProps {
  issue: Issue;
  repoOwner: string;
  repoName: string;
}

const statusConfig = {
  open: { icon: Circle, color: 'text-muted-foreground', label: 'Open' },
  processing: { icon: Clock, color: 'text-warning', label: 'Processing' },
  completed: { icon: CheckCircle2, color: 'text-success', label: 'Completed' },
};

export const IssueCard = ({ issue, repoOwner, repoName }: IssueCardProps) => {
  const status = statusConfig[issue.status];
  const StatusIcon = status.icon;
  const { passed, failed, pending, total } = issue.checklist_summary;

  return (
    <Link to={`/repo/${repoOwner}/${repoName}/issues/${issue.issue_number}`}>
      <Card className="glass-card transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 cursor-pointer">
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <StatusIcon className={`h-4 w-4 ${status.color}`} />
                <span className="text-xs font-medium text-muted-foreground">#{issue.issue_number}</span>
                <Badge variant="outline" className="text-xs">
                  {status.label}
                </Badge>
              </div>
              
              <h3 className="font-semibold text-foreground mb-3 truncate">
                {issue.title}
              </h3>

              <div className="flex items-center gap-4 text-sm">
                {passed > 0 && (
                  <div className="flex items-center gap-1 text-success">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>{passed}</span>
                  </div>
                )}
                {failed > 0 && (
                  <div className="flex items-center gap-1 text-destructive">
                    <XCircle className="h-4 w-4" />
                    <span>{failed}</span>
                  </div>
                )}
                {pending > 0 && (
                  <div className="flex items-center gap-1 text-warning">
                    <Clock className="h-4 w-4" />
                    <span>{pending}</span>
                  </div>
                )}
                <span className="text-muted-foreground">of {total}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
};
