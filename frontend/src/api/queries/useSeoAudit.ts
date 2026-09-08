import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../client';
import { SeoAudit } from '@/types';

export interface SeoIssueItem {
  id: string;
  pillar: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  recommendation: string;
}

export interface SeoAuditHistoryItem {
  id: string;
  total_score: number;
  technical_score: number;
  content_score: number;
  structured_data_score: number;
  link_score: number;
  audited_at: string;
}

export interface SeoAuditHistoryResponse {
  items: SeoAuditHistoryItem[];
  brand_id: string;
  latest_score?: number;
}

export const useGetLatestSeoAudit = (brandId?: string) => {
  return useQuery({
    queryKey: ['seo-audit', 'latest', brandId],
    queryFn: async () => {
      const { data } = await apiClient.get<SeoAudit>(`/seo/brands/${brandId}/seo-audit/latest`);
      return data;
    },
    enabled: !!brandId,
    retry: false,
  });
};

export const useGetSeoAuditHistory = (brandId?: string) => {
  return useQuery({
    queryKey: ['seo-audit', 'history', brandId],
    queryFn: async () => {
      const { data } = await apiClient.get<SeoAuditHistoryResponse>(`/seo/brands/${brandId}/seo-audit/history`);
      return data;
    },
    enabled: !!brandId,
    retry: false,
  });
};

export const useRunSeoAudit = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: string | { brandId: string; refresh?: boolean }) => {
      const brandId = typeof params === 'string' ? params : params.brandId;
      const refresh = typeof params === 'object' && params.refresh;
      const url = `/seo/brands/${brandId}/seo-audit/run${refresh ? '?refresh=true' : ''}`;
      const { data } = await apiClient.post<SeoAudit>(url);
      return data;
    },
    onSuccess: (_, variables) => {
      const brandId = typeof variables === 'string' ? variables : variables.brandId;
      queryClient.invalidateQueries({ queryKey: ['seo-audit', 'latest', brandId] });
      queryClient.invalidateQueries({ queryKey: ['seo-audit', 'history', brandId] });
    },
  });
};
