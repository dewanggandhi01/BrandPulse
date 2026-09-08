import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../client';
import { Brand } from '@/types';

export const useGetBrands = () => {
  return useQuery({
    queryKey: ['brands'],
    queryFn: async () => {
      const { data } = await apiClient.get<any>('/brands');
      if (data && Array.isArray(data.items)) {
        return data.items as Brand[];
      }
      if (Array.isArray(data)) {
        return data as Brand[];
      }
      return [] as Brand[];
    },
  });
};

export const useGetBrand = (id: string) => {
  return useQuery({
    queryKey: ['brands', id],
    queryFn: async () => {
      const { data } = await apiClient.get<Brand>(`/brands/${id}`);
      return data;
    },
    enabled: !!id,
  });
};

export const useCreateBrand = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (newBrand: Partial<Brand>) => {
      const { data } = await apiClient.post<Brand>('/brands', newBrand);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['brands'] });
    },
  });
};
