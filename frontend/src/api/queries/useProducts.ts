import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../client';
import { Product, ProductDetail, ProductAnalyticsSummary, PaginatedResponse } from '@/types';

export interface ProductQueryParams {
  page?: number;
  size?: number;
  search?: string;
  availability?: string;
  min_price?: number;
  max_price?: number;
  order_by?: 'recent' | 'price_asc' | 'price_desc' | 'name_asc';
}

export const useGetProducts = (brandId?: string, params?: ProductQueryParams) => {
  return useQuery({
    queryKey: ['products', brandId, params],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<Product>>(`/products/brands/${brandId}/products`, {
        params,
      });
      return data;
    },
    enabled: !!brandId,
    staleTime: 30_000,
  });
};

export const useGetProductDetail = (productId?: string) => {
  return useQuery({
    queryKey: ['product', productId],
    queryFn: async () => {
      const { data } = await apiClient.get<ProductDetail>(`/products/products/${productId}`);
      return data;
    },
    enabled: !!productId,
  });
};

export const useGetProductAnalytics = (brandId?: string) => {
  return useQuery({
    queryKey: ['product-analytics', brandId],
    queryFn: async () => {
      const { data } = await apiClient.get<ProductAnalyticsSummary>(`/products/brands/${brandId}/products/analytics`);
      return data;
    },
    enabled: !!brandId,
    staleTime: 30_000,
  });
};

export const useExtractProducts = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ brandId, snapshotId }: { brandId: string; snapshotId?: string }) => {
      const { data } = await apiClient.post(`/products/brands/${brandId}/products/extract`, null, {
        params: snapshotId ? { snapshot_id: snapshotId } : {},
      });
      return data;
    },
    onSuccess: (_, { brandId }) => {
      queryClient.invalidateQueries({ queryKey: ['products', brandId] });
      queryClient.invalidateQueries({ queryKey: ['product-analytics', brandId] });
    },
  });
};
