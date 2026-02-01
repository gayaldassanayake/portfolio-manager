import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type { Price, PriceCreate } from '../../types';
import { portfolioKeys } from './usePortfolio';
import { unitTrustKeys } from './useUnitTrusts';

// Query keys
export const priceKeys = {
  all: ['prices'] as const,
  forFund: (unitTrustId: number) => [...priceKeys.all, 'fund', unitTrustId] as const,
};

/**
 * Fetch price history for a specific unit trust
 */
export function usePrices(unitTrustId: number) {
  return useQuery<Price[]>({
    queryKey: priceKeys.forFund(unitTrustId),
    queryFn: () => api.prices.getForFund(unitTrustId),
    enabled: !!unitTrustId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Record a new price for a unit trust
 */
export function useCreatePrice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PriceCreate) => api.prices.create(data),
    onSuccess: (_, variables) => {
      // Invalidate price history for the fund
      queryClient.invalidateQueries({ 
        queryKey: priceKeys.forFund(variables.unit_trust_id) 
      });
      // Invalidate unit trust stats (latest price changed)
      queryClient.invalidateQueries({ 
        queryKey: unitTrustKeys.withStats(variables.unit_trust_id) 
      });
      // Invalidate portfolio data
      queryClient.invalidateQueries({ queryKey: portfolioKeys.all });
    },
  });
}
