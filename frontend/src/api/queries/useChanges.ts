import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../client';
import { ChangeEvent, ChangeAnalyticsSummary, PaginatedResponse } from '@/types';

export interface ChangeQueryParams {
  page?: number;
  size?: number;
  change_type?: string;
}

export const useGetChanges = (brandId?: string, params?: ChangeQueryParams) => {
  return useQuery({
    queryKey: ['changes', brandId, params],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<ChangeEvent>>(`/changes/brand/${brandId}`, {
        params,
      });
      return data;
    },
    enabled: !!brandId,
    staleTime: 30_000,
  });
};

export const useGetChangeDetail = (changeId?: string) => {
  return useQuery({
    queryKey: ['change-detail', changeId],
    queryFn: async () => {
      const { data } = await apiClient.get<ChangeEvent>(`/changes/${changeId}`);
      return data;
    },
    enabled: !!changeId,
  });
};

export const useGetChangeAnalytics = (brandId?: string) => {
  return useQuery({
    queryKey: ['change-analytics', brandId],
    queryFn: async () => {
      const { data } = await apiClient.get<ChangeAnalyticsSummary>(`/changes/brand/${brandId}/analytics`);
      return data;
    },
    enabled: !!brandId,
    staleTime: 30_000,
  });
};

export const useCompareSnapshots = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ snapshotId, previousSnapshotId }: { snapshotId: string; previousSnapshotId?: string }) => {
      const { data } = await apiClient.post<ChangeEvent>('/changes/compare', {
        snapshot_id: snapshotId,
        previous_snapshot_id: previousSnapshotId,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['changes'] });
      queryClient.invalidateQueries({ queryKey: ['change-analytics'] });
    },
  });
};

export const useScanBrandChanges = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (brandId: string) => {
      const { data } = await apiClient.post(`/changes/brand/${brandId}/scan`);
      return data;
    },
    onSuccess: (_, brandId) => {
      queryClient.invalidateQueries({ queryKey: ['changes', brandId] });
      queryClient.invalidateQueries({ queryKey: ['change-analytics', brandId] });
    },
  });
};

