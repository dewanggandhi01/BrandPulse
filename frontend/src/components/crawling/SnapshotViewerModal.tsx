import React, { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { useGetSnapshotDetail } from '@/api/queries/useScrapeJobs';
import { Copy, Check, Eye, Code, FileText } from 'lucide-react';

interface SnapshotViewerModalProps {
  snapshotId: string | null;
  onClose: () => void;
}

export const SnapshotViewerModal: React.FC<SnapshotViewerModalProps> = ({ snapshotId, onClose }) => {
  const [activeTab, setActiveTab] = useState<'rendered' | 'raw' | 'headers'>('rendered');
  const [copied, setCopied] = useState(false);
  const { data: snapshot, isLoading } = useGetSnapshotDetail(snapshotId || '');

  const handleCopy = () => {
    if (snapshot?.html_content) {
      navigator.clipboard.writeText(snapshot.html_content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Modal isOpen={!!snapshotId} onClose={onClose} title="HTML Snapshot Details" maxWidth="max-w-4xl">
      {isLoading ? (
        <div className="flex items-center justify-center p-12">
          <Spinner size="lg" />
        </div>
      ) : snapshot ? (
        <div className="space-y-4">
          {/* Metadata Badges */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
            <div className="flex flex-wrap gap-2 text-xs">
              <Badge variant={snapshot.status_code === 200 ? 'success' : 'warning'}>
                HTTP {snapshot.status_code}
              </Badge>
              <Badge variant="info">Size: {(snapshot.html_size / 1024).toFixed(1)} KB</Badge>
              <Badge variant="default">Hash: {snapshot.content_hash.substring(0, 16)}...</Badge>
              <Badge variant="default">Captured: {new Date(snapshot.captured_at).toLocaleString()}</Badge>
            </div>

            {/* View Mode Tabs */}
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-md text-xs font-medium">
              <button
                type="button"
                onClick={() => setActiveTab('rendered')}
                className={`flex items-center gap-1.5 px-3 py-1 rounded transition-colors ${
                  activeTab === 'rendered'
                    ? 'bg-surface text-brand-600 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Eye size={13} />
                Rendered Preview
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('raw')}
                className={`flex items-center gap-1.5 px-3 py-1 rounded transition-colors ${
                  activeTab === 'raw'
                    ? 'bg-surface text-brand-600 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Code size={13} />
                Raw HTML
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('headers')}
                className={`flex items-center gap-1.5 px-3 py-1 rounded transition-colors ${
                  activeTab === 'headers'
                    ? 'bg-surface text-brand-600 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <FileText size={13} />
                Headers
              </button>
            </div>
          </div>

          {/* Tab 1: Rendered HTML Preview */}
          {activeTab === 'rendered' && (
            <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-inner">
              <div className="bg-slate-50 border-b border-slate-200 px-3 py-1.5 text-xs text-slate-500 flex items-center justify-between">
                <span>Sandboxed HTML Rendered Preview</span>
                <span className="text-[10px] text-slate-400">Scripts disabled for security</span>
              </div>
              <iframe
                title="Rendered HTML Preview"
                srcDoc={snapshot.html_content || '<p class="p-4 text-slate-400">No content available</p>'}
                sandbox="allow-same-origin"
                className="w-full h-[450px] border-none"
              />
            </div>
          )}

          {/* Tab 2: Raw HTML */}
          {activeTab === 'raw' && (
            <div className="relative">
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-slate-500 font-mono">Raw HTML Content:</span>
                <Button size="sm" variant="ghost" onClick={handleCopy} className="!p-1 text-xs gap-1">
                  {copied ? <Check size={14} className="text-green-600" /> : <Copy size={14} />}
                  {copied ? 'Copied to Clipboard' : 'Copy HTML'}
                </Button>
              </div>
              <pre className="h-[450px] overflow-auto bg-slate-900 text-slate-100 p-3.5 rounded-lg text-xs font-mono whitespace-pre-wrap break-all border border-slate-800">
                {snapshot.html_content || '(Empty body)'}
              </pre>
            </div>
          )}

          {/* Tab 3: Response Headers */}
          {activeTab === 'headers' && (
            <div className="border border-slate-200 rounded-lg overflow-hidden h-[450px] overflow-y-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 sticky top-0">
                  <tr>
                    <th className="px-4 py-2.5 font-semibold w-1/3">Header Name</th>
                    <th className="px-4 py-2.5 font-semibold">Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {snapshot.headers && Object.keys(snapshot.headers).length > 0 ? (
                    Object.entries(snapshot.headers).map(([key, val]) => (
                      <tr key={key} className="hover:bg-slate-50/50">
                        <td className="px-4 py-2 text-slate-600 font-medium">{key}</td>
                        <td className="px-4 py-2 text-slate-900 break-all">{String(val)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={2} className="px-4 py-6 text-center text-slate-400 font-sans">
                        No HTTP response headers captured for this snapshot.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <p className="text-sm text-slate-500 p-4 text-center">No snapshot details available.</p>
      )}
    </Modal>
  );
};
