import React, { useState } from 'react';
import { Copy, Check, GitCompare, ArrowRight, Plus, Minus, FileText, Split, AlignLeft } from 'lucide-react';
import { useGetChangeDetail } from '@/api/queries/useChanges';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';

interface VisualDiffModalProps {
  changeId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export const VisualDiffModal: React.FC<VisualDiffModalProps> = ({
  changeId,
  isOpen,
  onClose,
}) => {
  const { data: event, isLoading, error } = useGetChangeDetail(changeId || undefined);
  const [viewMode, setViewMode] = useState<'chunks' | 'unified' | 'side-by-side'>('chunks');
  const [copied, setCopied] = useState(false);

  if (!isOpen || !changeId) return null;

  const diff = event?.diff_details;
  const chunks = diff?.diff_chunks || [];
  const unified = diff?.unified_diff || '';

  const handleCopy = () => {
    if (!unified) return;
    navigator.clipboard.writeText(unified);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getBadgeVariant = (type: string): 'default' | 'success' | 'warning' | 'critical' | 'info' => {
    switch (type) {
      case 'pricing_change':
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

  const modalTitle = (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <Badge variant={getBadgeVariant(event?.change_type || '')}>
          {(event?.change_type || 'change').replace('_', ' ').toUpperCase()}
        </Badge>
        {event?.similarity_ratio != null && (
          <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
            Similarity: {(event.similarity_ratio * 100).toFixed(1)}%
          </span>
        )}
        {event?.created_at && (
          <span className="text-xs text-slate-400">
            {new Date(event.created_at).toLocaleString()}
          </span>
        )}
      </div>
      <span className="text-lg font-bold text-slate-900 leading-snug">
        {event?.ai_summary || 'Visual Snapshot Comparison'}
      </span>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={modalTitle}
      size="4xl"
      isLoading={isLoading && !event}
    >
      <div className="space-y-4">
        <div className="flex items-center justify-end">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleCopy}
            disabled={!unified}
            className="text-xs flex items-center gap-1.5"
          >
            {copied ? <Check size={14} className="text-emerald-600" /> : <Copy size={14} />}
            {copied ? 'Copied' : 'Copy Unified Diff'}
          </Button>
        </div>

        {error && (
          <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
            Failed to load diff details.
          </div>
        )}

          {event && diff && (
            <>
              {/* Metric Stats Banner */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
                <div className="flex items-center gap-2">
                  <span className="p-1.5 rounded bg-emerald-100 text-emerald-700 font-bold">
                    <Plus size={14} />
                  </span>
                  <div>
                    <div className="font-semibold text-slate-900 tnum">{diff.additions_count}</div>
                    <div className="text-slate-500 text-[11px]">Additions</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="p-1.5 rounded bg-red-100 text-red-700 font-bold">
                    <Minus size={14} />
                  </span>
                  <div>
                    <div className="font-semibold text-slate-900 tnum">{diff.deletions_count}</div>
                    <div className="text-slate-500 text-[11px]">Deletions</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="p-1.5 rounded bg-blue-100 text-blue-700 font-bold">
                    <GitCompare size={14} />
                  </span>
                  <div>
                    <div className="font-semibold text-slate-900 tnum">{diff.total_changes}</div>
                    <div className="text-slate-500 text-[11px]">Sections Modified</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="p-1.5 rounded bg-purple-100 text-purple-700 font-bold">
                    <FileText size={14} />
                  </span>
                  <div>
                    <div className="font-semibold text-slate-900 tnum">
                      {diff.word_delta > 0 ? `+${diff.word_delta}` : diff.word_delta}
                    </div>
                    <div className="text-slate-500 text-[11px]">Word Count Shift</div>
                  </div>
                </div>
              </div>

              {/* View Mode Toggle */}
              <div className="flex items-center justify-between pt-1">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Diff Visualizer
                </div>
                <div className="flex bg-slate-100 p-0.5 rounded-lg text-xs font-medium text-slate-600">
                  <button
                    onClick={() => setViewMode('chunks')}
                    className={`px-3 py-1 rounded-md transition-colors flex items-center gap-1.5 ${
                      viewMode === 'chunks' ? 'bg-white shadow text-slate-900 font-semibold' : 'hover:text-slate-900'
                    }`}
                  >
                    <AlignLeft size={13} />
                    Block Feed
                  </button>
                  <button
                    onClick={() => setViewMode('side-by-side')}
                    className={`px-3 py-1 rounded-md transition-colors flex items-center gap-1.5 ${
                      viewMode === 'side-by-side' ? 'bg-white shadow text-slate-900 font-semibold' : 'hover:text-slate-900'
                    }`}
                  >
                    <Split size={13} />
                    Side-by-Side
                  </button>
                  <button
                    onClick={() => setViewMode('unified')}
                    className={`px-3 py-1 rounded-md transition-colors flex items-center gap-1.5 ${
                      viewMode === 'unified' ? 'bg-white shadow text-slate-900 font-semibold' : 'hover:text-slate-900'
                    }`}
                  >
                    <FileText size={13} />
                    Unified Patch
                  </button>
                </div>
              </div>

              {/* Diff Display Canvas */}
              <div className="border border-slate-200 rounded-lg overflow-hidden bg-slate-950 font-mono text-xs">
                {viewMode === 'unified' ? (
                  <div className="p-4 overflow-x-auto max-h-96">
                    <pre className="text-slate-300 whitespace-pre-wrap leading-relaxed">
                      {unified.split('\n').map((line, idx) => {
                        const isAdd = line.startsWith('+') && !line.startsWith('+++');
                        const isDel = line.startsWith('-') && !line.startsWith('---');
                        const isMeta = line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++');
                        return (
                          <div
                            key={idx}
                            className={`px-2 py-0.5 rounded-sm ${
                              isAdd
                                ? 'bg-emerald-950/80 text-emerald-400 font-medium'
                                : isDel
                                ? 'bg-red-950/80 text-red-400 font-medium'
                                : isMeta
                                ? 'text-blue-400 font-semibold'
                                : 'text-slate-400'
                            }`}
                          >
                            {line}
                          </div>
                        );
                      })}
                    </pre>
                  </div>
                ) : viewMode === 'side-by-side' ? (
                  <div className="grid grid-cols-2 divide-x divide-slate-800 max-h-96 overflow-y-auto">
                    <div className="p-3 space-y-2 bg-slate-900/60">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider pb-1 border-b border-slate-800">
                        Prior Snapshot Content
                      </div>
                      {chunks.filter((c) => c.type === 'removed' || c.type === 'modified').map((c, idx) => (
                        <div key={idx} className="p-2 rounded bg-red-950/60 border border-red-900/40 text-red-300">
                          <span className="text-[10px] uppercase font-bold text-red-400 block mb-0.5">Removed</span>
                          {c.type === 'modified' ? c.old_content : c.content}
                        </div>
                      ))}
                      {chunks.filter((c) => c.type === 'removed' || c.type === 'modified').length === 0 && (
                        <div className="text-slate-500 py-8 text-center text-xs">No deleted elements</div>
                      )}
                    </div>

                    <div className="p-3 space-y-2 bg-slate-900/60">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider pb-1 border-b border-slate-800">
                        Current Snapshot Content
                      </div>
                      {chunks.filter((c) => c.type === 'added' || c.type === 'modified').map((c, idx) => (
                        <div key={idx} className="p-2 rounded bg-emerald-950/60 border border-emerald-900/40 text-emerald-300">
                          <span className="text-[10px] uppercase font-bold text-emerald-400 block mb-0.5">Added</span>
                          {c.type === 'modified' ? c.new_content : c.content}
                        </div>
                      ))}
                      {chunks.filter((c) => c.type === 'added' || c.type === 'modified').length === 0 && (
                        <div className="text-slate-500 py-8 text-center text-xs">No added elements</div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="p-3 space-y-2 max-h-96 overflow-y-auto">
                    {chunks.map((chunk, idx) => {
                      if (chunk.type === 'added') {
                        return (
                          <div key={idx} className="p-2.5 rounded bg-emerald-950/60 border border-emerald-900/50 text-emerald-300 flex items-start gap-2">
                            <span className="px-1.5 py-0.5 rounded bg-emerald-900 text-emerald-200 text-[10px] font-bold uppercase shrink-0">
                              + Added
                            </span>
                            <span className="leading-relaxed">{chunk.content}</span>
                          </div>
                        );
                      }
                      if (chunk.type === 'removed') {
                        return (
                          <div key={idx} className="p-2.5 rounded bg-red-950/60 border border-red-900/50 text-red-300 flex items-start gap-2">
                            <span className="px-1.5 py-0.5 rounded bg-red-900 text-red-200 text-[10px] font-bold uppercase shrink-0">
                              - Removed
                            </span>
                            <span className="leading-relaxed line-through text-red-400">{chunk.content}</span>
                          </div>
                        );
                      }
                      if (chunk.type === 'modified') {
                        return (
                          <div key={idx} className="p-2.5 rounded bg-blue-950/60 border border-blue-900/50 text-blue-200 space-y-1.5">
                            <span className="px-1.5 py-0.5 rounded bg-blue-900 text-blue-200 text-[10px] font-bold uppercase inline-block">
                              ~ Modified Section
                            </span>
                            <div className="text-red-400 line-through text-[11px] pl-2 border-l border-red-700">
                              {chunk.old_content}
                            </div>
                            <div className="text-emerald-400 text-[11px] pl-2 border-l border-emerald-700 font-semibold flex items-center gap-1.5">
                              <ArrowRight size={11} /> {chunk.new_content}
                            </div>
                          </div>
                        );
                      }
                      return null;
                    })}
                  </div>
                )}
              </div>
            </>
          )}
      </div>
    </Modal>
  );
};
