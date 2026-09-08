import React from 'react';
import clsx from 'clsx';

export interface CardProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'title'> {
  title?: React.ReactNode;
  action?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({ className, children, title, action, ...props }) => (
  <div className={clsx('bg-surface rounded-lg border border-border shadow-sm overflow-hidden', className)} {...props}>
    {(title || action) && (
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        {title && <h3 className="text-sm font-semibold text-slate-800">{title}</h3>}
        {action && <div>{action}</div>}
      </div>
    )}
    <div className="p-4">{children}</div>
  </div>
);

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={clsx('px-4 py-3 border-b border-border font-medium text-slate-800', className)} {...props} />
);

export const CardBody: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={clsx('p-4', className)} {...props} />
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={clsx('px-4 py-3 border-t border-border', className)} {...props} />
);
