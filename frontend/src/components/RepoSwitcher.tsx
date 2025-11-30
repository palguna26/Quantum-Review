import { Link } from 'react-router-dom';
import { Check, ChevronDown, FolderGit2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useLocation } from 'react-router-dom';

interface Repo {
  repo_full_name: string;
  owner: string;
  name: string;
}

interface RepoSwitcherProps {
  repos: Repo[];
}

export const RepoSwitcher = ({ repos }: RepoSwitcherProps) => {
  const location = useLocation();
  const pathParts = location.pathname.split('/');
  const currentRepo = pathParts[2] && pathParts[3] ? `${pathParts[2]}/${pathParts[3]}` : null;

  const displayRepos = repos.slice(0, 8);
  const hasMore = repos.length > 8;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="gap-2">
          <FolderGit2 className="h-4 w-4" />
          <span className="hidden sm:inline">
            {currentRepo || 'Select Repository'}
          </span>
          <ChevronDown className="h-4 w-4 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
        {displayRepos.map((repo) => (
          <DropdownMenuItem key={repo.repo_full_name} asChild>
            <Link 
              to={`/repo/${repo.owner}/${repo.name}`}
              className="flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <FolderGit2 className="h-4 w-4" />
                <span className="font-mono text-sm">{repo.repo_full_name}</span>
              </div>
              {currentRepo === repo.repo_full_name && (
                <Check className="h-4 w-4 text-primary" />
              )}
            </Link>
          </DropdownMenuItem>
        ))}
        {hasMore && (
          <DropdownMenuItem asChild>
            <Link to="/dashboard" className="text-muted-foreground">
              View all repositories →
            </Link>
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
