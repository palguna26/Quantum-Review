import { CheckCircle2, Circle, XCircle, Clock, Tag, ChevronDown } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import type { ChecklistItem as ChecklistItemType } from '@/types/api';

interface ChecklistItemProps {
  item: ChecklistItemType;
  onStatusChange?: (itemId: string, newStatus: 'pending' | 'passed' | 'failed' | 'skipped') => void;
  disabled?: boolean;
}

const statusConfig = {
  passed: { icon: CheckCircle2, color: 'text-success', bgColor: 'bg-success/10', label: 'Passed' },
  failed: { icon: XCircle, color: 'text-destructive', bgColor: 'bg-destructive/10', label: 'Failed' },
  pending: { icon: Clock, color: 'text-warning', bgColor: 'bg-warning/10', label: 'Pending' },
  skipped: { icon: Circle, color: 'text-muted-foreground', bgColor: 'bg-muted/10', label: 'Skipped' },
};

export const ChecklistItem = ({ item, onStatusChange, disabled = false }: ChecklistItemProps) => {
  const status = statusConfig[item.status];
  const StatusIcon = status.icon;

  const handleStatusChange = (newStatus: 'pending' | 'passed' | 'failed' | 'skipped') => {
    if (onStatusChange && !disabled) {
      onStatusChange(item.id, newStatus);
    }
  };

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${status.bgColor} border-border/50 transition-colors ${!disabled && onStatusChange ? 'hover:border-border cursor-pointer' : ''}`}>
      <StatusIcon className={`h-5 w-5 ${status.color} mt-0.5 flex-shrink-0`} />
      
      <div className="flex-1 min-w-0">
        <p className="font-medium text-foreground mb-1">{item.text}</p>
        
        <div className="flex items-center gap-2 flex-wrap">
          {item.required && (
            <Badge variant="outline" className="text-xs">
              Required
            </Badge>
          )}
          
          {item.linked_tests.length > 0 && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Tag className="h-3 w-3" />
              <span>{item.linked_tests.length} test{item.linked_tests.length !== 1 ? 's' : ''}</span>
            </div>
          )}
        </div>
      </div>

      {onStatusChange && !disabled && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 px-2">
              <ChevronDown className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => handleStatusChange('pending')}>
              <Clock className="mr-2 h-4 w-4" />
              Mark as Pending
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleStatusChange('passed')}>
              <CheckCircle2 className="mr-2 h-4 w-4 text-success" />
              Mark as Passed
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleStatusChange('failed')}>
              <XCircle className="mr-2 h-4 w-4 text-destructive" />
              Mark as Failed
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleStatusChange('skipped')}>
              <Circle className="mr-2 h-4 w-4" />
              Mark as Skipped
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  );
};
