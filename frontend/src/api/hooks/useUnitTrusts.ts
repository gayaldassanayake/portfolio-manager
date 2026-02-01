import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type { UnitTrust, UnitTrustWithStats, UnitTrustWithStatsRaw, UnitTrustCreate, UnitTrustUpdate } from '../../types';
import { portfolioKeys } from './usePortfolio';

// Query keys
export const unitTrustKeys = {
  all: ['unitTrusts'] as const,
  list: () => [...unitTrustKeys.all, 'list'] as const,
  detail: (id: number) => [...unitTrustKeys.all, 'detail', id] as const,
  withStats: (id: number) => [...unitTrustKeys.all, 'withStats', id] as const,
};

/**
 * Calculate derived fields from raw stats
 */
function enrichWithStats(raw: UnitTrustWithStatsRaw): UnitTrustWithStats {
  const total_cost = raw.total_units * raw.avg_purchase_price;
  const current_value = raw.latest_price ? raw.total_units * raw.latest_price : null;
  const gain_loss = current_value !== null ? current_value - total_cost : null;
  const gain_loss_percentage = gain_loss !== null && total_cost > 0 
    ? (gain_loss / total_cost) * 100 
    : null;

  return {
    ...raw,
    current_value,
    total_cost,
    gain_loss,
    gain_loss_percentage,
  };
}

/**
 * Fetch all unit trusts
 */
export function useUnitTrusts() {
  return useQuery<UnitTrust[]>({
    queryKey: unitTrustKeys.list(),
    queryFn: () => api.unitTrusts.list(),
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Fetch a single unit trust by ID
 */
export function useUnitTrust(id: number) {
  return useQuery<UnitTrust>({
    queryKey: unitTrustKeys.detail(id),
    queryFn: () => api.unitTrusts.get(id),
    enabled: !!id,
    staleTime: 60 * 1000,
  });
}

/**
 * Fetch a unit trust with calculated statistics
 */
export function useUnitTrustWithStats(id: number) {
  return useQuery<UnitTrustWithStats>({
    queryKey: unitTrustKeys.withStats(id),
    queryFn: async () => {
      const raw = await api.unitTrusts.getWithStats(id);
      return enrichWithStats(raw);
    },
    enabled: !!id,
    staleTime: 30 * 1000, // 30 seconds - more frequent for stats
  });
}

/**
 * Create a new unit trust
 */
export function useCreateUnitTrust() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UnitTrustCreate) => api.unitTrusts.create(data),
    onSuccess: () => {
      // Invalidate unit trust list
      queryClient.invalidateQueries({ queryKey: unitTrustKeys.list() });
    },
  });
}

/**
 * Update an existing unit trust
 */
export function useUpdateUnitTrust() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UnitTrustUpdate }) =>
      api.unitTrusts.update(id, data),
    onSuccess: (_, variables) => {
      // Invalidate specific unit trust and list
      queryClient.invalidateQueries({ queryKey: unitTrustKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: unitTrustKeys.withStats(variables.id) });
      queryClient.invalidateQueries({ queryKey: unitTrustKeys.list() });
    },
  });
}

/**
 * Delete a unit trust
 */
export function useDeleteUnitTrust() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.unitTrusts.delete(id),
    onSuccess: () => {
      // Invalidate all unit trust queries and portfolio
      queryClient.invalidateQueries({ queryKey: unitTrustKeys.all });
      queryClient.invalidateQueries({ queryKey: portfolioKeys.all });
    },
  });
}
