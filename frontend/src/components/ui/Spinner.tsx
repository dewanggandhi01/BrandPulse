import React from 'react';
import clsx from 'clsx';
import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className }) => {
  const sizes = {
    sm: 16,
    md: 24,
    lg: 32,
  };
  return <Loader2 className={clsx('animate-spin text-brand-600', className)} size={sizes[size]} />;
};
