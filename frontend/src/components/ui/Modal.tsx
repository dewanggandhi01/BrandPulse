import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { Spinner } from './Spinner';

export type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | 'full';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string | React.ReactNode;
  children: React.ReactNode;
  maxWidth?: string;
  size?: ModalSize;
  isLoading?: boolean;
  className?: string;
}

const SIZE_WIDTH_CONFIG: Record<ModalSize, { widthPx: number; minWidthPx: number }> = {
  sm: { widthPx: 480, minWidthPx: 360 },
  md: { widthPx: 600, minWidthPx: 400 },
  lg: { widthPx: 680, minWidthPx: 440 },
  xl: { widthPx: 760, minWidthPx: 480 },
  '2xl': { widthPx: 860, minWidthPx: 520 },
  '3xl': { widthPx: 960, minWidthPx: 560 },
  '4xl': { widthPx: 1080, minWidthPx: 600 },
  '5xl': { widthPx: 1200, minWidthPx: 640 },
  full: { widthPx: 1400, minWidthPx: 720 },
};

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  maxWidth,
  size = 'md',
  isLoading = false,
  className = '',
}) => {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Resolve target size: if maxWidth is provided, map recognized tailwind tokens
  let effectiveSize = size;
  if (maxWidth) {
    if (maxWidth.includes('max-w-sm')) effectiveSize = 'sm';
    else if (maxWidth.includes('max-w-md')) effectiveSize = 'md';
    else if (maxWidth.includes('max-w-lg')) effectiveSize = 'md';
    else if (maxWidth.includes('max-w-xl')) effectiveSize = 'lg';
    else if (maxWidth.includes('max-w-2xl')) effectiveSize = 'xl';
    else if (maxWidth.includes('max-w-3xl')) effectiveSize = '2xl';
    else if (maxWidth.includes('max-w-4xl')) effectiveSize = '4xl';
    else if (maxWidth.includes('max-w-5xl')) effectiveSize = '5xl';
  }

  const { widthPx, minWidthPx } = SIZE_WIDTH_CONFIG[effectiveSize] || SIZE_WIDTH_CONFIG.md;

  return createPortal(
    <div
      className="fixed inset-0 z-[9999] overflow-y-auto overflow-x-hidden"
      role="region"
      aria-label="Modal Overlay"
    >
      {/* Dimmed Background Overlay */}
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs transition-opacity cursor-pointer"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Centering Layout Container */}
      <div className="min-h-full flex items-center justify-center p-4 sm:p-6 text-center">
        {/* Modal Dialog Box */}
        <div
          className={`relative z-10 text-left bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden max-h-[90vh] shrink-0 my-auto ${className}`}
          style={{
            width: `min(92vw, ${widthPx}px)`,
            minWidth: `min(92vw, ${minWidthPx}px)`,
            maxWidth: `min(92vw, ${widthPx}px)`,
            flexShrink: 0,
            boxSizing: 'border-box',
          }}
          role="dialog"
          aria-modal="true"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 shrink-0 bg-white">
            <div className="font-bold text-slate-900 tracking-tight text-lg flex items-center gap-2">
              {typeof title === 'string' ? <h2>{title}</h2> : title}
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close modal"
              className="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer shrink-0 ml-4"
            >
              <X size={20} />
            </button>
          </div>

          {/* Body Content / Loading State */}
          <div className="overflow-y-auto p-6 flex-1 break-words">
            {isLoading ? (
              <div className="py-16 flex flex-col items-center justify-center space-y-3 text-center w-full">
                <Spinner size="lg" />
                <p className="text-sm font-medium text-slate-500">Loading content...</p>
              </div>
            ) : (
              children
            )}
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};
