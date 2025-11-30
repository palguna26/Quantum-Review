import { Link } from 'react-router-dom';
import { Github, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { RepoSwitcher } from './RepoSwitcher';

interface HeaderProps {
  user?: { login: string; avatar_url: string };
  repos?: Array<{ repo_full_name: string; owner: string; name: string }>;
}

export const Header = ({ user, repos }: HeaderProps) => {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-lg">
      <div className="container flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2 transition-transform hover:scale-105">
            <Sparkles className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold gradient-text">QuantumReview</span>
          </Link>
          
          {user && repos && repos.length > 0 && (
            <RepoSwitcher repos={repos} />
          )}
        </div>

        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-3">
              <img 
                src={user.avatar_url} 
                alt={user.login}
                className="h-8 w-8 rounded-full border-2 border-primary/50"
              />
              <span className="text-sm font-medium hidden sm:inline">{user.login}</span>
            </div>
          ) : (
            <Button asChild variant="default" className="btn-hero">
              <a href="/auth/github">
                <Github className="mr-2 h-4 w-4" />
                Sign in with GitHub
              </a>
            </Button>
          )}
        </div>
      </div>
    </header>
  );
};
