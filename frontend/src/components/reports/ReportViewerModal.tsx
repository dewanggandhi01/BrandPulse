import React, { useEffect } from 'react';
import {
  Printer,
  TrendingUp,
  ShieldCheck,
  AlertTriangle,
  Sparkles,
  ShieldAlert,
  CheckCircle2,
  Target,
  BarChart3,
  Activity,
  FileText,
  Radio,
  Layers,
  ShoppingBag,
} from 'lucide-react';
import type { Report, SwotItem } from '../../types';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Modal } from '../ui/Modal';

interface ReportViewerModalProps {
  report: Report | null;
  isOpen: boolean;
  onClose: () => void;
  brandName?: string;
  brandDomain?: string;
}

export const ReportViewerModal: React.FC<ReportViewerModalProps> = ({
  report,
  isOpen,
  onClose,
  brandName = 'ApexCloud',
  brandDomain = 'apexcloud.com',
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen || !report) return null;

  const content = report.content;
  const healthScore = content?.health_score ?? 0;
  const riskLevel = content?.risk_level ?? 'Moderate Attention';
  const pillarScores = content?.pillar_scores ?? {
    seo: 0,
    pricing: 0,
    sentiment: 0,
    agility: 0,
    advertising: 0,
  };
  const swot = content?.swot ?? [];
  const recommendations = content?.recommendations ?? [];
  const narrative = report.ai_narrative || 'Comprehensive intelligence report compiled successfully.';

  // Group SWOT items
  const strengths = swot.filter((s: SwotItem) => s.category === 'strength');
  const weaknesses = swot.filter((s: SwotItem) => s.category === 'weakness');
  const opportunities = swot.filter((s: SwotItem) => s.category === 'opportunity');
  const threats = swot.filter((s: SwotItem) => s.category === 'threat');

  const getRiskBadge = (risk: string) => {
    if (risk.toLowerCase().includes('low')) {
      return <Badge variant="success">Low Risk</Badge>;
    } else if (risk.toLowerCase().includes('moderate')) {
      return <Badge variant="warning">Moderate Attention</Badge>;
    } else {
      return <Badge variant="critical">High Threat</Badge>;
    }
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 75) return 'text-emerald-600 border-emerald-500 bg-emerald-50';
    if (score >= 50) return 'text-amber-600 border-amber-500 bg-amber-50';
    return 'text-rose-600 border-rose-500 bg-rose-50';
  };

  const getImpactBadgeVariant = (impact: string): 'critical' | 'warning' | 'info' | 'default' => {
    switch (impact?.toLowerCase()) {
      case 'high':
        return 'critical';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const modalTitle = (
    <div className="flex items-center gap-3">
      <div className="p-2 bg-blue-100 text-blue-700 rounded-lg">
        <FileText size={20} />
      </div>
      <div>
        <h2 className="text-lg font-bold text-slate-900">
          Executive Intelligence Brief
        </h2>
        <p className="text-xs text-slate-500 font-mono">
          ID: {report.id.slice(0, 8)} • Generated{' '}
          {report.generated_at
            ? new Date(report.generated_at).toLocaleString()
            : 'Recent'}
        </p>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={modalTitle}
      size="4xl"
      className="print:max-h-none print:shadow-none print:border-none"
    >
      <div className="space-y-8 print:p-0 print:overflow-visible">
        <div className="flex justify-end print:hidden">
          <Button
            variant="secondary"
            size="sm"
            onClick={handlePrint}
            className="flex items-center gap-1.5"
          >
            <Printer size={15} />
            <span>Print / Save PDF</span>
          </Button>
        </div>
        
        {/* Header Banner */}
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-200 gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-200">
                C-Suite Intelligence
              </span>
              {getRiskBadge(riskLevel)}
            </div>
            <h1 className="text-2xl md:text-3xl font-bold text-slate-900">
              {brandName}
            </h1>
            <p className="text-sm text-slate-500">{brandDomain}</p>
          </div>

          {/* Health Score Gauge */}
          <div className="flex items-center gap-4 bg-slate-50 border border-slate-200 p-4 rounded-xl shrink-0">
            <div
              className={`w-16 h-16 rounded-full border-4 flex flex-col items-center justify-center font-bold font-mono text-xl ${getHealthScoreColor(
                healthScore
              )}`}
            >
              <span>{healthScore}</span>
              <span className="text-[9px] font-normal text-slate-500 uppercase -mt-1">
                / 100
              </span>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider">
                Composite Brand Health
              </p>
              <p className="text-sm font-bold text-slate-900">{riskLevel}</p>
              <p className="text-xs text-slate-400">Weighted Multi-Pillar Blend</p>
            </div>
          </div>
        </div>

          {/* AI Executive Synthesis Narrative */}
          <div className="bg-gradient-to-r from-blue-50/70 via-indigo-50/40 to-slate-50 border border-blue-200/80 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-2 text-blue-900 font-semibold text-sm">
              <Sparkles size={16} className="text-blue-600" />
              <span>Executive Synthesis & Narrative</span>
            </div>
            <p className="text-sm text-slate-700 leading-relaxed font-sans">
              {narrative}
            </p>
          </div>

          {/* 5 Pillar Scorecard Breakdown */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <BarChart3 size={16} className="text-slate-500" />
                Intelligence Pillars
              </h3>
              <span className="text-xs text-slate-500">Benchmark Scale (0-100)</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {/* Pillar 1: SEO */}
              <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-medium text-slate-600 flex items-center gap-1">
                    <Activity size={13} className="text-blue-500" /> SEO Audit
                  </span>
                  <span className="text-xs font-mono font-bold text-slate-900">
                    {pillarScores.seo}%
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-blue-600 h-full rounded-full transition-all"
                    style={{ width: `${Math.min(100, pillarScores.seo)}%` }}
                  />
                </div>
              </div>

              {/* Pillar 2: Pricing */}
              <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-medium text-slate-600 flex items-center gap-1">
                    <ShoppingBag size={13} className="text-emerald-500" /> Pricing & Catalog
                  </span>
                  <span className="text-xs font-mono font-bold text-slate-900">
                    {pillarScores.pricing}%
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-emerald-600 h-full rounded-full transition-all"
                    style={{ width: `${Math.min(100, pillarScores.pricing)}%` }}
                  />
                </div>
              </div>

              {/* Pillar 3: Sentiment */}
              <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-medium text-slate-600 flex items-center gap-1">
                    <Radio size={13} className="text-indigo-500" /> Sentiment
                  </span>
                  <span className="text-xs font-mono font-bold text-slate-900">
                    {pillarScores.sentiment}%
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-indigo-600 h-full rounded-full transition-all"
                    style={{ width: `${Math.min(100, pillarScores.sentiment)}%` }}
                  />
                </div>
              </div>

              {/* Pillar 4: Agility */}
              <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-medium text-slate-600 flex items-center gap-1">
                    <Layers size={13} className="text-amber-500" /> Web Agility
                  </span>
                  <span className="text-xs font-mono font-bold text-slate-900">
                    {pillarScores.agility}%
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-amber-500 h-full rounded-full transition-all"
                    style={{ width: `${Math.min(100, pillarScores.agility)}%` }}
                  />
                </div>
              </div>

              {/* Pillar 5: Advertising */}
              <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-medium text-slate-600 flex items-center gap-1">
                    <Target size={13} className="text-purple-500" /> Paid Ads
                  </span>
                  <span className="text-xs font-mono font-bold text-slate-900">
                    {pillarScores.advertising}%
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-purple-600 h-full rounded-full transition-all"
                    style={{ width: `${Math.min(100, pillarScores.advertising)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* 4-Quadrant SWOT Matrix */}
          <div>
            <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3 flex items-center gap-2">
              <ShieldCheck size={16} className="text-slate-500" />
              Strategic SWOT Analysis
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Quadrant 1: Strengths */}
              <div className="border border-emerald-200 bg-emerald-50/40 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3 pb-2 border-b border-emerald-200/70">
                  <CheckCircle2 size={18} className="text-emerald-600" />
                  <h4 className="font-bold text-emerald-900 text-sm tracking-wide uppercase">
                    Strengths ({strengths.length})
                  </h4>
                </div>
                {strengths.length > 0 ? (
                  <div className="space-y-2.5">
                    {strengths.map((item, idx) => (
                      <div
                        key={idx}
                        className="bg-white p-3 rounded-lg border border-emerald-100 shadow-xs"
                      >
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="font-semibold text-xs text-slate-900">
                            {item.title}
                          </span>
                          <Badge variant={getImpactBadgeVariant(item.impact)}>
                            {item.impact} impact
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-600 leading-normal">
                          {item.description}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">
                    No primary strengths identified in current crawl cycle.
                  </p>
                )}
              </div>

              {/* Quadrant 2: Weaknesses */}
              <div className="border border-rose-200 bg-rose-50/40 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3 pb-2 border-b border-rose-200/70">
                  <AlertTriangle size={18} className="text-rose-600" />
                  <h4 className="font-bold text-rose-900 text-sm tracking-wide uppercase">
                    Weaknesses ({weaknesses.length})
                  </h4>
                </div>
                {weaknesses.length > 0 ? (
                  <div className="space-y-2.5">
                    {weaknesses.map((item, idx) => (
                      <div
                        key={idx}
                        className="bg-white p-3 rounded-lg border border-rose-100 shadow-xs"
                      >
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="font-semibold text-xs text-slate-900">
                            {item.title}
                          </span>
                          <Badge variant={getImpactBadgeVariant(item.impact)}>
                            {item.impact} impact
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-600 leading-normal">
                          {item.description}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">
                    No critical structural weaknesses observed.
                  </p>
                )}
              </div>

              {/* Quadrant 3: Opportunities */}
              <div className="border border-blue-200 bg-blue-50/40 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3 pb-2 border-b border-blue-200/70">
                  <Sparkles size={18} className="text-blue-600" />
                  <h4 className="font-bold text-blue-900 text-sm tracking-wide uppercase">
                    Opportunities ({opportunities.length})
                  </h4>
                </div>
                {opportunities.length > 0 ? (
                  <div className="space-y-2.5">
                    {opportunities.map((item, idx) => (
                      <div
                        key={idx}
                        className="bg-white p-3 rounded-lg border border-blue-100 shadow-xs"
                      >
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="font-semibold text-xs text-slate-900">
                            {item.title}
                          </span>
                          <Badge variant={getImpactBadgeVariant(item.impact)}>
                            {item.impact} impact
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-600 leading-normal">
                          {item.description}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">
                    Market conditions stable across tracked dimensions.
                  </p>
                )}
              </div>

              {/* Quadrant 4: Threats */}
              <div className="border border-amber-200 bg-amber-50/40 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3 pb-2 border-b border-amber-200/70">
                  <ShieldAlert size={18} className="text-amber-600" />
                  <h4 className="font-bold text-amber-900 text-sm tracking-wide uppercase">
                    Threats ({threats.length})
                  </h4>
                </div>
                {threats.length > 0 ? (
                  <div className="space-y-2.5">
                    {threats.map((item, idx) => (
                      <div
                        key={idx}
                        className="bg-white p-3 rounded-lg border border-amber-100 shadow-xs"
                      >
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="font-semibold text-xs text-slate-900">
                            {item.title}
                          </span>
                          <Badge variant={getImpactBadgeVariant(item.impact)}>
                            {item.impact} impact
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-600 leading-normal">
                          {item.description}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">
                    No urgent competitive threats detected.
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Strategic Action Recommendations */}
          <div>
            <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3 flex items-center gap-2">
              <TrendingUp size={16} className="text-slate-500" />
              Strategic Recommendations
            </h3>
            <div className="bg-white border border-slate-200 rounded-xl p-4 divide-y divide-slate-100">
              {recommendations.length > 0 ? (
                recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
                    <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                      {index + 1}
                    </span>
                    <p className="text-xs md:text-sm text-slate-700 leading-relaxed">
                      {rec}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500 italic py-2">
                  No explicit action items recommended at this time.
                </p>
              )}
            </div>
          </div>

        {/* Modal Footer */}
        <div className="pt-4 border-t border-slate-200 flex items-center justify-between print:hidden">
          <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
            <span>Confidential Executive Brief</span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" onClick={onClose}>
              Close
            </Button>
            <Button variant="primary" size="sm" onClick={handlePrint} className="flex items-center gap-1.5">
              <Printer size={15} />
              <span>Print / Save PDF</span>
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};
