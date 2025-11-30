import { Copy, Code2, Check } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useState } from 'react';
import type { SuggestedTest } from '@/types/api';

interface SuggestedTestCardProps {
  test: SuggestedTest;
}

export const SuggestedTestCard = ({ test }: SuggestedTestCardProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(test.snippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="glass-card">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base font-semibold mb-2">{test.name}</CardTitle>
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="outline" className="text-xs">
                {test.framework}
              </Badge>
              <span className="text-xs text-muted-foreground">{test.target}</span>
            </div>
          </div>
          
          <Button
            size="sm"
            variant="outline"
            onClick={handleCopy}
            className="flex-shrink-0"
          >
            {copied ? (
              <>
                <Check className="h-3 w-3 mr-1" />
                Copied
              </>
            ) : (
              <>
                <Copy className="h-3 w-3 mr-1" />
                Copy
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      
      <CardContent>
        {test.reasoning && (
          <p className="text-sm text-muted-foreground mb-3">{test.reasoning}</p>
        )}
        
        <div className="relative">
          <div className="absolute top-2 right-2">
            <Code2 className="h-4 w-4 text-muted-foreground" />
          </div>
          <pre className="bg-muted/50 rounded-md p-3 overflow-x-auto text-xs font-mono border border-border/50">
            <code>{test.snippet}</code>
          </pre>
        </div>

        {test.checklist_ids.length > 0 && (
          <div className="mt-3 text-xs text-muted-foreground">
            Covers {test.checklist_ids.length} checklist item{test.checklist_ids.length !== 1 ? 's' : ''}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
