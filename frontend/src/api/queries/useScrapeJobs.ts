import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../client';
import { ScrapeJob, Snapshot } from '@/types';

export interface ScrapeJobSubmitInput {
  brand_id: string;
  job_type?: string;
  seed_urls?: string[];
  max_depth?: number;
  max_pages?: number;
  tier?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export const useGetScrapeJobs = (brandId?: string) => {
  return useQuery({
    queryKey: ['scrape-jobs', brandId],
    queryFn: async () => {
      const url = brandId ? `/scrape-jobs?brand_id=${brandId}` : '/scrape-jobs';
      const { data } = await apiClient.get<PaginatedResponse<ScrapeJob>>(url);
      return data;
    },
    refetchInterval: (query) => {
      const hasActiveJobs = query.state.data?.items?.some(
        (job) => job.status === 'pending' || job.status === 'running'
      );
      return hasActiveJobs ? 3000 : false;
    },
  });
};

export const useGetScrapeJob = (jobId: string) => {
  return useQuery({
    queryKey: ['scrape-jobs', jobId],
    queryFn: async () => {
      const { data } = await apiClient.get<ScrapeJob>(`/scrape-jobs/${jobId}`);
      return data;
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'pending' || status === 'running' ? 2000 : false;
    },
  });
};

export const useCreateScrapeJob = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ScrapeJobSubmitInput) => {
      const { data } = await apiClient.post<ScrapeJob>('/scrape-jobs', payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scrape-jobs'] });
    },
  });
};

export const useGetSnapshots = (brandId?: string, jobId?: string) => {
  return useQuery({
    queryKey: ['snapshots', { brandId, jobId }],
    queryFn: async () => {
      let url = '/snapshots';
      if (brandId) {
        url = `/snapshots/brand/${brandId}`;
      } else if (jobId) {
        url = `/snapshots?job_id=${jobId}`;
      }
      const { data } = await apiClient.get<PaginatedResponse<Snapshot>>(url);
      return data;
    },
  });
};

export const useGetSnapshotDetail = (snapshotId: string) => {
  return useQuery({
    queryKey: ['snapshots', 'detail', snapshotId],
    queryFn: async () => {
      const { data } = await apiClient.get<Snapshot & { html_content?: string }>(`/snapshots/${snapshotId}`);
      return data;
    },
    enabled: !!snapshotId,
  });
};
