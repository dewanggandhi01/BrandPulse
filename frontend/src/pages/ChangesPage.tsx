import React, { useState } from 'react';
import {
  Activity,
  GitCompare,
  Tag,
  Layout,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  Eye,
  Calendar,
  RefreshCw,
  Play,
  CheckCircle2,
} from 'lucide-react';
import { useGetBrands } from '@/api/queries/useBrands';
import {
  useGetChanges,
  useGetChangeAnalytics,
  useScanBrandChanges,
} from '@/api/queries/useChanges';
import { useAppStore } from '@/stores/appStore';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/feedback/EmptyState';
import { VisualDiffModal } from '@/components/changes/VisualDiffModal';
import { ScrapeJobModal } from '@/components/crawling/ScrapeJobModal';

export const ChangesPage: React.FC = () => {
  const { data: brands = [], isLoading: brandsLoading } = useGetBrands();
  const { currentBrandId, setCurrentBrandId } = useAppStore();

  const effectiveBrandId =
    currentBrandId && brands.some((b) => b.id === currentBrandId)
      ? currentBrandId
      : brands[0]?.id || '';

  const activeBrand = brands.find((b) => b.id === effectiveBrandId);

  // Filter & pagination
  const [changeTypeFilter, setChangeTypeFilter] = useState<string>('');
  const [page, setPage] = useState(1);

  // Modals & notices
  const [inspectChangeId, setInspectChangeId] = useState<string | null>(null);
  const [isCrawlModalOpen, setIsCrawlModalOpen] = useState(false);
  const [scanNotice, setScanNotice] = useState<string | null>(null);

  // Queries & Mutations
  const {
    data: changesData,
    isLoading: changesLoading,
    error: changesError,
    refetch: refetchChanges,
  } = useGetChanges(effectiveBrandId, {
    page,
    size: 15,
    change_type: changeTypeFilter || undefined,
  });

  const { data: analytics, refetch: refetchAnalytics } = useGetChangeAnalytics(effectiveBrandId);
  const scanMutation = useScanBrandChanges();

  const changes = changesData?.items || [];
  const totalPages = changesData?.pages || 1;

  const handleBrandChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setCurrentBrandId(e.target.value);
    setPage(1);
    setScanNotice(null);
  };

  const handleScanChanges = () => {
    if (!effectiveBrandId) return;
    setScanNotice(null);
    scanMutation.mutate(effectiveBrandId, {
      onSuccess: (res: any) => {
        setScanNotice(res?.message || 'Snapshot scan complete!');
        refetchChanges();
        refetchAnalytics();
        setTimeout(() => setScanNotice(null), 6000);
      },
      onError: (err: any) => {
        setScanNotice(err?.response?.data?.detail || 'Failed to scan snapshots.');
        setTimeout(() => setScanNotice(null), 6000);
      },
    });
  };

  const getBadgeVariant = (type: string): 'default' | 'success' | 'warning' | 'critical' | 'info' => {
    switch (type) {
      case 'pricing_change':
      case 'price_update':
      case 'stock_status_change':
        return 'warning';
      case 'messaging_pivot':
        return 'info';
      case 'layout_overhaul':
        return 'critical';
      case 'seo_change':
        return 'success';
      default:
        return 'default';
    }
  };

  const formatChangeTypeName = (type: string): string => {
    switch (type) {
      case 'pricing_change':
      case 'price_update':
        return 'Pricing Shift';
      case 'stock_status_change':
        return 'Stock Change';
      case 'messaging_pivot':
        return 'Messaging Pivot';
      case 'layout_overhaul':
        return 'Layout Redesign';
      case 'seo_change':
        return 'SEO Revision';
      case 'minor_copy':
        return 'Minor Copy';
      default:
        return type.replace('_', ' ').toUpperCase();
    }
  };

  return (
    <div className="space-y-6 flex flex-col min-h-full pb-10">
      {/* Top Header & Brand Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Activity className="text-brand-600" size={28} />
            Website Change Detection & Diffing
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Automated visual and semantic diffing detecting competitor messaging pivots, price adjustments, and layout shifts.
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
            onClick={handleScanChanges}
            disabled={!effectiveBrandId || scanMutation.isPending}
            className="flex items-center gap-1.5 text-xs"
            title="Scan consecutive snapshots for content and layout differences"
          >
            <RefreshCw size={15} className={scanMutation.isPending ? 'animate-spin' : ''} />
            Scan for Changes
          </Button>

          <Button
            variant="primary"
            onClick={() => setIsCrawlModalOpen(true)}
            disabled={!effectiveBrandId}
            className="flex items-center gap-1.5 text-xs"
            title="Trigger a new crawl to capture a fresh snapshot"
          >
            <Play size={14} />
            Crawl Website
          </Button>
        </div>
      </div>

      {scanNotice && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
          <span>{scanNotice}</span>
        </div>
      )}

      {brandsLoading ? (
        <div className="py-20 flex justify-center">
          <Spinner size="lg" />
        </div>
      ) : brands.length === 0 ? (
        <EmptyState
          icon={<Activity size={48} />}
          title="No Monitored Brands"
          description="Create your first brand in the Brands section to begin detecting changes."
        />
      ) : (
        <>
          {/* KPI Analytics Strip */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-4 bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Changes</span>
                <span className="p-2 rounded-lg bg-blue-50 text-blue-600">
                  <Activity size={18} />
                </span>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 tnum">
                  {analytics?.total_changes ?? 0}
                </span>
                <span className="text-xs text-slate-500">events detected</span>
              </div>
            </Card>

            <Card className="p-4 bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pricing Shifts</span>
                <span className="p-2 rounded-lg bg-amber-50 text-amber-600">
                  <Tag size={18} />
                </span>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-amber-700 tnum">
                  {analytics?.pricing_changes_count ?? 0}
                </span>
                <span className="text-xs text-slate-500">pricing/catalog shifts</span>
              </div>
            </Card>

            <Card className="p-4 bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Messaging Pivots</span>
                <span className="p-2 rounded-lg bg-indigo-50 text-indigo-600">
                  <MessageSquare size={18} />
                </span>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-indigo-700 tnum">
                  {analytics?.messaging_pivots_count ?? 0}
                </span>
                <span className="text-xs text-slate-500">headline/title updates</span>
              </div>
            </Card>

            <Card className="p-4 bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Layout Overhauls</span>
                <span className="p-2 rounded-lg bg-rose-50 text-rose-600">
                  <Layout size={18} />
                </span>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-rose-700 tnum">
                  {analytics?.layout_overhauls_count ?? 0}
                </span>
                <span className="text-xs text-slate-500">major redesigns</span>
              </div>
            </Card>
          </div>

          {/* Filter Tabs */}
          <div className="flex items-center justify-between gap-3 bg-white p-2.5 rounded-lg border border-slate-200 shadow-sm overflow-x-auto">
            <div className="flex bg-slate-100 p-0.5 rounded-lg text-xs font-medium text-slate-600 shrink-0">
              <button
                onClick={() => {
                  setChangeTypeFilter('');
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-md transition-colors ${
                  changeTypeFilter === '' ? 'bg-white shadow text-slate-900 font-semibold' : 'hover:text-slate-900'
                }`}
              >
                All Events ({analytics?.total_changes ?? 0})
              </button>
              <button
                onClick={() => {
                  setChangeTypeFilter('pricing_change');
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-md transition-colors ${
                  changeTypeFilter === 'pricing_change' ? 'bg-white shadow text-amber-800 font-semibold' : 'hover:text-slate-900'
                }`}
              >
                Pricing Shifts
              </button>
              <button
                onClick={() => {
                  setChangeTypeFilter('messaging_pivot');
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-md transition-colors ${
                  changeTypeFilter === 'messaging_pivot' ? 'bg-white shadow text-blue-800 font-semibold' : 'hover:text-slate-900'
                }`}
              >
                Messaging Pivots
              </button>
              <button
                onClick={() => {
                  setChangeTypeFilter('layout_overhaul');
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-md transition-colors ${
                  changeTypeFilter === 'layout_overhaul' ? 'bg-white shadow text-rose-800 font-semibold' : 'hover:text-slate-900'
                }`}
              >
                Layout Overhauls
              </button>
              <button
                onClick={() => {
                  setChangeTypeFilter('seo_change');
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-md transition-colors ${
                  changeTypeFilter === 'seo_change' ? 'bg-white shadow text-emerald-800 font-semibold' : 'hover:text-slate-900'
                }`}
              >
                SEO Changes
              </button>
            </div>

            <div className="text-xs text-slate-400 font-medium pr-2 shrink-0">
              Showing {changes.length} events
            </div>
          </div>

          {/* Change Events Timeline List */}
          {changesLoading ? (
            <div className="py-24 flex justify-center">
              <Spinner size="lg" />
            </div>
          ) : changesError ? (
            <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              Failed to load change log for this brand.
            </div>
          ) : changes.length === 0 ? (
            <div className="space-y-4">
              <EmptyState
                icon={<GitCompare size={48} />}
                title="No Changes Detected Yet"
                description="Multiple crawl snapshots on the same domain are required to evaluate visual and semantic shifts. Scan existing snapshots or trigger a new crawl."
                actionLabel="Scan Existing Snapshots"
                onAction={handleScanChanges}
              />
              <div className="flex justify-center">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsCrawlModalOpen(true)}
                  className="flex items-center gap-1.5 text-xs text-slate-600"
                >
                  <Play size={13} /> Trigger New Crawl to Capture Future Shifts
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {changes.map((event) => {
                const simPct =
                  event.similarity_ratio != null ? Math.round(event.similarity_ratio * 100) : 100;
                return (
                  <Card
                    key={event.id}
                    className="p-4 bg-white border border-slate-200 shadow-sm hover:border-slate-300 transition-colors"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="space-y-1.5 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge variant={getBadgeVariant(event.change_type)}>
                            {formatChangeTypeName(event.change_type)}
                          </Badge>
                          <span className="text-xs text-slate-400 flex items-center gap-1">
                            <Calendar size={13} />
                            {new Date(event.created_at).toLocaleString()}
                          </span>
                          <span
                            className={`text-xs font-mono px-2 py-0.5 rounded font-medium ${
                              simPct >= 95
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : simPct >= 70
                                ? 'bg-amber-50 text-amber-700 border border-amber-200'
                                : 'bg-rose-50 text-rose-700 border border-rose-200'
                            }`}
                          >
                            {simPct}% content similarity
                          </span>
                        </div>

                        <h3 className="text-base font-semibold text-slate-900 leading-snug">
                          {event.ai_summary || 'Snapshot differences detected across page content.'}
                        </h3>

                        <div className="flex items-center gap-3 text-xs text-slate-500">
                          {event.additions_count != null && (
                            <span className="text-emerald-700 font-medium">
                              +{event.additions_count} additions
                            </span>
                          )}
                          {event.deletions_count != null && (
                            <span className="text-red-700 font-medium">
                              -{event.deletions_count} deletions
                            </span>
                          )}
                          {event.total_changes != null && (
                            <span className="text-slate-400">
                              ({event.total_changes} sections affected)
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="shrink-0 flex items-center gap-3">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setInspectChangeId(event.id)}
                          className="flex items-center gap-1.5 text-xs"
                        >
                          <Eye size={14} className="text-slate-500" />
                          Inspect Diff
                        </Button>
                      </div>
                    </div>
                  </Card>
                );
              })}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 bg-white border border-slate-200 rounded-lg text-xs text-slate-500">
                  <div>
                    Page <span className="font-semibold text-slate-800">{page}</span> of{' '}
                    <span className="font-semibold text-slate-800">{totalPages}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page <= 1}
                    >
                      <ChevronLeft size={14} /> Previous
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page >= totalPages}
                    >
                      Next <ChevronRight size={14} />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Visual Diff Modal */}
      <VisualDiffModal
        changeId={inspectChangeId}
        isOpen={!!inspectChangeId}
        onClose={() => setInspectChangeId(null)}
      />

      {/* Trigger Crawl Modal */}
      <ScrapeJobModal
        isOpen={isCrawlModalOpen}
        onClose={() => {
          setIsCrawlModalOpen(false);
          refetchChanges();
          refetchAnalytics();
        }}
        brandId={effectiveBrandId}
        defaultDomain={activeBrand?.domain || ''}
      />
    </div>
  );
};
