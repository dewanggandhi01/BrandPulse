import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { useGetScrapeJobs, useGetSnapshots } from '@/api/queries/useScrapeJobs';
import { SnapshotViewerModal } from './SnapshotViewerModal';
import { RefreshCw, Eye } from 'lucide-react';

interface ScrapeJobListProps {
  brandId?: string;
}

export const ScrapeJobList: React.FC<ScrapeJobListProps> = ({ brandId }) => {
  const [selectedSnapshotId, setSelectedSnapshotId] = useState<string | null>(null);
  const { data: jobsData, isLoading: jobsLoading, refetch: refetchJobs } = useGetScrapeJobs(brandId);
  const { data: snapsData, isLoading: snapsLoading } = useGetSnapshots(brandId);

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'info';
      case 'failed':
        return 'critical';
      default:
        return 'warning';
    }
  };

  return (
    <div className="space-y-6">
      <Card
        title="Active & Recent Crawl Jobs"
        action={
          <Button variant="ghost" size="sm" onClick={() => refetchJobs()} className="gap-1 text-xs">
            <RefreshCw size={14} /> Refresh
          </Button>
        }
      >
        {jobsLoading ? (
          <div className="p-4 flex justify-center"><Spinner /></div>
        ) : jobsData?.items && jobsData.items.length > 0 ? (
          <div className="divide-y divide-border">
            {jobsData.items.map((job) => (
              <div key={job.id} className="py-3 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-slate-500">{job.id.substring(0, 8)}</span>
                    <Badge variant={getStatusVariant(job.status)}>{job.status.toUpperCase()}</Badge>
                    <span className="text-xs text-slate-600 font-medium">{job.job_type}</span>
                  </div>
                  {job.config && typeof job.config === 'object' && (
                    <div className="text-xs text-slate-500 mt-1 flex gap-3">
                      <span>Pages: {(job.config as any).pages_crawled ?? 0}</span>
                      <span>Created: {(job.config as any).snapshots_created ?? 0}</span>
                      <span>Time: {(job.config as any).elapsed_ms ? `${(job.config as any).elapsed_ms}ms` : '-'}</span>
                    </div>
                  )}
                  {job.error_message && (
                    <p className="text-xs text-red-600 mt-1">{job.error_message}</p>
                  )}
                </div>
                <div className="text-xs text-slate-400">
                  {new Date(job.created_at).toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500 py-4 text-center">No crawl jobs initiated yet.</p>
        )}
      </Card>

      <Card title="Captured Web Snapshots">
        {snapsLoading ? (
          <div className="p-4 flex justify-center"><Spinner /></div>
        ) : snapsData?.items && snapsData.items.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-border bg-slate-50 text-slate-600">
                <tr>
                  <th className="py-2 px-3">Status</th>
                  <th className="py-2 px-3">Content Hash</th>
                  <th className="py-2 px-3">HTML Size</th>
                  <th className="py-2 px-3">Captured At</th>
                  <th className="py-2 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {snapsData.items.map((snap) => (
                  <tr key={snap.id} className="hover:bg-slate-50">
                    <td className="py-2 px-3">
                      <Badge variant={snap.status_code === 200 ? 'success' : 'warning'}>
                        {snap.status_code}
                      </Badge>
                    </td>
                    <td className="py-2 px-3 font-mono text-slate-600">
                      {snap.content_hash.substring(0, 16)}...
                    </td>
                    <td className="py-2 px-3 tabular-nums">
                      {(snap.html_size / 1024).toFixed(1)} KB
                    </td>
                    <td className="py-2 px-3 text-slate-500">
                      {new Date(snap.captured_at).toLocaleString()}
                    </td>
                    <td className="py-2 px-3 text-right">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setSelectedSnapshotId(snap.id)}
                        className="!p-1 gap-1 text-xs"
                      >
                        <Eye size={14} /> View
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-500 py-4 text-center">No snapshots stored yet. Start a crawl job above.</p>
        )}
      </Card>

      <SnapshotViewerModal
        snapshotId={selectedSnapshotId}
        onClose={() => setSelectedSnapshotId(null)}
      />
    </div>
  );
};
