const fs = require('fs');
const path = require('path');

const files = {
  'package.json': `{
  "name": "brandpulse-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.0.0",
    "axios": "^1.7.0",
    "clsx": "^2.1.0",
    "lucide-react": "^0.400.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0",
    "recharts": "^2.12.0",
    "zustand": "^5.0.0"
  },
  "devDependencies": {
    "@playwright/test": "^1.40.0",
    "@tailwindcss/vite": "^4.0.0",
    "@testing-library/react": "^16.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "eslint": "^9.0.0",
    "prettier": "^3.2.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.6.0",
    "vite": "^6.0.0",
    "vitest": "^2.0.0"
  }
}`,

  'tsconfig.json': `{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}`,

  'tsconfig.node.json': `{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}`,

  'vite.config.ts': `import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});`,

  'index.html': `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <title>BrandPulse</title>
  </head>
  <body class="bg-base text-slate-900 font-sans antialiased">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>`,

  'src/app.css': `@import "tailwindcss";

@theme {
  --color-brand-50: oklch(0.97 0.01 250);
  --color-brand-100: oklch(0.93 0.02 250);
  --color-brand-500: oklch(0.55 0.15 250);
  --color-brand-600: oklch(0.48 0.17 250);
  --color-brand-700: oklch(0.40 0.15 250);
  --color-surface: oklch(1.0 0 0);
  --color-base: oklch(0.985 0.002 250);
  --color-muted: oklch(0.55 0.01 250);
  --color-border: oklch(0.90 0.005 250);
  --color-success: oklch(0.55 0.15 145);
  --color-warning: oklch(0.70 0.15 75);
  --color-critical: oklch(0.55 0.20 25);
  
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-2xl: 48px;
  --spacing-3xl: 64px;
}

@layer base {
  body {
    font-variant-numeric: tabular-nums;
  }
}`,

  'src/main.tsx': `import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { App } from './App';
import './app.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>
);`,

  'src/App.tsx': `import { BrowserRouter } from 'react-router-dom';
import { AppRouter } from './router';
import { AppShell } from './components/layout/AppShell';

export function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <AppRouter />
      </AppShell>
    </BrowserRouter>
  );
}`,

  'src/router.tsx': `import { Routes, Route } from 'react-router-dom';
import { DashboardPage } from './pages/DashboardPage';
import { BrandDetailPage } from './pages/BrandDetailPage';
import { SeoAuditPage } from './pages/SeoAuditPage';
import { ProductsPage } from './pages/ProductsPage';
import { CompetitorsPage } from './pages/CompetitorsPage';
import { ChangesPage } from './pages/ChangesPage';
import { MentionsPage } from './pages/MentionsPage';
import { AdsPage } from './pages/AdsPage';
import { ReportsPage } from './pages/ReportsPage';

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/brands/:id" element={<BrandDetailPage />} />
      <Route path="/seo" element={<SeoAuditPage />} />
      <Route path="/products" element={<ProductsPage />} />
      <Route path="/competitors" element={<CompetitorsPage />} />
      <Route path="/changes" element={<ChangesPage />} />
      <Route path="/mentions" element={<MentionsPage />} />
      <Route path="/ads" element={<AdsPage />} />
      <Route path="/reports" element={<ReportsPage />} />
    </Routes>
  );
}`,

  'src/api/client.ts': `import axios from 'axios';

export const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Global error handling could go here
    return Promise.reject(error);
  }
);`,

  'src/api/queries/useBrands.ts': `import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../client';
import { Brand } from '@/types';

export const useGetBrands = () => {
  return useQuery({
    queryKey: ['brands'],
    queryFn: async () => {
      const { data } = await apiClient.get<Brand[]>('/brands');
      return data;
    },
  });
};

export const useGetBrand = (id: string) => {
  return useQuery({
    queryKey: ['brands', id],
    queryFn: async () => {
      const { data } = await apiClient.get<Brand>(\`/brands/\${id}\`);
      return data;
    },
    enabled: !!id,
  });
};

export const useCreateBrand = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (newBrand: Partial<Brand>) => {
      const { data } = await apiClient.post<Brand>('/brands', newBrand);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['brands'] });
    },
  });
};`,

  'src/stores/appStore.ts': `import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AppState {
  sidebarCollapsed: boolean;
  currentBrandId: string | null;
  theme: 'light' | 'dark';
  setSidebarCollapsed: (collapsed: boolean) => void;
  setCurrentBrandId: (id: string | null) => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      currentBrandId: null,
      theme: 'light',
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      setCurrentBrandId: (id) => set({ currentBrandId: id }),
      setTheme: (theme) => set({ theme }),
    }),
    { name: 'brandpulse-store' }
  )
);`,

  'src/types/index.ts': `export interface Brand {
  id: string;
  name: string;
  website: string;
  createdAt: string;
}

export interface BrandUrl {
  id: string;
  brandId: string;
  url: string;
}

export interface ScrapeJob {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startedAt: string;
  completedAt?: string;
}

export interface Snapshot {
  id: string;
  urlId: string;
  timestamp: string;
}

export interface SeoAudit {
  id: string;
  urlId: string;
  score: number;
  issues: string[];
}

export interface Product {
  id: string;
  brandId: string;
  name: string;
  price: number;
}

export interface PriceHistory {
  id: string;
  productId: string;
  price: number;
  timestamp: string;
}

export interface ChangeEvent {
  id: string;
  brandId: string;
  description: string;
  timestamp: string;
}

export interface Mention {
  id: string;
  brandId: string;
  source: string;
  content: string;
  url: string;
  timestamp: string;
}

export interface Sentiment {
  id: string;
  mentionId: string;
  score: number;
  label: 'positive' | 'neutral' | 'negative';
}

export interface AdIntel {
  id: string;
  brandId: string;
  platform: string;
  spend: number;
}

export interface Report {
  id: string;
  brandId: string;
  title: string;
  generatedAt: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
}`,

  'src/hooks/useMediaQuery.ts': `import { useState, useEffect } from 'react';

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    if (media.matches !== matches) {
      setMatches(media.matches);
    }
    const listener = () => setMatches(media.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [matches, query]);

  return matches;
}`,

  'src/components/ui/Button.tsx': `import React from 'react';
import clsx from 'clsx';
import { Spinner } from './Spinner';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading,
  className,
  disabled,
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:opacity-50 disabled:pointer-events-none rounded';
  
  const variants = {
    primary: 'bg-brand-600 text-white hover:bg-brand-700',
    secondary: 'bg-brand-50 text-brand-700 hover:bg-brand-100 border border-brand-100',
    ghost: 'bg-transparent text-slate-700 hover:bg-slate-100',
    destructive: 'bg-critical text-white hover:bg-red-700',
  };

  const sizes = {
    sm: 'h-8 px-3 text-sm',
    md: 'h-10 px-4 text-base',
    lg: 'h-12 px-6 text-lg',
  };

  return (
    <button
      className={clsx(baseClasses, variants[variant], sizes[size], className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Spinner size="sm" className="mr-2" />}
      {children}
    </button>
  );
};`,

  'src/components/ui/Input.tsx': `import React from 'react';
import clsx from 'clsx';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, className, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1 w-full">
        {label && <label className="text-sm font-medium text-slate-700">{label}</label>}
        <input
          ref={ref}
          className={clsx(
            'flex h-10 w-full rounded border bg-surface px-3 py-2 text-sm text-slate-900 placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:cursor-not-allowed disabled:opacity-50',
            error ? 'border-critical focus:ring-critical' : 'border-border',
            className
          )}
          {...props}
        />
        {(error || helperText) && (
          <p className={clsx('text-xs', error ? 'text-critical' : 'text-muted')}>
            {error || helperText}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = 'Input';`,

  'src/components/ui/Card.tsx': `import React from 'react';
import clsx from 'clsx';

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => (
  <div className={clsx('bg-surface rounded-lg border border-border shadow-sm', className)} {...props}>
    {children}
  </div>
);

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={clsx('p-md border-b border-border', className)} {...props} />
);

export const CardBody: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={clsx('p-md', className)} {...props} />
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={clsx('p-md border-t border-border', className)} {...props} />
);`,

  'src/components/ui/Badge.tsx': `import React from 'react';
import clsx from 'clsx';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'critical' | 'info';
}

export const Badge: React.FC<BadgeProps> = ({ variant = 'default', className, children, ...props }) => {
  const variants = {
    default: 'bg-slate-100 text-slate-800',
    success: 'bg-green-100 text-success',
    warning: 'bg-yellow-100 text-warning',
    critical: 'bg-red-100 text-critical',
    info: 'bg-brand-50 text-brand-600',
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};`,

  'src/components/ui/Modal.tsx': `import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import clsx from 'clsx';
import { Button } from './Button';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children }) => {
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={onClose} />
      <div className="z-50 w-full max-w-lg rounded-lg bg-surface p-6 shadow-xl relative m-4 max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between mb-4 shrink-0">
          <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close modal" className="!p-2">
            <X size={20} />
          </Button>
        </div>
        <div className="overflow-y-auto pr-2">
          {children}
        </div>
      </div>
    </div>
  );
};`,

  'src/components/ui/Spinner.tsx': `import React from 'react';
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
};`,

  'src/components/ui/Skeleton.tsx': `import React from 'react';
import clsx from 'clsx';

export const Skeleton: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => {
  return (
    <div
      className={clsx('animate-pulse rounded bg-slate-200', className)}
      {...props}
    />
  );
};`,

  'src/components/feedback/EmptyState.tsx': `import React from 'react';
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
);`,

  'src/components/feedback/ErrorBoundary.tsx': `import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle } from 'lucide-react';
import { Button } from '../ui/Button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center bg-base rounded-lg border border-border">
          <AlertCircle className="w-12 h-12 text-critical mb-4" />
          <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
          <p className="text-muted mb-6 max-w-md">{this.state.error?.message}</p>
          <Button onClick={() => this.setState({ hasError: false })}>Try again</Button>
        </div>
      );
    }

    return this.props.children;
  }
}`,

  'src/components/feedback/ErrorState.tsx': `import React from 'react';
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
);`,

  'src/components/feedback/Toast.tsx': `import React from 'react';
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
};`,

  'src/components/layout/Sidebar.tsx': `import React from 'react';
import { NavLink } from 'react-router-dom';
import clsx from 'clsx';
import { 
  LayoutDashboard, 
  Search, 
  Package, 
  Users, 
  Activity, 
  MessageSquare, 
  Megaphone, 
  FileText,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { useAppStore } from '@/stores/appStore';

export const Sidebar: React.FC = () => {
  const { sidebarCollapsed, setSidebarCollapsed } = useAppStore();

  const navItems = [
    { to: '/', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { to: '/seo', icon: <Search size={20} />, label: 'SEO Audit' },
    { to: '/products', icon: <Package size={20} />, label: 'Products' },
    { to: '/competitors', icon: <Users size={20} />, label: 'Competitors' },
    { to: '/changes', icon: <Activity size={20} />, label: 'Changes' },
    { to: '/mentions', icon: <MessageSquare size={20} />, label: 'Mentions' },
    { to: '/ads', icon: <Megaphone size={20} />, label: 'Ads Intel' },
    { to: '/reports', icon: <FileText size={20} />, label: 'Reports' },
  ];

  return (
    <aside
      className={clsx(
        'bg-surface border-r border-border h-screen sticky top-0 flex flex-col transition-all duration-300',
        sidebarCollapsed ? 'w-16' : 'w-64'
      )}
    >
      <div className="h-16 flex items-center px-4 border-b border-border justify-between shrink-0">
        {!sidebarCollapsed && <span className="font-bold text-lg text-brand-600 truncate">BrandPulse</span>}
        {sidebarCollapsed && <span className="font-bold text-xl text-brand-600 mx-auto">BP</span>}
      </div>
      
      <div className="flex-1 overflow-y-auto py-4 flex flex-col gap-1 px-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => clsx(
              'flex items-center gap-3 px-3 py-2 rounded transition-colors group',
              isActive 
                ? 'bg-brand-50 text-brand-600 font-medium' 
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
              sidebarCollapsed && 'justify-center px-0'
            )}
            title={sidebarCollapsed ? item.label : undefined}
          >
            <span className="shrink-0">{item.icon}</span>
            {!sidebarCollapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </div>

      <div className="p-2 border-t border-border shrink-0">
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="flex w-full items-center justify-center p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900 rounded transition-colors"
        >
          {sidebarCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>
    </aside>
  );
};`,

  'src/components/layout/Topbar.tsx': `import React from 'react';
import { Search as SearchIcon, Settings, Bell } from 'lucide-react';
import { Input } from '../ui/Input';

export const Topbar: React.FC = () => {
  return (
    <header className="h-16 bg-surface border-b border-border flex items-center justify-between px-6 sticky top-0 z-10 shrink-0">
      <div className="flex items-center flex-1 max-w-md">
        <div className="relative w-full">
          <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={18} />
          <Input 
            placeholder="Search brands, products..." 
            className="pl-10 h-9"
          />
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <button className="text-slate-500 hover:text-slate-900 relative">
          <Bell size={20} />
          <span className="absolute top-0 right-0 w-2 h-2 bg-brand-500 rounded-full border border-surface"></span>
        </button>
        <button className="text-slate-500 hover:text-slate-900">
          <Settings size={20} />
        </button>
        <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-semibold text-sm border border-brand-200">
          U
        </div>
      </div>
    </header>
  );
};`,

  'src/components/layout/AppShell.tsx': `import React from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { ErrorBoundary } from '../feedback/ErrorBoundary';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  return (
    <div className="flex min-h-screen bg-base">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <Topbar />
        <main className="flex-1 p-6 overflow-y-auto">
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
};`,

  'src/pages/DashboardPage.tsx': `import React, { useState } from 'react';
import { LayoutDashboard } from 'lucide-react';
import { EmptyState } from '../components/feedback/EmptyState';
import { Skeleton } from '../components/ui/Skeleton';
import { Card, CardBody, CardHeader } from '../components/ui/Card';

export const DashboardPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any[]>([]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[31.25px] font-bold text-slate-900 tracking-tight">Dashboard</h1>
          <p className="text-muted text-sm mt-1">Overview of your monitored brands.</p>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      ) : data.length === 0 ? (
        <EmptyState
          icon={<LayoutDashboard size={48} />}
          title="No data yet"
          description="Start monitoring a brand to see dashboard metrics."
          actionLabel="Add Brand"
          onAction={() => {}}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
           <Card><CardHeader>Total Brands</CardHeader><CardBody>0</CardBody></Card>
        </div>
      )}
    </div>
  );
};`,

  'src/pages/BrandDetailPage.tsx': `import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronRight, Building } from 'lucide-react';
import { EmptyState } from '../components/feedback/EmptyState';

export const BrandDetailPage: React.FC = () => {
  const { id } = useParams();

  return (
    <div className="space-y-6">
      <div className="flex items-center text-sm text-muted">
        <Link to="/" className="hover:text-slate-900">Brands</Link>
        <ChevronRight size={16} className="mx-2" />
        <span className="text-slate-900 font-medium">Brand Detail</span>
      </div>
      
      <h1 className="text-[31.25px] font-bold text-slate-900 tracking-tight">Brand: {id}</h1>
      
      <EmptyState
        icon={<Building size={48} />}
        title="No detailed info yet"
        description="Data for this brand is still being collected."
      />
    </div>
  );
};`,

  'src/pages/SeoAuditPage.tsx': `import React from 'react';
import { Search } from 'lucide-react';
import { EmptyState } from '../components/feedback/EmptyState';

export const SeoAuditPage: React.FC = () => {
  return (
    <div className="space-y-6 h-full flex flex-col">
      <h1 className="text-[31.25px] font-bold text-slate-900 tracking-tight">SEO Audit</h1>
      <div className="flex-1">
        <EmptyState
          icon={<Search size={48} />}
          title="No SEO Audits"
          description="Run your first SEO audit to get actionable insights."
          actionLabel="Run Audit"
          onAction={() => {}}
        />
      </div>
    </div>
  );
};`,

  'src/pages/ProductsPage.tsx': `import React from 'react';
import { Package } from 'lucide-react';
import { EmptyState } from '../components/feedback/EmptyState';

export const ProductsPage: React.FC = () => {
  return (
    <div className="space-y-6 h-full flex flex-col">
      <h1 className="text-[31.25px] font-bold text-slate-900 tracking-tight">Products</h1>
      <div className="flex-1">
        <EmptyState
          icon={<Package size={48} />}
          title="No Products Found"
          description="We haven't detected any products for your monitored brands yet."
        />
      </div>
    </div>
  );
};`,

  'src/pages/CompetitorsPage.tsx': `import React from 'react';
import { Users } from 'lucide-react';
import { EmptyState } from '../components/feedback/EmptyState';

export const CompetitorsPage: React.FC = () => {
  return (
    <div className="space-y-6 h-full flex flex-col">
      <h1 className="text-[31.25px] font-bold text-slate-900 tracking-tight">Competitors</h1>
      <div className="flex-1">
        <EmptyState
          icon={<Users size={48} />}
          title="No Competitors Tracking"
          description="Add competitor brands to compare performance."
          actionLabel="Add Competitor"
          onAction={() => {}}
        />
      </div>
    </div>
  );
};`,

  'src/pages/ChangesPage.tsx': `import React from 'react';
import { Activity } from 'lucide-react';
import { EmptyState } from '../components/feedback/EmptyState';

export const ChangesPage: React.FC = () => {
  return (
    <div className="space-y-6 h-full flex flex-col">
      <h1 className="text-[31.25px] font-bold text-slate-900 tracking-tight">Changes log</h1>
      <div className="flex-1">
        <EmptyState
          icon={<Activity size={48} />}
          title="No Activity"
          description="No recent changes detected in the tracked properties."
        />
      </div>
    </div>
  );
};`,

  'src/pages/MentionsPage.tsx': `import React from 'react';
import { MessageSquare } from 'lucide-react';
import { EmptyState } from '../components/feedback/EmptyState';

export const MentionsPage: React.FC = () => {
  return (
    <div className="space-y-6 h-full flex flex-col">
      <h1 className="text-[31.25px] font-bold text-slate-900 tracking-tight">Mentions</h1>
      <div className="flex-1">
        <EmptyState
          icon={<MessageSquare size={48} />}
          title="No Mentions"
          description="We are scanning the web for mentions of your brands."
        />
      </div>
    </div>
  );
};`,

  'src/pages/AdsPage.tsx': `import React from 'react';
import { Megaphone } from 'lucide-react';
import { EmptyState } from '../components/feedback/EmptyState';

export const AdsPage: React.FC = () => {
  return (
    <div className="space-y-6 h-full flex flex-col">
      <h1 className="text-[31.25px] font-bold text-slate-900 tracking-tight">Ads Intel</h1>
      <div className="flex-1">
        <EmptyState
          icon={<Megaphone size={48} />}
          title="No Ads Data"
          description="No advertising intelligence data collected yet."
        />
      </div>
    </div>
  );
};`,

  'src/pages/ReportsPage.tsx': `import React from 'react';
import { FileText } from 'lucide-react';
import { EmptyState } from '../components/feedback/EmptyState';

export const ReportsPage: React.FC = () => {
  return (
    <div className="space-y-6 h-full flex flex-col">
      <h1 className="text-[31.25px] font-bold text-slate-900 tracking-tight">Reports</h1>
      <div className="flex-1">
        <EmptyState
          icon={<FileText size={48} />}
          title="No Reports"
          description="Generate your first report to see insights."
          actionLabel="Generate Report"
          onAction={() => {}}
        />
      </div>
    </div>
  );
};`
};

const root = 'd:/Downloads/New project of illuminiti/frontend';

for (const [filePath, content] of Object.entries(files)) {
  const fullPath = path.join(root, filePath);
  const dir = path.dirname(fullPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  fs.writeFileSync(fullPath, content);
}

console.log('Done scaffolding frontend foundation.');
