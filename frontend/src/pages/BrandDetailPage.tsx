import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronRight, Play, Globe } from 'lucide-react';
import { useGetBrand } from '@/api/queries/useBrands';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { ScrapeJobModal } from '@/components/crawling/ScrapeJobModal';
import { ScrapeJobList } from '@/components/crawling/ScrapeJobList';

export const BrandDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [isCrawlModalOpen, setIsCrawlModalOpen] = useState(false);
  const { data: brand, isLoading } = useGetBrand(id || '');

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center text-sm text-muted">
        <Link to="/" className="hover:text-slate-900">Brands</Link>
        <ChevronRight size={16} className="mx-2" />
        <span className="text-slate-900 font-medium">{brand?.name || id}</span>
      </div>

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-[31.25px] font-bold text-slate-900 tracking-tight">
              {brand?.name || `Brand: ${id}`}
            </h1>
            {brand?.industry && <Badge variant="info">{brand.industry}</Badge>}
          </div>
          {brand?.domain && (
            <div className="flex items-center gap-1.5 text-sm text-slate-500 mt-1">
              <Globe size={14} />
              <a href={`https://${brand.domain}`} target="_blank" rel="noreferrer" className="hover:underline">
                {brand.domain}
              </a>
            </div>
          )}
        </div>

        <Button
          variant="primary"
          onClick={() => setIsCrawlModalOpen(true)}
          className="gap-2"
        >
          <Play size={16} /> Run Website Crawl
        </Button>
      </div>

      {id && <ScrapeJobList brandId={id} />}

      {id && (
        <ScrapeJobModal
          isOpen={isCrawlModalOpen}
          onClose={() => setIsCrawlModalOpen(false)}
          brandId={id}
          defaultDomain={brand?.domain}
        />
      )}
    </div>
  );
};
