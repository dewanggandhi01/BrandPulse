import React, { useState } from 'react';
import {
  Users,
  Plus,
  Trash2,
  ExternalLink,
  Award,
  BarChart3,
  Percent,
  RefreshCw,
  Info,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';
import { useGetBrands } from '@/api/queries/useBrands';
import {
  useGetLinkedCompetitors,
  useGetCompetitorComparison,
  useUnlinkCompetitor,
  useSyncCompetitors,
} from '@/api/queries/useCompetitors';
import { useAppStore } from '@/stores/appStore';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/feedback/EmptyState';
import { LinkCompetitorModal } from '@/components/competitors/LinkCompetitorModal';

const RADAR_COLORS = ['#2563EB', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#6366F1'];

export const getCurrencySymbol = (currency?: string | null): string => {
  if (!currency) return '$';
  switch (currency.toUpperCase()) {
    case 'INR':
      return '₹';
    case 'EUR':
      return '€';
    case 'GBP':
      return '£';
    case 'JPY':
      return '¥';
    case 'CAD':
    case 'AUD':
    case 'USD':
    default:
      return '$';
  }
};

export const formatPrice = (price?: number | null, currency?: string | null) => {
  if (price == null) return '—';
  const sym = getCurrencySymbol(currency);
  return `${sym}${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

export const CompetitorsPage: React.FC = () => {
  const { data: brands = [], isLoading: brandsLoading } = useGetBrands();
  const { currentBrandId, setCurrentBrandId } = useAppStore();

  // Active brand resolution: prefer app store selection, fallback to first available brand
  const effectiveBrandId =
    currentBrandId && brands.some((b) => b.id === currentBrandId)
      ? currentBrandId
      : brands[0]?.id || '';

  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false);
  const [syncNotice, setSyncNotice] = useState<string | null>(null);

  // Queries
  const {
    data: linkedCompetitors = [],
    isLoading: linkedLoading,
  } = useGetLinkedCompetitors(effectiveBrandId);

  const {
    data: comparison,
    isLoading: compareLoading,
    refetch: refetchComparison,
  } = useGetCompetitorComparison(effectiveBrandId);

  const unlinkMutation = useUnlinkCompetitor();
  const syncMutation = useSyncCompetitors();

  const target = comparison?.target_brand;
  const competitors = comparison?.competitors || [];
  const radarData = comparison?.radar_data || [];

  const [searchTerm, setSearchTerm] = useState('');
  const [scoreFilter, setScoreFilter] = useState('all'); // all, high (>80), mid (50-80), low (<50)

  const handleBrandChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newId = e.target.value;
    setCurrentBrandId(newId);
  };

  const handleUnlink = (linkId: string) => {
    if (confirm('Are you sure you want to unlink this competitor?')) {
      unlinkMutation.mutate({ linkId, brandId: effectiveBrandId });
    }
  };

  const handleSyncIntelligence = () => {
    if (!effectiveBrandId) return;
    setSyncNotice(null);
    syncMutation.mutate(effectiveBrandId, {
      onSuccess: (res: any) => {
        setSyncNotice(res?.message || 'Intelligence sync triggered for target brand & competitors!');
        setTimeout(() => {
          refetchComparison();
        }, 1500);
        setTimeout(() => {
          setSyncNotice(null);
        }, 6000);
      },
    });
  };

  // Apply filters
  const filteredCompetitors = competitors.filter((c) => {
    if (searchTerm && !c.brand_name.toLowerCase().includes(searchTerm.toLowerCase())) return false;

    if (scoreFilter !== 'all') {
      const score = c.seo_total_score || 0;
      if (scoreFilter === 'high' && score < 80) return false;
      if (scoreFilter === 'mid' && (score >= 80 || score < 50)) return false;
      if (scoreFilter === 'low' && score >= 50) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6 flex flex-col min-h-full pb-10">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Users className="text-brand-600" size={28} />
            Competitor Intelligence & Benchmarking
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Side-by-side market rivalry tracking across search visibility, pricing index, and catalogue breadth.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {brands.length > 0 && (
            <select
              value={effectiveBrandId}
              onChange={handleBrandChange}
              aria-label="Select Monitored Brand"
              className="text-sm font-medium border border-slate-300 rounded-lg px-3 py-2 bg-white text-slate-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              {brands.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name} ({b.domain})
                </option>
              ))}
            </select>
          )}

          <Button
            variant="secondary"
            onClick={handleSyncIntelligence}
            disabled={!effectiveBrandId || syncMutation.isPending}
            className="flex items-center gap-1.5 text-xs"
            title="Trigger background crawl and audits for this brand & all competitors"
          >
            <RefreshCw size={15} className={syncMutation.isPending ? 'animate-spin' : ''} />
            Sync Intelligence
          </Button>

          <Button
            variant="primary"
            onClick={() => setIsLinkModalOpen(true)}
            disabled={!effectiveBrandId}
            className="flex items-center gap-1.5"
          >
            <Plus size={16} />
            Link Competitor
          </Button>
        </div>
      </div>

      {syncNotice && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
          <span>{syncNotice}</span>
        </div>
      )}

      {brandsLoading ? (
        <div className="py-20 flex justify-center">
          <Spinner size="lg" />
        </div>
      ) : brands.length === 0 ? (
        <EmptyState
          icon={<Users size={48} />}
          title="No Monitored Brands"
          description="Create your first brand in the Brands section before linking competitors."
        />
      ) : linkedLoading || compareLoading ? (
        <div className="py-20 flex justify-center">
          <Spinner size="lg" />
        </div>
      ) : linkedCompetitors.length === 0 ? (
        <EmptyState
          icon={<Users size={48} />}
          title="No Competitors Linked Yet"
          description="Link competitor brands to unlock multi-brand radar overlays, price index benchmarking, and side-by-side matrix comparisons."
          actionLabel="Link Competitor Now"
          onAction={() => setIsLinkModalOpen(true)}
        />
      ) : (
        <>
          {/* Executive KPI Benchmark Strip */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-4 bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">SEO Standing</span>
                <span className="p-2 rounded-lg bg-blue-50 text-blue-600">
                  <Award size={18} />
                </span>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 tnum">
                  {target?.seo_total_score != null ? `${target.seo_total_score}/100` : '—'}
                </span>
                <span className="text-xs text-slate-500">
                  vs {competitors.length} competitor{competitors.length === 1 ? '' : 's'}
                </span>
              </div>
            </Card>

            <Card className="p-4 bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Price Index</span>
                <span className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
                  <Percent size={18} />
                </span>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 tnum">
                  {comparison?.price_index != null ? `${comparison.price_index}%` : '100%'}
                </span>
                <span className="text-xs text-slate-500 flex items-center gap-1">
                  {comparison?.price_index && comparison.price_index > 100 ? (
                    <>
                      <TrendingUp size={13} className="text-amber-600" /> Premium pricing
                    </>
                  ) : comparison?.price_index && comparison.price_index < 100 ? (
                    <>
                      <TrendingDown size={13} className="text-emerald-600" /> Value pricing
                    </>
                  ) : (
                    'Market parity'
                  )}
                </span>
              </div>
            </Card>

            <Card className="p-4 bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Catalogue Overlap</span>
                <span className="p-2 rounded-lg bg-purple-50 text-purple-600">
                  <BarChart3 size={18} />
                </span>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 tnum">
                  {target?.product_count ?? 0}
                </span>
                <span className="text-xs text-slate-500">
                  vs {competitors.reduce((acc, c) => acc + c.product_count, 0)} rival items
                </span>
              </div>
            </Card>

            <Card className="p-4 bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tracked Rivals</span>
                <span className="p-2 rounded-lg bg-amber-50 text-amber-600">
                  <Users size={18} />
                </span>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 tnum">
                  {competitors.length}
                </span>
                <span className="text-xs text-slate-500">active competitor links</span>
              </div>
            </Card>
          </div>

          {/* Side-by-Side Radar Chart Overlay & Competitor List */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="p-5 bg-white border border-slate-200 shadow-sm lg:col-span-2">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-base font-bold text-slate-900">4-Pillar Search Visibility Overlay</h2>
                  <p className="text-xs text-slate-500">
                    Comparative audit scores across Technical, Content, Schema, and Link Architecture.
                  </p>
                </div>
              </div>

              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                    <PolarGrid stroke="#E2E8F0" />
                    <PolarAngleAxis dataKey="pillar" tick={{ fill: '#64748B', fontSize: 12, fontWeight: 500 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#CBD5E1" fontSize={10} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0F172A',
                        borderColor: '#1E293B',
                        borderRadius: '8px',
                        color: '#F8FAFC',
                        fontSize: '12px',
                      }}
                    />
                    <Legend />
                    {target && (
                      <Radar
                        name={`${target.brand_name} (Target)`}
                        dataKey={target.brand_name}
                        stroke={RADAR_COLORS[0]}
                        fill={RADAR_COLORS[0]}
                        fillOpacity={0.35}
                        strokeWidth={2}
                      />
                    )}
                    {competitors.map((comp, idx) => (
                      <Radar
                        key={comp.brand_id}
                        name={comp.brand_name}
                        dataKey={comp.brand_name}
                        stroke={RADAR_COLORS[(idx + 1) % RADAR_COLORS.length]}
                        fill={RADAR_COLORS[(idx + 1) % RADAR_COLORS.length]}
                        fillOpacity={0.2}
                        strokeWidth={1.5}
                      />
                    ))}
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              {/* Radar Diagnostic Explanations */}
              <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-2 bg-slate-50 rounded border border-slate-100">
                  <div className="font-semibold text-slate-800">Technical</div>
                  <div className="text-slate-500 text-[11px] mt-0.5">Core Web Vitals, speed, headers, security</div>
                </div>
                <div className="p-2 bg-slate-50 rounded border border-slate-100">
                  <div className="font-semibold text-slate-800">Content</div>
                  <div className="text-slate-500 text-[11px] mt-0.5">Headings, keywords, reading ease, density</div>
                </div>
                <div className="p-2 bg-slate-50 rounded border border-slate-100">
                  <div className="font-semibold text-slate-800">Structured Data</div>
                  <div className="text-slate-500 text-[11px] mt-0.5">Schema.org, JSON-LD, OpenGraph, Twitter cards</div>
                </div>
                <div className="p-2 bg-slate-50 rounded border border-slate-100">
                  <div className="font-semibold text-slate-800">Links</div>
                  <div className="text-slate-500 text-[11px] mt-0.5">Internal mesh, anchor text, external authority</div>
                </div>
              </div>
            </Card>

            {/* Linked Competitors Quick Card */}
            <Card className="p-5 bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-4">
                  <h3 className="text-sm font-bold text-slate-900">Linked Competitors</h3>
                  <Badge variant="info">{linkedCompetitors.length} Active</Badge>
                </div>

                <div className="space-y-3 max-h-[290px] overflow-y-auto pr-1">
                  {linkedCompetitors.map((comp) => (
                    <div
                      key={comp.id}
                      className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between"
                    >
                      <div>
                        <div className="font-semibold text-slate-900 text-sm flex items-center gap-1.5">
                          {comp.competitor_name}
                          <a
                            href={`https://${comp.competitor_domain}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-slate-400 hover:text-slate-600"
                          >
                            <ExternalLink size={12} />
                          </a>
                        </div>
                        <div className="text-xs text-slate-500 font-mono mt-0.5">
                          {comp.competitor_domain}
                        </div>
                        {comp.industry && (
                          <div className="text-[11px] text-slate-400 mt-0.5">
                            {comp.industry}
                          </div>
                        )}
                      </div>

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleUnlink(comp.id)}
                        disabled={unlinkMutation.isPending}
                        className="text-red-600 hover:bg-red-50 !p-1.5"
                        title="Unlink competitor"
                      >
                        <Trash2 size={15} />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-4 mt-4 border-t border-slate-100">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsLinkModalOpen(true)}
                  className="w-full flex items-center justify-center gap-1.5 text-xs"
                >
                  <Plus size={14} /> Add Another Competitor
                </Button>
              </div>
            </Card>
          </div>

          {/* Full Side-by-Side Benchmarking Comparison Matrix */}
          <Card className="bg-white border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-bold text-slate-900">Side-by-Side Competitive Matrix</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Head-to-head metric comparison against monitored competitors.
                </p>
              </div>

              {/* Faceted Filters */}
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Search competitor..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="text-sm border border-slate-300 rounded px-3 py-1.5 focus:outline-none focus:border-brand-500"
                />
                <select
                  value={scoreFilter}
                  onChange={(e) => setScoreFilter(e.target.value)}
                  className="text-sm border border-slate-300 rounded px-3 py-1.5 focus:outline-none focus:border-brand-500"
                >
                  <option value="all">All Scores</option>
                  <option value="high">High (&gt;80)</option>
                  <option value="mid">Mid (50-80)</option>
                  <option value="low">Low (&lt;50)</option>
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3">Brand & Domain</th>
                    <th className="px-4 py-3">SEO Overall</th>
                    <th className="px-4 py-3">Tech</th>
                    <th className="px-4 py-3">Content</th>
                    <th className="px-4 py-3">Schema</th>
                    <th className="px-4 py-3">Links</th>
                    <th className="px-4 py-3">Catalog Size</th>
                    <th className="px-4 py-3">Average Price</th>
                    <th className="px-4 py-3">Price Range</th>
                    <th className="px-4 py-3">In-Stock Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {/* Target Brand (Highlighted) */}
                  {target && (
                    <tr className="bg-blue-50/40 font-medium">
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-brand-700">{target.brand_name}</span>
                          <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-brand-100 text-brand-700">
                            Target
                          </span>
                        </div>
                        <div className="text-xs text-slate-400 font-mono mt-0.5">{target.domain}</div>
                      </td>
                      <td className="px-4 py-3.5 font-bold text-slate-900 tnum">
                        {target.seo_total_score != null ? `${target.seo_total_score}/100` : '—'}
                      </td>
                      <td className="px-4 py-3.5 tnum">{target.technical_score ?? '—'}</td>
                      <td className="px-4 py-3.5 tnum">{target.content_score ?? '—'}</td>
                      <td className="px-4 py-3.5 tnum">{target.structured_data_score ?? '—'}</td>
                      <td className="px-4 py-3.5 tnum">{target.link_score ?? '—'}</td>
                      <td className="px-4 py-3.5 tnum font-semibold">{target.product_count} items</td>
                      <td className="px-4 py-3.5 tnum font-semibold text-slate-900">
                        {formatPrice(target.avg_price, target.currency)}
                      </td>
                      <td className="px-4 py-3.5 tnum text-xs text-slate-600">
                        {target.min_price != null && target.max_price != null
                          ? `${formatPrice(target.min_price, target.currency)} – ${formatPrice(target.max_price, target.currency)}`
                          : '—'}
                      </td>
                      <td className="px-4 py-3.5 tnum">
                        {target.in_stock_rate != null ? `${target.in_stock_rate}%` : '—'}
                      </td>
                    </tr>
                  )}

                  {/* Competitor Rows */}
                  {filteredCompetitors.map((comp) => (
                    <tr key={comp.brand_id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3.5">
                        <div className="font-semibold text-slate-900">{comp.brand_name}</div>
                        <div className="text-xs text-slate-400 font-mono mt-0.5">{comp.domain}</div>
                      </td>
                      <td className="px-4 py-3.5 font-semibold text-slate-800 tnum">
                        {comp.seo_total_score != null ? `${comp.seo_total_score}/100` : '—'}
                      </td>
                      <td className="px-4 py-3.5 tnum text-slate-600">{comp.technical_score ?? '—'}</td>
                      <td className="px-4 py-3.5 tnum text-slate-600">{comp.content_score ?? '—'}</td>
                      <td className="px-4 py-3.5 tnum text-slate-600">{comp.structured_data_score ?? '—'}</td>
                      <td className="px-4 py-3.5 tnum text-slate-600">{comp.link_score ?? '—'}</td>
                      <td className="px-4 py-3.5 tnum text-slate-700">{comp.product_count} items</td>
                      <td className="px-4 py-3.5 tnum text-slate-700 font-medium">
                        {formatPrice(comp.avg_price, comp.currency)}
                      </td>
                      <td className="px-4 py-3.5 tnum text-xs text-slate-500">
                        {comp.min_price != null && comp.max_price != null
                          ? `${formatPrice(comp.min_price, comp.currency)} – ${formatPrice(comp.max_price, comp.currency)}`
                          : '—'}
                      </td>
                      <td className="px-4 py-3.5 tnum text-slate-700">
                        {comp.in_stock_rate != null ? `${comp.in_stock_rate}%` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-3 bg-slate-50 border-t border-slate-200 text-xs text-slate-500 flex items-center gap-2">
              <Info size={14} className="text-slate-400 shrink-0" />
              <span>
                All pricing comparisons are normalized according to real-time currency conversions when computing the executive Price Index.
              </span>
            </div>
          </Card>
        </>
      )}

      {/* Link Competitor Modal */}
      <LinkCompetitorModal
        brandId={effectiveBrandId}
        isOpen={isLinkModalOpen}
        onClose={() => setIsLinkModalOpen(false)}
      />
    </div>
  );
};
