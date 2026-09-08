import React, { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Globe, Layers, Compass, Play, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useCreateScrapeJob } from '@/api/queries/useScrapeJobs';

interface ScrapeJobModalProps {
  isOpen: boolean;
  onClose: () => void;
  brandId: string;
  defaultDomain?: string;
}

export const ScrapeJobModal: React.FC<ScrapeJobModalProps> = ({
  isOpen,
  onClose,
  brandId,
  defaultDomain = ''
}) => {
  const [seedUrl, setSeedUrl] = useState('');
  const [maxDepth, setMaxDepth] = useState(1);
  const [maxPages, setMaxPages] = useState(10);
  const [tier, setTier] = useState('auto');
  const [isSuccess, setIsSuccess] = useState(false);

  // Sync domain whenever modal opens or defaultDomain is supplied
  useEffect(() => {
    if (isOpen) {
      if (defaultDomain) {
        const clean = defaultDomain.startsWith('http') ? defaultDomain : `https://${defaultDomain}`;
        setSeedUrl(clean);
      } else if (!seedUrl) {
        setSeedUrl('');
      }
      setIsSuccess(false);
    }
  }, [isOpen, defaultDomain]);

  const createJob = useCreateScrapeJob();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    let url = seedUrl.trim();
    if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
      url = `https://${url}`;
    }

    createJob.mutate(
      {
        brand_id: brandId,
        seed_urls: url ? [url] : undefined,
        max_depth: Number(maxDepth),
        max_pages: Number(maxPages),
        tier,
      },
      {
        onSuccess: () => {
          setIsSuccess(true);
          setTimeout(() => {
            onClose();
          }, 800);
        },
      }
    );
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Trigger Website Crawl Job" maxWidth="max-w-xl">
      {isSuccess ? (
        <div className="py-8 flex flex-col items-center justify-center text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">
            <CheckCircle2 size={28} />
          </div>
          <h3 className="text-base font-bold text-slate-900">Crawl Job Dispatched!</h3>
          <p className="text-sm text-slate-500">Celery background workers are now harvesting data.</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5 flex items-center gap-1.5">
              <Globe size={14} className="text-blue-600" /> Target URL to Crawl *
            </label>
            <input
              type="text"
              value={seedUrl}
              onChange={(e) => setSeedUrl(e.target.value)}
              placeholder="https://example.com"
              required
              className="w-full h-10 px-3 py-2 text-sm font-mono bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
            <p className="text-[11px] text-slate-500 mt-1">Starting landing page for internal link discovery.</p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5 flex items-center gap-1.5">
                <Compass size={14} className="text-blue-600" /> Crawl Depth
              </label>
              <select
                value={maxDepth}
                onChange={(e) => setMaxDepth(Number(e.target.value))}
                className="w-full h-10 px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={0}>Depth 0 (Target URL Only)</option>
                <option value={1}>Depth 1 (Direct Links)</option>
                <option value={2}>Depth 2 (Sub-pages)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5 flex items-center gap-1.5">
                <Layers size={14} className="text-blue-600" /> Max Pages Cap
              </label>
              <input
                type="number"
                min={1}
                max={50}
                value={maxPages}
                onChange={(e) => setMaxPages(Number(e.target.value))}
                className="w-full h-10 px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
              Crawler Engine Strategy
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: 'auto', title: 'Auto (Recommended)', desc: 'Fast HTTP with SPA Browser fallback' },
                { id: 'http', title: 'HTTP (Lightweight)', desc: 'Fastest via httpx without JS execution' },
                { id: 'browser', title: 'Headless Browser', desc: 'Playwright Chromium for dynamic JS' },
              ].map((strat) => (
                <div
                  key={strat.id}
                  onClick={() => setTier(strat.id)}
                  className={`p-2.5 rounded-lg border text-left cursor-pointer transition-all flex flex-col justify-between ${
                    tier === strat.id
                      ? 'border-blue-600 bg-blue-50/60 ring-2 ring-blue-500/20'
                      : 'border-slate-200 bg-white hover:border-slate-300'
                  }`}
                >
                  <p className="text-xs font-bold text-slate-900">{strat.title}</p>
                  <p className="text-[10px] text-slate-500 mt-1 leading-tight">{strat.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {createJob.isError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start gap-2">
              <AlertCircle size={16} className="shrink-0 text-red-500 mt-0.5" />
              <span>Failed to schedule crawl job. Ensure Celery broker and backend services are active.</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={createJob.isPending}
              disabled={createJob.isPending}
              className="gap-1.5 shadow-sm"
            >
              <Play size={16} />
              {createJob.isPending ? 'Dispatching...' : 'Start Crawl Job'}
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
};
