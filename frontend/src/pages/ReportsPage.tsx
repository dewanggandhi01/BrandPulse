import React, { useState } from 'react';
import { useAppStore } from '../stores/appStore';
import { useGetBrand } from '../api/queries/useBrands';
import {
  useGetReports,
  useGenerateReport,
  useDeleteReport,
} from '../api/queries/useReports';
import { ReportViewerModal } from '../components/reports/ReportViewerModal';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/feedback/EmptyState';
import { ErrorState } from '../components/feedback/ErrorState';
import type { Report } from '../types';
import {
  FileText,
  Sparkles,
  RefreshCw,
  Trash2,
  Eye,
  Activity,
  ShieldCheck,
  TrendingUp,
  Calendar,
  Building2,
} from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const { currentBrandId } = useAppStore();
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const [page] = useState(1);

  const { data: currentBrand } = useGetBrand(currentBrandId || '');

  // Queries
  const {
    data: reportsData,
    isLoading,
    isError,
    refetch,
  } = useGetReports(currentBrandId, page, 20);

  // Mutations
  const generateMutation = useGenerateReport(currentBrandId);
  const deleteMutation = useDeleteReport(currentBrandId);

  const reports = reportsData?.items || [];
  const latestReport = reports[0] || null;

  // KPI calculations
  const totalReports = reportsData?.total || 0;
  const latestHealthScore = latestReport?.content?.health_score ?? null;
  const latestRiskLevel = latestReport?.content?.risk_level ?? 'None';
  const totalRecommendations =
    latestReport?.content?.recommendations?.length ?? 0;

  const handleGenerate = async () => {
    if (!currentBrandId) return;
    try {
      const res = await generateMutation.mutateAsync({
        report_type: 'executive_brief',
      });
      if (res?.report) {
        setSelectedReport(res.report);
        setIsViewerOpen(true);
      }
    } catch (err) {
      console.error('Failed to generate report', err);
    }
  };

  const handleDelete = async (reportId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this executive brief?')) {
      try {
        await deleteMutation.mutateAsync(reportId);
      } catch (err) {
        console.error('Failed to delete report', err);
      }
    }
  };

  const handleOpenReport = (rep: Report) => {
    setSelectedReport(rep);
    setIsViewerOpen(true);
  };

  const getHealthBadge = (score: number) => {
    if (score >= 75) return <Badge variant="success">{score}/100 Health</Badge>;
    if (score >= 50) return <Badge variant="warning">{score}/100 Health</Badge>;
    return <Badge variant="critical">{score}/100 Health</Badge>;
  };

  const getRiskBadge = (risk: string) => {
    if (risk.toLowerCase().includes('low'))
      return <Badge variant="success">Low Risk</Badge>;
    if (risk.toLowerCase().includes('moderate'))
      return <Badge variant="warning">Moderate Attention</Badge>;
    if (risk.toLowerCase().includes('high'))
      return <Badge variant="critical">High Threat</Badge>;
    return <Badge variant="default">{risk}</Badge>;
  };

  if (!currentBrandId) {
    return (
      <div className="space-y-6 h-full flex flex-col">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          Executive Intelligence Reports
        </h1>
        <div className="flex-1 flex items-center justify-center">
          <EmptyState
            icon={<Building2 size={48} />}
            title="No Brand Selected"
            description="Please select a brand from the top navigation to view or generate executive reports."
          />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Executive Intelligence Reports
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Holistic C-suite briefs synthesizing SEO health, pricing, web agility, sentiment, and ad intelligence.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => refetch()}
            className="flex items-center gap-1.5"
            disabled={isLoading}
          >
            <RefreshCw size={15} className={isLoading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleGenerate}
            disabled={generateMutation.isPending}
            className="flex items-center gap-1.5 shadow-sm"
          >
            <Sparkles size={15} />
            <span>
              {generateMutation.isPending
                ? 'Synthesizing Brief...'
                : 'Generate Executive Brief'}
            </span>
          </Button>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border border-slate-200">
          <CardBody className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-blue-50 text-blue-600 rounded-lg">
              <FileText size={22} />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Total Briefs
              </p>
              <p className="text-xl font-bold text-slate-900 font-mono">
                {isLoading ? '...' : totalReports}
              </p>
            </div>
          </CardBody>
        </Card>

        <Card className="border border-slate-200">
          <CardBody className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-lg">
              <Activity size={22} />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Brand Health
              </p>
              <p className="text-xl font-bold text-slate-900 font-mono">
                {isLoading
                  ? '...'
                  : latestHealthScore !== null
                  ? `${latestHealthScore} / 100`
                  : 'N/A'}
              </p>
            </div>
          </CardBody>
        </Card>

        <Card className="border border-slate-200">
          <CardBody className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-amber-50 text-amber-600 rounded-lg">
              <ShieldCheck size={22} />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Risk Assessment
              </p>
              <p className="text-base font-bold text-slate-900">
                {isLoading ? '...' : latestRiskLevel}
              </p>
            </div>
          </CardBody>
        </Card>

        <Card className="border border-slate-200">
          <CardBody className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-purple-50 text-purple-600 rounded-lg">
              <TrendingUp size={22} />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Strategic Actions
              </p>
              <p className="text-xl font-bold text-slate-900 font-mono">
                {isLoading ? '...' : totalRecommendations}
              </p>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Main Content Area */}
      {isLoading ? (
        <Card className="border border-slate-200">
          <CardBody className="p-6 space-y-4">
            <Skeleton className="h-6 w-1/4 rounded" />
            <Skeleton className="h-16 w-full rounded-lg" />
            <Skeleton className="h-16 w-full rounded-lg" />
            <Skeleton className="h-16 w-full rounded-lg" />
          </CardBody>
        </Card>
      ) : isError ? (
        <ErrorState
          message="Could not connect to the reporting intelligence engine. Please retry."
          onRetry={() => refetch()}
        />
      ) : reports.length === 0 ? (
        <Card className="border border-slate-200">
          <CardBody className="py-12">
            <EmptyState
              icon={<FileText size={48} className="text-slate-400" />}
              title="No Executive Reports Compiled"
              description="Synthesize your first executive brief to compile SEO metrics, pricing parity, website change velocity, sentiment NSS, and advertising intelligence into a single report."
              actionLabel={
                generateMutation.isPending
                  ? 'Compiling Brief...'
                  : 'Generate First Executive Brief'
              }
              onAction={handleGenerate}
            />
          </CardBody>
        </Card>
      ) : (
        <Card className="border border-slate-200 overflow-hidden shadow-xs">
          <CardHeader className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">
                Historical Executive Briefs Archive
              </h2>
              <p className="text-xs text-slate-500">
                Chronological list of compiled strategic audits for {currentBrand?.name || 'this brand'}
              </p>
            </div>
            <span className="text-xs font-mono font-semibold text-slate-600 bg-white border border-slate-200 px-2 py-0.5 rounded">
              {totalReports} {totalReports === 1 ? 'Report' : 'Reports'}
            </span>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/70 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-4">Report Type</th>
                  <th className="py-3 px-4">Health Score</th>
                  <th className="py-3 px-4">Risk Level</th>
                  <th className="py-3 px-4">Key Strategic Takeaway</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {reports.map((report) => {
                  const content = report.content;
                  const health = content?.health_score ?? 0;
                  const risk = content?.risk_level ?? 'Moderate';
                  const narrative = report.ai_narrative || 'Intelligence brief compiled';
                  const swotCount = content?.swot?.length ?? 0;

                  return (
                    <tr
                      key={report.id}
                      onClick={() => handleOpenReport(report)}
                      className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                    >
                      <td className="py-3.5 px-4 font-mono text-xs text-slate-700 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <Calendar size={14} className="text-slate-400" />
                          <span>
                            {report.generated_at
                              ? new Date(report.generated_at).toLocaleString([], {
                                  year: 'numeric',
                                  month: 'short',
                                  day: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit',
                                })
                              : 'Recent'}
                          </span>
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="font-semibold text-slate-900 capitalize">
                          {report.report_type.replace(/_/g, ' ')}
                        </span>
                        <div className="text-[11px] text-slate-400 font-mono">
                          {swotCount} SWOT insights
                        </div>
                      </td>

                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {getHealthBadge(health)}
                      </td>

                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {getRiskBadge(risk)}
                      </td>

                      <td className="py-3.5 px-4 max-w-xs truncate text-xs text-slate-600">
                        {narrative}
                      </td>

                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenReport(report);
                            }}
                            className="flex items-center gap-1 text-xs"
                          >
                            <Eye size={13} />
                            <span>View Brief</span>
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => handleDelete(report.id, e)}
                            className="!p-1.5 text-slate-400 hover:text-rose-600"
                            aria-label="Delete report"
                          >
                            <Trash2 size={15} />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Report Viewer Modal */}
      <ReportViewerModal
        report={selectedReport}
        isOpen={isViewerOpen}
        onClose={() => setIsViewerOpen(false)}
        brandName={currentBrand?.name}
        brandDomain={currentBrand?.domain}
      />
    </div>
  );
};
