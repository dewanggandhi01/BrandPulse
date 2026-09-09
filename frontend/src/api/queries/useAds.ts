import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../client';
import type { AdIntel, AdIntelAnalytics, PaginatedResponse } from '../../types';

export function useGetAds(
  brandId: string | null | undefined,
  platform?: string,
  adFormat?: string,
  search?: string,
  page = 1,
  size = 20
) {
  return useQuery({
    queryKey: ['ads', brandId, platform, adFormat, search, page, size],
    queryFn: async () => {
      if (!brandId) return null;
      const params = new URLSearchParams({
        page: page.toString(),
        size: size.toString(),
      });
      if (platform && platform !== 'all') params.append('platform', platform);
      if (adFormat && adFormat !== 'all') params.append('ad_format', adFormat);
      if (search && search.trim()) params.append('search', search.trim());

      const response = await apiClient.get<PaginatedResponse<AdIntel>>(
        `/ads/brand/${brandId}?${params.toString()}`
      );
      return response.data;
    },
    enabled: !!brandId,
  });
}

export function useGetAdAnalytics(brandId: string | null | undefined) {
  return useQuery({
    queryKey: ['ad-analytics', brandId],
    queryFn: async () => {
      if (!brandId) return null;
      const response = await apiClient.get<AdIntelAnalytics>(
        `/ads/brand/${brandId}/analytics`
      );
      return response.data;
    },
    enabled: !!brandId,
  });
}

export interface CreateAdPayload {
  platform: string;
  ad_text?: string;
  ad_format?: string;
  target_url?: string;
  first_seen?: string;
  last_seen?: string;
  targeting_info?: Record<string, any>;
  data_source_tag?: string;
}

export function useCreateAd(brandId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateAdPayload) => {
      if (!brandId) throw new Error('Brand ID is required');
      const response = await apiClient.post<AdIntel>(
        `/ads/brand/${brandId}`,
        payload
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ads', brandId] });
      queryClient.invalidateQueries({ queryKey: ['ad-analytics', brandId] });
    },
  });
}

export function useSeedAds(brandId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      if (!brandId) throw new Error('Brand ID is required');
      const response = await apiClient.post<{ status: string; count: number; brand_id: string }>(
        `/ads/brand/${brandId}/seed`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ads', brandId] });
      queryClient.invalidateQueries({ queryKey: ['ad-analytics', brandId] });
    },
  });
}

export interface AdParsePreviewPayload {
  raw_text: string;
  target_url?: string;
  suggested_format?: string;
}

export interface AdParsePreviewResult {
  headline: string | null;
  body_copy: string;
  cta: string | null;
  detected_format: string;
  landing_page_domain: string | null;
  utm_parameters: Record<string, string>;
  longevity_days: number;
  spend_tier: string;
  is_evergreen: boolean;
}

export function useParseAdPreview() {
  return useMutation({
    mutationFn: async (payload: AdParsePreviewPayload) => {
      const response = await apiClient.post<AdParsePreviewResult>(
        `/ads/parse-preview`,
        payload
      );
      return response.data;
    },
  });
}
