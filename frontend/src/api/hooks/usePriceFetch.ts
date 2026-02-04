import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type { PriceFetchResult, BulkPriceFetchResponse } from '../../types';
import { unitTrustKeys } from './useUnitTrusts';
import { priceKeys } from './usePrices';

/**
 * Fetch prices from provider for a single unit trust
 */
export function useFetchPrices() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      unitTrustId,
      startDate,
      endDate,
    }: {
      unitTrustId: number;
      startDate?: string;
      endDate?: string;
    }) => api.prices.fetchForFund(unitTrustId, startDate, endDate),
    onSuccess: (data: PriceFetchResult) => {
      // Invalidate prices for this specific fund
      queryClient.invalidateQueries({
        queryKey: priceKeys.forFund(data.unit_trust_id),
      });
      // Invalidate unit trust stats (to update latest price)
      queryClient.invalidateQueries({
        queryKey: unitTrustKeys.withStats(data.unit_trust_id),
      });
    },
  });
}

/**
 * Bulk fetch prices for multiple unit trusts
 */
export function useBulkFetchPrices() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      unitTrustIds,
      startDate,
      endDate,
    }: {
      unitTrustIds?: number[];
      startDate?: string;
      endDate?: string;
    }) => api.prices.fetchBulk(unitTrustIds, startDate, endDate),
    onSuccess: (data: BulkPriceFetchResponse) => {
      // Invalidate prices for all successful fetches
      data.results.forEach((result) => {
        queryClient.invalidateQueries({
          queryKey: priceKeys.forFund(result.unit_trust_id),
        });
        queryClient.invalidateQueries({
          queryKey: unitTrustKeys.withStats(result.unit_trust_id),
        });
      });
      // Also invalidate the unit trust list to refresh any displayed data
      queryClient.invalidateQueries({ queryKey: unitTrustKeys.list() });
    },
  });
}
