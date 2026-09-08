import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../client';
import type { Mention, ReputationAnalytics, PaginatedResponse } from '../../types';

export function useGetMentions(
  brandId: string | null | undefined,
  source?: string,
  label?: string,
  page = 1,
  size = 20
) {
  return useQuery({
    queryKey: ['mentions', brandId, source, label, page, size],
    queryFn: async () => {
      if (!brandId) return null;
      const params = new URLSearchParams({
        page: page.toString(),
        size: size.toString(),
      });
      if (source && source !== 'all') params.append('source', source);
      if (label && label !== 'all') params.append('label', label);

      const response = await apiClient.get<PaginatedResponse<Mention>>(
        `/mentions/brand/${brandId}?${params.toString()}`
      );
      return response.data;
    },
    enabled: !!brandId,
  });
}

export function useGetReputationAnalytics(brandId: string | null | undefined) {
  return useQuery({
    queryKey: ['reputation-analytics', brandId],
    queryFn: async () => {
      if (!brandId) return null;
      const response = await apiClient.get<ReputationAnalytics>(
        `/mentions/brand/${brandId}/analytics`
      );
      return response.data;
    },
    enabled: !!brandId,
  });
}

export interface CreateMentionPayload {
  source: string;
  source_url?: string;
  content: string;
  author?: string;
  published_at?: string;
}

export function useCreateMention(brandId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateMentionPayload) => {
      if (!brandId) throw new Error('Brand ID is required');
      const response = await apiClient.post<Mention>(
        `/mentions/brand/${brandId}`,
        payload
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mentions', brandId] });
      queryClient.invalidateQueries({ queryKey: ['reputation-analytics', brandId] });
    },
  });
}

export function useSeedMentions(brandId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      if (!brandId) throw new Error('Brand ID is required');
      const response = await apiClient.post<{ status: string; count: number; brand_id: string }>(
        `/mentions/brand/${brandId}/seed`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mentions', brandId] });
      queryClient.invalidateQueries({ queryKey: ['reputation-analytics', brandId] });
    },
  });
}

export interface AnalyzeTextPayload {
  text: string;
}

export interface AnalyzeTextResult {
  text: string;
  label: 'positive' | 'negative' | 'neutral';
  positive_score: number;
  negative_score: number;
  neutral_score: number;
  compound_score: number;
  model_version: string;
}

export function useAnalyzeText() {
  return useMutation({
    mutationFn: async (payload: AnalyzeTextPayload) => {
      const response = await apiClient.post<AnalyzeTextResult>(
        `/mentions/analyze-text`,
        payload
      );
      return response.data;
    },
  });
}
