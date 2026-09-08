import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Button } from '../ui/Button';

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ message = 'An error occurred loading the data.', onRetry }) => (
  <div className="flex flex-col items-center justify-center p-12 text-center rounded-lg border border-border bg-base h-full">
    <AlertCircle className="w-10 h-10 text-critical mb-4" />
    <h3 className="mb-2 text-lg font-medium text-slate-900">Error Loading Data</h3>
    <p className="mb-6 text-sm text-slate-500 max-w-sm">{message}</p>
    {onRetry && (
      <Button variant="secondary" onClick={onRetry}>Retry</Button>
    )}
  </div>
);
