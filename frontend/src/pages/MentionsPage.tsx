import React, { useState, useMemo, useEffect } from 'react';
import { useAppStore } from '../stores/appStore';
import { useGetBrands } from '../api/queries/useBrands';
import {
  useGetMentions,
  useGetReputationAnalytics,
  useSeedMentions,
} from '../api/queries/useMentions';
import { AddMentionModal } from '../components/mentions/AddMentionModal';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Spinner } from '../components/ui/Spinner';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/feedback/EmptyState';
import { ErrorState } from '../components/feedback/ErrorState';
import {
  MessageSquare,
  Plus,
  TrendingUp,
  TrendingDown,
  ThumbsUp,
  AlertTriangle,
  ExternalLink,
  Search,
  Filter,
  RefreshCw,
  Tag,
  Share2,
  Sparkles,
  Info,
  CheckCircle2,
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

export const MentionsPage: React.FC = () => {
  const { data: brands = [], isLoading: brandsLoading } = useGetBrands();
  const { currentBrandId, setCurrentBrandId } = useAppStore();

  // Active brand resolution: store selection if valid, fallback to first active brand
  const effectiveBrandId =
    currentBrandId && brands.some((b) => b.id === currentBrandId)
      ? currentBrandId
      : brands[0]?.id || '';

  // Synchronize store if empty but brands exist
  useEffect(() => {
    if (!currentBrandId && brands.length > 0) {
      setCurrentBrandId(brands[0].id);
    }
  }, [currentBrandId, brands, setCurrentBrandId]);

  const [sourceFilter, setSourceFilter] = useState('all');
  const [labelFilter, setLabelFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [seedNotice, setSeedNotice] = useState<string | null>(null);

  // Queries
  const {
    data: mentionsData,
    isLoading: isMentionsLoading,
    isError: isMentionsError,
    refetch: refetchMentions,
  } = useGetMentions(effectiveBrandId, sourceFilter, labelFilter);

  const {
    data: analyticsData,
    isLoading: isAnalyticsLoading,
    isError: isAnalyticsError,
    refetch: refetchAnalytics,
  } = useGetReputationAnalytics(effectiveBrandId);

  const seedMutation = useSeedMentions(effectiveBrandId);

  const handleSeed = () => {
    if (!effectiveBrandId) return;
    setSeedNotice(null);
    seedMutation.mutate(undefined, {
      onSuccess: (data) => {
        setSeedNotice(`Successfully collected and analyzed ${data.count} social mentions!`);
        setTimeout(() => setSeedNotice(null), 5000);
      },
      onError: () => {
        setSeedNotice('Failed to scan mentions. Please try again.');
        setTimeout(() => setSeedNotice(null), 5000);
      },
    });
  };

  // Filter mentions by search query in memory
  const filteredMentions = useMemo(() => {
    if (!mentionsData?.items) return [];
    if (!searchQuery.trim()) return mentionsData.items;
    const q = searchQuery.toLowerCase();
    return mentionsData.items.filter(
      (m) =>
        m.content.toLowerCase().includes(q) ||
        m.author?.toLowerCase().includes(q) ||
        m.source.toLowerCase().includes(q)
    );
  }, [mentionsData?.items, searchQuery]);

  // Chart data for Sentiment Pie Chart
  const pieData = useMemo(() => {
    if (!analyticsData) return [];
    return [
      { name: 'Positive', value: analyticsData.positive_count, color: '#22c55e' },
      { name: 'Neutral', value: analyticsData.neutral_count, color: '#94a3b8' },
      { name: 'Negative', value: analyticsData.negative_count, color: '#ef4444' },
    ].filter((item) => item.value > 0);
  }, [analyticsData]);

  // Chart data for Sources Bar Chart
  const sourceBarData = useMemo(() => {
    if (!analyticsData?.sources_breakdown) return [];
    return analyticsData.sources_breakdown.map((s) => ({
      source: s.source.toUpperCase(),
      Positive: s.positive,
      Neutral: s.neutral,
      Negative: s.negative,
    }));
  }, [analyticsData]);

  if (!effectiveBrandId && !brandsLoading) {
    return (
      <div className="flex-1 flex flex-col justify-center items-center p-8">
        <EmptyState
          icon={<MessageSquare className="w-12 h-12 text-slate-500" />}
          title="No Brand Configured"
          description="Please add a brand first to inspect social mentions and sentiment analytics."
        />
      </div>
    );
  }

  if (isMentionsError || isAnalyticsError) {
    return (
      <div className="p-8">
        <ErrorState
          message="Could not load sentiment data. Ensure the backend service is reachable."
          onRetry={() => {
            refetchMentions();
            refetchAnalytics();
          }}
        />
      </div>
    );
  }

  const nss = analyticsData?.net_sentiment_score ?? 0;
  const nssStatus =
    nss > 20
      ? { label: 'Positive Reputation', variant: 'success' as const, icon: TrendingUp }
      : nss < -20
      ? { label: 'High Negative Risk', variant: 'critical' as const, icon: AlertTriangle }
      : { label: 'Neutral Brand Stance', variant: 'default' as const, icon: TrendingDown };

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <MessageSquare className="w-6 h-6 text-blue-400" />
            Social Reputation & Sentiment Analysis
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time multi-platform mention monitoring, Net Sentiment Score (NSS), and consumer perception tracking.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Brand Selector Dropdown */}
          <div className="flex items-center gap-2">
            <select
              id="brand-select"
              value={effectiveBrandId}
              onChange={(e) => setCurrentBrandId(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 outline-none focus:border-blue-500 min-w-[170px]"
            >
              {brands.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name} ({b.domain})
                </option>
              ))}
            </select>
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={handleSeed}
            disabled={seedMutation.isPending || !effectiveBrandId}
          >
            {seedMutation.isPending ? (
              <Spinner size="sm" className="mr-1.5" />
            ) : (
              <Sparkles className="w-3.5 h-3.5 mr-1.5 text-amber-400" />
            )}
            Scan Social Mentions
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              refetchMentions();
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
            Ingest Mention
          </Button>
        </div>
      </div>

      {/* Action Notice Alert */}
      {seedNotice && (
        <div className="p-3 bg-emerald-950/40 border border-emerald-800 rounded-lg text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{seedNotice}</span>
          </div>
          <button
            onClick={() => setSeedNotice(null)}
            className="text-slate-400 hover:text-slate-200 text-xs ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Diagnostic & Formula Insights Banner */}
      <Card className="bg-gradient-to-r from-slate-900 via-slate-900 to-blue-950/40 border-slate-800 p-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 shrink-0 mt-0.5">
            <Info className="w-4 h-4" />
          </div>
          <div className="space-y-1 text-xs text-slate-300">
            <span className="font-semibold text-slate-100 text-sm block">
              How Social Reputation & Net Sentiment Score (NSS) Works
            </span>
            <p className="text-slate-400 leading-relaxed">
              BrandPulse continuously evaluates brand perception across Twitter/X, Reddit, G2, Trustpilot, and News.
              Mentions are processed through algorithmic NLP models with negation context windows and emoji decoding.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
              <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800">
                <span className="text-blue-300 font-medium block mb-0.5">1. Net Sentiment Score (NSS)</span>
                <span className="text-[11px] text-slate-400 block">
                  Formula: <code className="text-slate-200 bg-slate-900 px-1 py-0.5 rounded">((Pos - Neg) / Total) × 100</code>. Scores range from -100 to +100. Over +20 denotes strong brand love.
                </span>
              </div>
              <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800">
                <span className="text-emerald-300 font-medium block mb-0.5">2. Multi-Channel Monitoring</span>
                <span className="text-[11px] text-slate-400 block">
                  Aggregates social feedback, app reviews, customer support tickets, and news coverage to detect viral trends early.
                </span>
              </div>
              <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800">
                <span className="text-purple-300 font-medium block mb-0.5">3. Perception Themes</span>
                <span className="text-[11px] text-slate-400 block">
                  Extracts top consumer discussion topics (e.g. pricing, reliability, UX) paired with granular sentiment valence.
                </span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Net Sentiment Score */}
        <Card className="p-4 bg-slate-900 border-slate-800">
          <div className="flex items-center justify-between text-xs font-semibold uppercase text-slate-400">
            <span>Net Sentiment Score</span>
            <nssStatus.icon className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            {isAnalyticsLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <span className="text-3xl font-extrabold text-slate-100 tabular-nums">
                  {nss > 0 ? `+${nss}` : nss}
                </span>
                <span className="text-xs text-slate-500">/ 100</span>
              </>
            )}
          </div>
          <div className="mt-2">
            <Badge variant={nssStatus.variant}>
              {nssStatus.label}
            </Badge>
          </div>
        </Card>

        {/* Total Mentions */}
        <Card className="p-4 bg-slate-900 border-slate-800">
          <div className="flex items-center justify-between text-xs font-semibold uppercase text-slate-400">
            <span>Total Mentions</span>
            <Share2 className="w-4 h-4 text-slate-400" />
          </div>
          <div className="mt-2">
            {isAnalyticsLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <span className="text-3xl font-extrabold text-slate-100 tabular-nums">
                {analyticsData?.total_mentions ?? 0}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Across {analyticsData?.sources_breakdown.length ?? 0} platforms
          </p>
        </Card>

        {/* Positive Sentiment % */}
        <Card className="p-4 bg-slate-900 border-slate-800">
          <div className="flex items-center justify-between text-xs font-semibold uppercase text-slate-400">
            <span>Positive Ratio</span>
            <ThumbsUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2">
            {isAnalyticsLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <span className="text-3xl font-extrabold text-emerald-400 tabular-nums">
                {analyticsData?.positive_pct ?? 0}%
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-2">
            {analyticsData?.positive_count ?? 0} positive mentions
          </p>
        </Card>

        {/* Negative Sentiment % */}
        <Card className="p-4 bg-slate-900 border-slate-800">
          <div className="flex items-center justify-between text-xs font-semibold uppercase text-slate-400">
            <span>Negative Ratio</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-2">
            {isAnalyticsLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <span className="text-3xl font-extrabold text-rose-400 tabular-nums">
                {analyticsData?.negative_pct ?? 0}%
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-2">
            {analyticsData?.negative_count ?? 0} negative complaints
          </p>
        </Card>
      </div>

      {/* Visual Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sentiment Distribution Pie Chart */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <h3 className="text-sm font-semibold text-slate-200">Sentiment Distribution</h3>
          </CardHeader>
          <CardBody className="h-64 flex items-center justify-center">
            {isAnalyticsLoading ? (
              <Skeleton className="h-full w-full" />
            ) : pieData.length === 0 ? (
              <div className="text-xs text-slate-500">No sentiment data available</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((entry, idx) => (
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

        {/* Source Breakdown Bar Chart */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <h3 className="text-sm font-semibold text-slate-200">Volume by Source Platform</h3>
          </CardHeader>
          <CardBody className="h-64">
            {isAnalyticsLoading ? (
              <Skeleton className="h-full w-full" />
            ) : sourceBarData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                No platform data available
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sourceBarData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="source" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Bar dataKey="Positive" fill="#22c55e" stackId="a" />
                  <Bar dataKey="Neutral" fill="#94a3b8" stackId="a" />
                  <Bar dataKey="Negative" fill="#ef4444" stackId="a" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardBody>
        </Card>

        {/* Perception Topics / Keyword Cloud */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-1.5">
              <Tag className="w-4 h-4 text-blue-400" />
              Perception Themes & Topics
            </h3>
          </CardHeader>
          <CardBody>
            {isAnalyticsLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-6 w-full" />
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-6 w-5/6" />
              </div>
            ) : !analyticsData?.top_topics || analyticsData.top_topics.length === 0 ? (
              <div className="h-48 flex items-center justify-center text-xs text-slate-500">
                No perception themes extracted yet
              </div>
            ) : (
              <div className="flex flex-wrap gap-2 pt-1">
                {analyticsData.top_topics.map((t, i) => {
                  const badgeVariant =
                    t.sentiment_label === 'positive'
                      ? 'success'
                      : t.sentiment_label === 'negative'
                      ? 'critical'
                      : 'default';

                  return (
                    <div
                      key={i}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs text-slate-200"
                    >
                      <span className="capitalize font-medium">{t.topic}</span>
                      <span className="text-[10px] text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded-full tabular-nums">
                        {t.frequency}
                      </span>
                      <Badge variant={badgeVariant}>
                        {t.sentiment_label}
                      </Badge>
                    </div>
                  );
                })}
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Toolbar: Search and Filter Tabs */}
      <Card className="bg-slate-900 border-slate-800 p-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search mentions by quote, author, or platform..."
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

            {/* Source dropdown */}
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Platforms</option>
              <option value="twitter">Twitter / X</option>
              <option value="reddit">Reddit</option>
              <option value="g2">G2 Reviews</option>
              <option value="trustpilot">Trustpilot</option>
              <option value="news">News</option>
              <option value="blog">Blog</option>
              <option value="web">Web Forum</option>
            </select>

            {/* Sentiment label tabs */}
            <div className="flex items-center rounded-lg bg-slate-950 p-0.5 border border-slate-800">
              {(['all', 'positive', 'neutral', 'negative'] as const).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setLabelFilter(tab)}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors capitalize ${
                    labelFilter === tab
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

      {/* Mentions Feed */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-400 px-1">
          <span>Displaying {filteredMentions.length} mentions</span>
        </div>

        {isMentionsLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((n) => (
              <Card key={n} className="p-4 bg-slate-900 border-slate-800">
                <Skeleton className="h-4 w-1/4 mb-3" />
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-3/4" />
              </Card>
            ))}
          </div>
        ) : filteredMentions.length === 0 ? (
          <EmptyState
            icon={<MessageSquare className="w-8 h-8 text-slate-500" />}
            title="No Mentions Matching Filter"
            description="Try adjusting your platform or sentiment filters, or ingest new mentions to test the analyzer."
            actionLabel="Ingest New Mention"
            onAction={() => setIsAddModalOpen(true)}
          />
        ) : (
          filteredMentions.map((mention) => {
            const label = mention.sentiment?.label ?? 'neutral';
            const badgeVariant =
              label === 'positive'
                ? 'success'
                : label === 'negative'
                ? 'critical'
                : 'default';

            return (
              <Card
                key={mention.id}
                className="p-4 bg-slate-900 border-slate-800 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-sm text-slate-200">
                        {mention.author || 'Anonymous User'}
                      </span>
                      <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 uppercase font-mono tracking-wider">
                        {mention.source}
                      </span>
                      {mention.created_at && (
                        <span className="text-xs text-slate-500">
                          {new Date(mention.created_at).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                          })}
                        </span>
                      )}
                    </div>

                    <p className="text-sm text-slate-300 leading-relaxed">
                      "{mention.content}"
                    </p>
                  </div>

                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <Badge variant={badgeVariant}>
                      {label.toUpperCase()}
                    </Badge>
                    {mention.sentiment && (
                      <div className="text-[10px] text-slate-500 font-mono">
                        +{((mention.sentiment.positive_score ?? 0) * 100).toFixed(0)}% / -
                        {((mention.sentiment.negative_score ?? 0) * 100).toFixed(0)}%
                      </div>
                    )}
                    {mention.source_url && (
                      <a
                        href={mention.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-400 hover:text-blue-300 inline-flex items-center gap-1 mt-1"
                      >
                        Source
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>
              </Card>
            );
          })
        )}
      </div>

      {/* Add Mention Modal */}
      <AddMentionModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        brandId={effectiveBrandId}
      />
    </div>
  );
};
