import React, { useState, useMemo } from 'react';
import { useAppStore } from '../stores/appStore';
import { useGetAds, useGetAdAnalytics } from '../api/queries/useAds';
import { AddAdModal } from '../components/ads/AddAdModal';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/feedback/EmptyState';
import { ErrorState } from '../components/feedback/ErrorState';
import {
  Megaphone,
  Plus,
  TrendingUp,
  DollarSign,
  Layers,
  Award,
  ExternalLink,
  Search,
  Filter,
  RefreshCw,
  Sparkles,
  Calendar,
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';

const PLATFORM_COLORS: Record<string, string> = {
  google: '#3b82f6',
  meta: '#06b6d4',
  linkedin: '#0284c7',
  twitter: '#6366f1',
  tiktok: '#ec4899',
  unknown: '#94a3b8',
};

export const AdsPage: React.FC = () => {
  const { currentBrandId } = useAppStore();
  const [platformFilter, setPlatformFilter] = useState('all');
  const [formatFilter, setFormatFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // Queries
  const {
    data: adsData,
    isLoading: isAdsLoading,
    isError: isAdsError,
    refetch: refetchAds,
  } = useGetAds(currentBrandId, platformFilter, formatFilter, searchQuery);

  const {
    data: analyticsData,
    isLoading: isAnalyticsLoading,
    isError: isAnalyticsError,
    refetch: refetchAnalytics,
  } = useGetAdAnalytics(currentBrandId);

  // Filtered ads in memory for quick text search
  const filteredAds = useMemo(() => {
    if (!adsData?.items) return [];
    if (!searchQuery.trim()) return adsData.items;
    const q = searchQuery.toLowerCase();
    return adsData.items.filter(
      (ad) =>
        ad.ad_text?.toLowerCase().includes(q) ||
        ad.headline?.toLowerCase().includes(q) ||
        ad.cta?.toLowerCase().includes(q) ||
        ad.platform.toLowerCase().includes(q)
    );
  }, [adsData?.items, searchQuery]);

  // Chart data for Platform Donut Chart
  const platformPieData = useMemo(() => {
    if (!analyticsData?.platform_distribution) return [];
    return analyticsData.platform_distribution.map((p) => ({
      name: p.platform.toUpperCase(),
      value: p.count,
      color: PLATFORM_COLORS[p.platform.toLowerCase()] || '#94a3b8',
    }));
  }, [analyticsData]);

  // Chart data for Format Bar Chart
  const formatBarData = useMemo(() => {
    if (!analyticsData?.format_distribution) return [];
    return analyticsData.format_distribution.map((f) => ({
      format: f.format.replace('_', ' ').toUpperCase(),
      count: f.count,
    }));
  }, [analyticsData]);

  if (!currentBrandId) {
    return (
      <div className="flex-1 flex flex-col justify-center items-center p-8">
        <EmptyState
          icon={<Megaphone className="w-12 h-12 text-slate-500" />}
          title="No Brand Selected"
          description="Please select a brand from the top navigation bar to inspect competitor paid advertising intelligence."
        />
      </div>
    );
  }

  if (isAdsError || isAnalyticsError) {
    return (
      <div className="p-8">
        <ErrorState
          message="Could not load advertising intelligence data. Ensure the backend service is reachable."
          onRetry={() => {
            refetchAds();
            refetchAnalytics();
          }}
        />
      </div>
    );
  }

  const topPlatform =
    analyticsData?.platform_distribution && analyticsData.platform_distribution.length > 0
      ? analyticsData.platform_distribution[0].platform.toUpperCase()
      : 'N/A';

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Megaphone className="w-6 h-6 text-blue-400" />
            Ad Intelligence & Paid Media Tracking
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Competitor paid campaign analysis, creative hooks, longevity detection, and estimated spend tiers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              refetchAds();
              refetchAnalytics();
            }}
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsAddModalOpen(true)}
          >
            <Plus className="w-3.5 h-3.5 mr-1.5" />
            Ingest Ad Creative
          </Button>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Ads */}
        <Card className="p-4 bg-slate-900 border-slate-800">
          <div className="flex items-center justify-between text-xs font-semibold uppercase text-slate-400">
            <span>Total Active Ads</span>
            <Layers className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-2">
            {isAnalyticsLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <span className="text-3xl font-extrabold text-slate-100 tabular-nums">
                {analyticsData?.total_ads ?? 0}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Tracked across major ad networks
          </p>
        </Card>

        {/* Estimated Monthly Spend */}
        <Card className="p-4 bg-slate-900 border-slate-800">
          <div className="flex items-center justify-between text-xs font-semibold uppercase text-slate-400">
            <span>Est. Monthly Spend</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2">
            {isAnalyticsLoading ? (
              <Skeleton className="h-8 w-28" />
            ) : (
              <span className="text-2xl font-extrabold text-emerald-400 tabular-nums">
                {analyticsData?.estimated_monthly_spend_range ?? '$0'}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Heuristic longevity-based estimation
          </p>
        </Card>

        {/* Evergreen Winners */}
        <Card className="p-4 bg-slate-900 border-slate-800">
          <div className="flex items-center justify-between text-xs font-semibold uppercase text-slate-400">
            <span>Evergreen Winners</span>
            <Award className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            {isAnalyticsLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <>
                <span className="text-3xl font-extrabold text-amber-400 tabular-nums">
                  {analyticsData?.evergreen_count ?? 0}
                </span>
                <span className="text-xs text-slate-500">ads active &gt; 45d</span>
              </>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-2">
            High-converting core campaigns
          </p>
        </Card>

        {/* Top Platform */}
        <Card className="p-4 bg-slate-900 border-slate-800">
          <div className="flex items-center justify-between text-xs font-semibold uppercase text-slate-400">
            <span>Primary Ad Network</span>
            <TrendingUp className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-2">
            {isAnalyticsLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <span className="text-2xl font-extrabold text-slate-100">
                {topPlatform}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Largest share of competitor impressions
          </p>
        </Card>
      </div>

      {/* Visual Analytics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Platform Share Donut Chart */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <h3 className="text-sm font-semibold text-slate-200">Advertising Network Share</h3>
          </CardHeader>
          <CardBody className="h-64 flex items-center justify-center">
            {isAnalyticsLoading ? (
              <Skeleton className="h-full w-full" />
            ) : platformPieData.length === 0 ? (
              <div className="text-xs text-slate-500">No ad network data recorded</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={platformPieData}
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {platformPieData.map((entry, idx) => (
                      <Cell key={`cell-${idx}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardBody>
        </Card>

        {/* Ad Format Bar Chart */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <h3 className="text-sm font-semibold text-slate-200">Creative Formats</h3>
          </CardHeader>
          <CardBody className="h-64">
            {isAnalyticsLoading ? (
              <Skeleton className="h-full w-full" />
            ) : formatBarData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                No creative formats recorded
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={formatBarData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="format" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardBody>
        </Card>

        {/* Top CTAs & Marketing Hooks */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-amber-400" />
              Top Call-to-Actions (CTAs)
            </h3>
          </CardHeader>
          <CardBody>
            {isAnalyticsLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-6 w-full" />
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-6 w-5/6" />
              </div>
            ) : !analyticsData?.top_ctas || analyticsData.top_ctas.length === 0 ? (
              <div className="h-48 flex items-center justify-center text-xs text-slate-500">
                No CTAs extracted yet
              </div>
            ) : (
              <div className="space-y-2.5 pt-1">
                {analyticsData.top_ctas.map((ctaItem, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-2 rounded bg-slate-800/60 border border-slate-700/60 text-xs text-slate-200"
                  >
                    <span className="font-semibold text-blue-400">"{ctaItem.name}"</span>
                    <span className="text-[10px] text-slate-400 bg-slate-900 px-2 py-0.5 rounded-full font-mono">
                      {ctaItem.count} ads
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Toolbar */}
      <Card className="bg-slate-900 border-slate-800 p-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search by headline, copy, or CTA..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1.5 text-xs text-slate-400 mr-2">
              <Filter className="w-3.5 h-3.5" />
              <span>Filters:</span>
            </div>

            {/* Platform Dropdown */}
            <select
              value={platformFilter}
              onChange={(e) => setPlatformFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Networks</option>
              <option value="google">Google Ads</option>
              <option value="meta">Meta</option>
              <option value="linkedin">LinkedIn</option>
              <option value="twitter">Twitter</option>
              <option value="tiktok">TikTok</option>
            </select>

            {/* Format Tabs */}
            <div className="flex items-center rounded-lg bg-slate-950 p-0.5 border border-slate-800">
              {(['all', 'search', 'display', 'video'] as const).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setFormatFilter(tab)}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors capitalize ${
                    formatFilter === tab
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Ad Creatives Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-400 px-1">
          <span>Displaying {filteredAds.length} ad creatives</span>
        </div>

        {isAdsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((n) => (
              <Card key={n} className="p-4 bg-slate-900 border-slate-800">
                <Skeleton className="h-4 w-1/3 mb-3" />
                <Skeleton className="h-5 w-3/4 mb-2" />
                <Skeleton className="h-4 w-full mb-3" />
                <Skeleton className="h-8 w-1/3" />
              </Card>
            ))}
          </div>
        ) : filteredAds.length === 0 ? (
          <EmptyState
            icon={<Megaphone className="w-8 h-8 text-slate-500" />}
            title="No Ads Matching Filter"
            description="Adjust your platform or format filters, or ingest new competitor creatives."
            actionLabel="Ingest New Ad"
            onAction={() => setIsAddModalOpen(true)}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredAds.map((ad) => {
              const isEvergreen = ad.is_evergreen ?? false;
              const longevityDays = ad.longevity_days ?? 1;

              return (
                <Card
                  key={ad.id}
                  className="p-5 bg-slate-900 border-slate-800 hover:border-slate-700 transition-colors flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    {/* Header Badges */}
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[11px] px-2 py-0.5 rounded bg-blue-950 border border-blue-800 text-blue-300 uppercase font-mono font-semibold">
                          {ad.platform}
                        </span>
                        <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 uppercase font-mono">
                          {ad.ad_format || 'search'}
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5">
                        {isEvergreen ? (
                          <Badge variant="success">
                            Evergreen ({longevityDays}d)
                          </Badge>
                        ) : (
                          <Badge variant="default">
                            {longevityDays}d active
                          </Badge>
                        )}
                        <span className="text-[10px] text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                          {ad.spend_tier || '$100 - $1,000'}
                        </span>
                      </div>
                    </div>

                    {/* Headline */}
                    {ad.headline && (
                      <h4 className="text-base font-bold text-slate-100 tracking-tight">
                        {ad.headline}
                      </h4>
                    )}

                    {/* Ad Copy */}
                    <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
                      {ad.ad_text}
                    </p>

                    {/* CTA Button Preview */}
                    {ad.cta && (
                      <div className="pt-1">
                        <button
                          type="button"
                          disabled
                          className="px-3 py-1.5 rounded-md bg-blue-600/90 text-white text-xs font-semibold shadow-sm cursor-default"
                        >
                          {ad.cta}
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Footer Meta */}
                  <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>
                        {ad.first_seen ? `First seen: ${ad.first_seen}` : 'Recently observed'}
                      </span>
                    </div>

                    {ad.target_url && (
                      <a
                        href={ad.target_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 inline-flex items-center gap-1"
                      >
                        Landing Page
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Add Ad Modal */}
      <AddAdModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        brandId={currentBrandId}
      />
    </div>
  );
};
