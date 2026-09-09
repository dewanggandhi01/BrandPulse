import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../client';
import type { Report, PaginatedResponse } from '../../types';

export interface GenerateReportPayload {
  report_type?: string;
}

export interface GenerateReportResponse {
  message: string;
  report: Report;
}

export function useGetReports(
  brandId: string | null | undefined,
  page = 1,
  size = 20
) {
  return useQuery({
    queryKey: ['reports', brandId, page, size],
    queryFn: async () => {
      if (!brandId) return null;
      const params = new URLSearchParams({
        page: page.toString(),
        size: size.toString(),
      });
      const response = await apiClient.get<PaginatedResponse<Report>>(
        `/reports/brand/${brandId}?${params.toString()}`
      );
      return response.data;
    },
    enabled: !!brandId,
  });
}

export function useGetReport(reportId: string | null | undefined) {
  return useQuery({
    queryKey: ['report-detail', reportId],
    queryFn: async () => {
      if (!reportId) return null;
      const response = await apiClient.get<Report>(`/reports/${reportId}`);
      return response.data;
    },
    enabled: !!reportId,
  });
}

export function useGenerateReport(brandId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload?: GenerateReportPayload) => {
      if (!brandId) throw new Error('No brand selected');
      const response = await apiClient.post<GenerateReportResponse>(
        `/reports/brand/${brandId}/generate`,
        payload || { report_type: 'executive_brief' }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', brandId] });
    },
  });
}

export function useDeleteReport(brandId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (reportId: string) => {
      await apiClient.delete(`/reports/${reportId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', brandId] });
    },
  });
}

export function useSeedReports(brandId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      if (!brandId) throw new Error('No brand selected');
      const response = await apiClient.post<GenerateReportResponse>(
        `/reports/brand/${brandId}/seed`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', brandId] });
    },
  });
}
