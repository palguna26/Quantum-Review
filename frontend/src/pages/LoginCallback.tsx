import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { api, auth } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

const LoginCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  useEffect(() => {
    const handleAuth = async () => {
      try {
        // Check if token is in URL (from backend redirect)
        const token = searchParams.get('token');
        console.log('[LoginCallback] Token from URL:', token ? token.substring(0, 20) + '...' : 'NOT FOUND');
        
        if (token) {
          auth.setToken(token);
          console.log('[LoginCallback] Token stored in localStorage');
        } else {
          console.warn('[LoginCallback] No token in URL');
        }
        
        // DEBUG: Check backend connectivity
        const backendUrl = import.meta.env.VITE_API_BASE || 'https://quantum-review.onrender.com';
        console.log('[LoginCallback] Backend URL:', backendUrl);
        console.log('[LoginCallback] Will call:', `${backendUrl}/api/me`);
        
        // Fetch user profile to verify authentication
        console.log('[LoginCallback] Calling api.getMe()...');
        const user = await api.getMe();
        console.log('[LoginCallback] User fetched:', user);
        
        toast({
          title: 'Success!',
          description: 'Successfully signed in with GitHub.',
        });

        navigate('/dashboard');
      } catch (error) {
        console.error('[LoginCallback] Auth error:', error);
        toast({
          title: 'Authentication Failed',
          description: 'Unable to sign in. Please try again.',
          variant: 'destructive',
        });
        
        navigate('/');
      }
    };

    handleAuth();
  }, [navigate, toast, searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center">
        <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
        <h2 className="text-xl font-semibold mb-2">Authenticating...</h2>
        <p className="text-muted-foreground">Please wait while we sign you in.</p>
      </div>
    </div>
  );
};

export default LoginCallback;
