import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Github, Sparkles, CheckCircle2, GitPullRequest, TrendingUp, Shield } from 'lucide-react';
import { Link } from 'react-router-dom';

// Backend URL (set at build time for production). Accept either
// `VITE_BACKEND_URL` or `VITE_API_BASE` (some deployments use the latter).
// For OAuth flows, we need an absolute URL. In production on Render,
// VITE_API_BASE must be set to the backend origin.
const VITE_BACKEND_URL = (import.meta.env.VITE_BACKEND_URL as string) || (import.meta.env.VITE_API_BASE as string) || '';
const backendOrigin = VITE_BACKEND_URL ? VITE_BACKEND_URL.replace(/\/+$/, '') : 'https://quantum-review.onrender.com';
console.log('[Landing] VITE_API_BASE from build:', import.meta.env.VITE_API_BASE);
console.log('[Landing] Computed backendOrigin:', backendOrigin);

const Landing = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-lg">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold gradient-text">QuantumReview</span>
          </div>
          
          <Button asChild variant="default" className="btn-hero">
            <a href={`${backendOrigin || ''}/auth/github`} target="_self">
              <Github className="mr-2 h-4 w-4" />
              Sign in with GitHub
            </a>
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container px-4 pt-20 pb-32">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mb-6 inline-block">
            <Badge className="bg-primary/10 text-primary border-primary/20">
              AI-Powered Code Review
            </Badge>
          </div>
          
          <h1 className="text-5xl sm:text-6xl font-bold mb-6 leading-tight">
            Elevate Your Code Quality with{' '}
            <span className="gradient-text">Quantum Intelligence</span>
          </h1>
          
          <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto">
            Automated quality assurance for GitHub repositories. Generate intelligent checklists, 
            validate PRs, and ensure every line of code meets your standards.
          </p>

          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Button asChild size="lg" className="btn-hero">
              <a href={`${backendOrigin || ''}/auth/github`}>
                <Github className="mr-2 h-5 w-5" />
                Get Started Free
              </a>
            </Button>
            
            <Button asChild size="lg" variant="outline">
              <Link to="/dashboard">
                View Demo
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="container px-4 pb-32">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-3xl font-bold text-center mb-12">Powerful Features</h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="glass-card">
              <CardContent className="pt-6">
                <div className="mb-4 inline-flex p-3 rounded-lg bg-primary/10">
                  <CheckCircle2 className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Smart Checklists</h3>
                <p className="text-muted-foreground">
                  AI-generated quality checklists for every issue, ensuring comprehensive coverage 
                  of testing and validation requirements.
                </p>
              </CardContent>
            </Card>

            <Card className="glass-card">
              <CardContent className="pt-6">
                <div className="mb-4 inline-flex p-3 rounded-lg bg-secondary/10">
                  <GitPullRequest className="h-6 w-6 text-secondary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">PR Validation</h3>
                <p className="text-muted-foreground">
                  Automated validation of pull requests against issue checklists with detailed 
                  test coverage analysis and suggestions.
                </p>
              </CardContent>
            </Card>

            <Card className="glass-card">
              <CardContent className="pt-6">
                <div className="mb-4 inline-flex p-3 rounded-lg bg-success/10">
                  <TrendingUp className="h-6 w-6 text-success" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Health Scores</h3>
                <p className="text-muted-foreground">
                  Real-time code health metrics for repositories and PRs, helping you maintain 
                  high standards across your codebase.
                </p>
              </CardContent>
            </Card>

            <Card className="glass-card">
              <CardContent className="pt-6">
                <div className="mb-4 inline-flex p-3 rounded-lg bg-warning/10">
                  <Shield className="h-6 w-6 text-warning" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Code Health Analysis</h3>
                <p className="text-muted-foreground">
                  Identify security issues, performance bottlenecks, and code smells with 
                  actionable recommendations for improvement.
                </p>
              </CardContent>
            </Card>

            <Card className="glass-card">
              <CardContent className="pt-6">
                <div className="mb-4 inline-flex p-3 rounded-lg bg-accent/10">
                  <Sparkles className="h-6 w-6 text-accent" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Test Suggestions</h3>
                <p className="text-muted-foreground">
                  AI-powered test generation with ready-to-use code snippets that match your 
                  testing framework and style.
                </p>
              </CardContent>
            </Card>

            <Card className="glass-card">
              <CardContent className="pt-6">
                <div className="mb-4 inline-flex p-3 rounded-lg bg-primary/10">
                  <Github className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">GitHub Integration</h3>
                <p className="text-muted-foreground">
                  Seamless integration with GitHub webhooks for automatic processing of issues 
                  and pull requests as they're created.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container px-4 pb-32">
        <Card className="glass-card mx-auto max-w-3xl text-center p-12">
          <h2 className="text-3xl font-bold mb-4">Ready to Transform Your Code Review Process?</h2>
          <p className="text-xl text-muted-foreground mb-8">
            Join teams using QuantumReview to ship higher quality code faster.
          </p>
          <Button asChild size="lg" className="btn-hero">
            <a href={`${backendOrigin || ''}/auth/github`}>
              <Github className="mr-2 h-5 w-5" />
              Sign in with GitHub
            </a>
          </Button>
        </Card>
      </section>
    </div>
  );
};

const Badge = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${className}`}>
    {children}
  </span>
);

export default Landing;
