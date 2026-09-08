import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  Globe,
  ShoppingBag,
  Users,
  Layers,
  Radio,
  Target,
  FileText,
  Building2,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Database,
  Cpu,
  Plus,
  Play,
} from 'lucide-react';
import { useGetBrands } from '../api/queries/useBrands';
import { useAppStore } from '../stores/appStore';
import { Card, CardBody } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/feedback/EmptyState';
import { AddBrandModal } from '../components/brands/AddBrandModal';
import { ScrapeJobModal } from '../components/crawling/ScrapeJobModal';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { currentBrandId, setCurrentBrandId } = useAppStore();
  const { data: brands = [], isLoading } = useGetBrands();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedCrawlBrand, setSelectedCrawlBrand] = useState<{ id: string; domain: string } | null>(null);

  const handleSelectBrand = (brandId: string, targetPath?: string) => {
    setCurrentBrandId(brandId);
    if (targetPath) {
      navigate(targetPath);
    }
  };

  const currentBrand = brands.find((b) => b.id === currentBrandId) || brands[0] || null;

  const modules = [
    {
      title: 'SEO Audit Engine',
      description: 'Algorithmic 4-pillar analysis across technical, content, schema, and links with 43+ checks.',
      path: '/seo',
      icon: <Activity className="text-blue-600" size={22} />,
      color: 'border-blue-200 bg-blue-50/30',
      badge: '4 Pillars',
    },
    {
      title: 'Product & Pricing',
      description: 'Multi-strategy JSON-LD, hydration, and DOM extraction with time-series price tracking.',
      path: '/products',
      icon: <ShoppingBag className="text-emerald-600" size={22} />,
      color: 'border-emerald-200 bg-emerald-50/30',
      badge: 'Catalog & Parity',
    },
    {
      title: 'Competitor Intelligence',
      description: 'Side-by-side benchmark matrix with relative price indexing and multi-brand radar overlays.',
      path: '/competitors',
      icon: <Users className="text-indigo-600" size={22} />,
      color: 'border-indigo-200 bg-indigo-50/30',
      badge: 'Benchmarking',
    },
    {
      title: 'Website Change Diffing',
      description: 'DOM cleanup, SequenceMatcher comparator, and algorithmic classification of revisions.',
      path: '/changes',
      icon: <Layers className="text-amber-600" size={22} />,
      color: 'border-amber-200 bg-amber-50/30',
      badge: 'Visual Diffs',
    },
    {
      title: 'Social Sentiment & Mentions',
      description: 'VADER-style multi-lexicon sentiment analysis with Net Sentiment Score and topic extraction.',
      path: '/mentions',
      icon: <Radio className="text-pink-600" size={22} />,
      color: 'border-pink-200 bg-pink-50/30',
      badge: 'NSS Metrics',
    },
    {
      title: 'Ad Intelligence',
      description: 'Multi-platform ad creative parsing, headline/CTA extraction, and longevity spend estimation.',
      path: '/ads',
      icon: <Target className="text-purple-600" size={22} />,
      color: 'border-purple-200 bg-purple-50/30',
      badge: 'Longevity Tiers',
    },
    {
      title: 'Executive Reporting',
      description: 'Multi-source intelligence aggregation, composite health score, and 4-quadrant SWOT matrix.',
      path: '/reports',
      icon: <FileText className="text-cyan-600" size={22} />,
      color: 'border-cyan-200 bg-cyan-50/30',
      badge: 'SWOT Matrix',
    },
    {
      title: 'Crawling & Snapshots',
      description: 'Tier 1 HTTP, Tier 2 API, Tier 3 Playwright browser crawling with RFC 9309 compliance.',
      path: currentBrand ? `/brands/${currentBrand.id}` : '/',
      icon: <Globe className="text-slate-700" size={22} />,
      color: 'border-slate-200 bg-slate-50/30',
      badge: '3-Tier Engine',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-200">
              BrandPulse Platform
            </span>
            <span className="flex items-center gap-1 text-xs text-emerald-600 font-medium bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              <CheckCircle2 size={12} /> Systems Operational
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
            Brand Intelligence & Competitor Tracking Hub
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Autonomous multi-engine intelligence synthesizing SEO, catalog pricing, web changes, social reputation, and paid ad velocity.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 shrink-0">
          <Button
            variant="primary"
            onClick={() => setIsAddModalOpen(true)}
            className="gap-2 shadow-xs cursor-pointer"
          >
            <Plus size={16} /> Add Brand
          </Button>

          {currentBrand && (
            <Button
              variant="secondary"
              onClick={() => setSelectedCrawlBrand({ id: currentBrand.id, domain: currentBrand.domain })}
              className="gap-2 shadow-xs cursor-pointer text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200"
            >
              <Play size={15} /> Run Website Crawl
            </Button>
          )}

          {currentBrand && (
            <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-xs flex items-center gap-3">
              <div className="p-2 bg-blue-100 text-blue-700 rounded-lg">
                <Building2 size={20} />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-semibold uppercase">Active Monitored Brand</p>
                <p className="text-sm font-bold text-slate-900">{currentBrand.name}</p>
                <p className="text-xs text-slate-400 font-mono">{currentBrand.domain}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Platform Status KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border border-slate-200">
          <CardBody className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-blue-50 text-blue-600 rounded-lg">
              <Building2 size={22} />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Monitored Brands
              </p>
              <p className="text-xl font-bold text-slate-900 font-mono">
                {isLoading ? '...' : brands.length}
              </p>
            </div>
          </CardBody>
        </Card>

        <Card className="border border-slate-200">
          <CardBody className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-lg">
              <Cpu size={22} />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Intelligence Engines
              </p>
              <p className="text-xl font-bold text-slate-900 font-mono">
                8 Active
              </p>
            </div>
          </CardBody>
        </Card>

        <Card className="border border-slate-200">
          <CardBody className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-purple-50 text-purple-600 rounded-lg">
              <Database size={22} />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Celery Queues
              </p>
              <p className="text-sm font-bold text-slate-900 font-mono">
                scraping • analysis • seo • diffing
              </p>
            </div>
          </CardBody>
        </Card>

        <Card className="border border-slate-200">
          <CardBody className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-cyan-50 text-cyan-600 rounded-lg">
              <ShieldCheck size={22} />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Compliance Protocol
              </p>
              <p className="text-sm font-bold text-slate-900">
                RFC 9309 Robots / Token Bucket
              </p>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Monitored Brands Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <Building2 size={18} className="text-blue-600" />
              Tracked Brands Portfolio
            </h2>
            <span className="text-xs text-slate-500">
              Select a brand to view comprehensive audits or trigger website crawls
            </span>
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsAddModalOpen(true)}
            className="gap-1.5 text-xs shadow-xs cursor-pointer"
          >
            <Plus size={14} /> Add Brand
          </Button>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-36 w-full rounded-xl" />
            ))}
          </div>
        ) : brands.length === 0 ? (
          <Card className="border border-slate-200">
            <CardBody className="py-10 flex flex-col items-center justify-center">
              <EmptyState
                icon={<Building2 size={40} className="text-slate-400" />}
                title="No Brands Configured"
                description="Start monitoring your brand or competitors by adding a domain."
              />
              <div className="mt-4">
                <Button variant="primary" onClick={() => setIsAddModalOpen(true)} className="gap-2">
                  <Plus size={16} /> Add First Brand
                </Button>
              </div>
            </CardBody>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {brands.map((brand) => {
              const isSelected = brand.id === currentBrandId;
              return (
                <div
                  key={brand.id}
                  className={`bg-white rounded-xl border p-5 transition-all shadow-xs flex flex-col justify-between ${
                    isSelected
                      ? 'border-blue-500 ring-2 ring-blue-500/20'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-bold text-slate-900 text-base">
                        {brand.name}
                      </h3>
                      {isSelected ? (
                        <Badge variant="info">Active</Badge>
                      ) : (
                        <Badge variant="default">Tracked</Badge>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 font-mono mb-2">
                      {brand.domain}
                    </p>
                    {brand.industry && (
                      <span className="text-[11px] font-medium bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                        {brand.industry}
                      </span>
                    )}
                  </div>

                  <div className="mt-4 pt-4 border-t border-slate-100 flex items-center gap-2 justify-between">
                    <Button
                      variant={isSelected ? 'secondary' : 'ghost'}
                      size="sm"
                      onClick={() => handleSelectBrand(brand.id)}
                      className="text-xs"
                    >
                      {isSelected ? 'Active' : 'Select'}
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setSelectedCrawlBrand({ id: brand.id, domain: brand.domain })}
                      className="text-xs flex items-center gap-1 text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200"
                    >
                      <Play size={12} />
                      <span>Run Crawl</span>
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSelectBrand(brand.id, `/brands/${brand.id}`)}
                      className="text-xs flex items-center gap-1 text-slate-600 hover:text-slate-900"
                    >
                      <span>Hub</span>
                      <ArrowRight size={12} />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Intelligence Modules Showcase */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
            <Activity size={18} className="text-slate-500" />
            Intelligence Dashboards & Tools
          </h2>
          <span className="text-xs text-slate-500">
            Deep-dive into specific intelligence pillars
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {modules.map((mod, idx) => (
            <div
              key={idx}
              onClick={() => navigate(mod.path)}
              className="bg-white border border-slate-200 rounded-xl p-5 hover:shadow-md hover:border-blue-300 transition-all cursor-pointer flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="p-2.5 rounded-lg bg-slate-50 group-hover:scale-105 transition-transform">
                    {mod.icon}
                  </div>
                  <Badge variant="default" className="text-[10px]">
                    {mod.badge}
                  </Badge>
                </div>
                <h3 className="font-bold text-slate-900 text-sm mb-1 group-hover:text-blue-600 transition-colors">
                  {mod.title}
                </h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  {mod.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-blue-600 group-hover:text-blue-700">
                <span>Explore Module</span>
                <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          ))}
        </div>
      </div>

      <AddBrandModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
      />

      {selectedCrawlBrand && (
        <ScrapeJobModal
          isOpen={!!selectedCrawlBrand}
          onClose={() => setSelectedCrawlBrand(null)}
          brandId={selectedCrawlBrand.id}
          defaultDomain={selectedCrawlBrand.domain}
        />
      )}
    </div>
  );
};
