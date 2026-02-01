import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type { Transaction, TransactionWithFund, TransactionCreate } from '../../types';
import { portfolioKeys } from './usePortfolio';
import { unitTrustKeys } from './useUnitTrusts';

// Query keys
export const transactionKeys = {
  all: ['transactions'] as const,
  list: () => [...transactionKeys.all, 'list'] as const,
  detail: (id: number) => [...transactionKeys.all, 'detail', id] as const,
};

/**
 * Fetch all transactions
 */
export function useTransactions() {
  return useQuery<TransactionWithFund[]>({
    queryKey: transactionKeys.list(),
    queryFn: () => api.transactions.list(),
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Fetch a single transaction by ID
 */
export function useTransaction(id: number) {
  return useQuery<Transaction>({
    queryKey: transactionKeys.detail(id),
    queryFn: () => api.transactions.get(id),
    enabled: !!id,
    staleTime: 60 * 1000,
  });
}

/**
 * Create a new transaction
 */
export function useCreateTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TransactionCreate) => api.transactions.create(data),
    onSuccess: (_, variables) => {
      // Invalidate transactions list
      queryClient.invalidateQueries({ queryKey: transactionKeys.list() });
      // Invalidate the affected unit trust stats
      queryClient.invalidateQueries({ 
        queryKey: unitTrustKeys.withStats(variables.unit_trust_id) 
      });
      // Invalidate portfolio data since totals changed
      queryClient.invalidateQueries({ queryKey: portfolioKeys.all });
    },
  });
}

/**
 * Delete a transaction
 */
export function useDeleteTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.transactions.delete(id),
    onSuccess: () => {
      // Invalidate all related queries
      queryClient.invalidateQueries({ queryKey: transactionKeys.all });
      queryClient.invalidateQueries({ queryKey: unitTrustKeys.all });
      queryClient.invalidateQueries({ queryKey: portfolioKeys.all });
    },
  });
}
