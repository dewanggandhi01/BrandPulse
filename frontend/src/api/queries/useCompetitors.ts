import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../client';
import { CompetitorItem, CompetitorComparisonMatrix } from '@/types';

export const useGetLinkedCompetitors = (brandId?: string) => {
  return useQuery({
    queryKey: ['competitors', brandId],
    queryFn: async () => {
      const { data } = await apiClient.get<CompetitorItem[]>(`/competitors/brand/${brandId}`);
      return data;
    },
    enabled: !!brandId,
    staleTime: 30_000,
  });
};

export const useGetCompetitorComparison = (brandId?: string) => {
  return useQuery({
    queryKey: ['competitor-comparison', brandId],
    queryFn: async () => {
      const { data } = await apiClient.get<CompetitorComparisonMatrix>(`/competitors/brand/${brandId}/compare`);
      return data;
    },
    enabled: !!brandId,
    staleTime: 30_000,
  });
};

export const useLinkCompetitor = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ brandId, competitorBrandId }: { brandId: string; competitorBrandId: string }) => {
      const { data } = await apiClient.post<CompetitorItem>(`/competitors/brand/${brandId}/link`, {
        competitor_brand_id: competitorBrandId,
      });
      return data;
    },
    onSuccess: (_, { brandId }) => {
      queryClient.invalidateQueries({ queryKey: ['competitors', brandId] });
      queryClient.invalidateQueries({ queryKey: ['competitor-comparison', brandId] });
    },
  });
};

export const useUnlinkCompetitor = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ linkId }: { linkId: string; brandId: string }) => {
      await apiClient.delete(`/competitors/${linkId}`);
    },
    onSuccess: (_, { brandId }) => {
      queryClient.invalidateQueries({ queryKey: ['competitors', brandId] });
      queryClient.invalidateQueries({ queryKey: ['competitor-comparison', brandId] });
    },
  });
};

export const useSyncCompetitors = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (brandId: string) => {
      const { data } = await apiClient.post(`/competitors/brand/${brandId}/sync`);
      return data;
    },
    onSuccess: (_, brandId) => {
      queryClient.invalidateQueries({ queryKey: ['competitors', brandId] });
      queryClient.invalidateQueries({ queryKey: ['competitor-comparison', brandId] });
    },
  });
};

