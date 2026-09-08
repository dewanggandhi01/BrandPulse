import React from 'react';
import clsx from 'clsx';
import { CheckCircle, XCircle, Info, X } from 'lucide-react';

interface ToastProps {
  type: 'success' | 'error' | 'info';
  message: string;
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({ type, message, onClose }) => {
  const icons = {
    success: <CheckCircle className="text-success w-5 h-5" />,
    error: <XCircle className="text-critical w-5 h-5" />,
    info: <Info className="text-brand-500 w-5 h-5" />,
  };

  const bgStyles = {
    success: 'bg-green-50 border-green-200 text-green-900',
    error: 'bg-red-50 border-red-200 text-red-900',
    info: 'bg-brand-50 border-brand-200 text-brand-900',
  };

  return (
    <div className={clsx('fixed bottom-4 right-4 flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg z-50', bgStyles[type])}>
      {icons[type]}
      <span className="text-sm font-medium">{message}</span>
      <button onClick={onClose} className="ml-2 opacity-60 hover:opacity-100 transition-opacity">
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};
