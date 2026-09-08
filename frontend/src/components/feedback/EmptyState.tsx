import React from 'react';
import { Button } from '../ui/Button';

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ icon, title, description, actionLabel, onAction }) => (
  <div className="flex flex-col items-center justify-center p-12 text-center h-full border border-dashed border-border rounded-lg bg-base">
    <div className="mb-4 text-muted flex justify-center">{icon}</div>
    <h3 className="mb-2 text-lg font-semibold text-slate-900">{title}</h3>
    <p className="mb-6 text-sm text-slate-500 max-w-sm">{description}</p>
    {actionLabel && onAction && (
      <Button onClick={onAction}>{actionLabel}</Button>
    )}
  </div>
);
