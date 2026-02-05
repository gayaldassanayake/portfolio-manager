import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type {
  FixedDepositWithValue,
  FixedDepositCreate,
  FixedDepositUpdate,
  InterestCalculationRequest,
} from '../../types';

// Query keys
export const fixedDepositKeys = {
  all: ['fixedDeposits'] as const,
  list: (filters?: { status?: string; institution?: string }) =>
    [...fixedDepositKeys.all, 'list', filters] as const,
  detail: (id: number) => [...fixedDepositKeys.all, 'detail', id] as const,
};

/**
 * Fetch all fixed deposits with optional filters
 */
export function useFixedDeposits(filters?: { status?: string; institution?: string }) {
  return useQuery<FixedDepositWithValue[]>({
    queryKey: fixedDepositKeys.list(filters),
    queryFn: () => api.fixedDeposits.list(filters),
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Fetch a single fixed deposit by ID
 */
export function useFixedDeposit(id: number) {
  return useQuery<FixedDepositWithValue>({
    queryKey: fixedDepositKeys.detail(id),
    queryFn: () => api.fixedDeposits.get(id),
    enabled: !!id,
    staleTime: 30 * 1000,
  });
}

/**
 * Create a new fixed deposit
 */
export function useCreateFixedDeposit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: FixedDepositCreate) => api.fixedDeposits.create(data),
    onSuccess: () => {
      // Invalidate all fixed deposit lists
      queryClient.invalidateQueries({ queryKey: fixedDepositKeys.all });
    },
  });
}

/**
 * Update an existing fixed deposit
 */
export function useUpdateFixedDeposit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: FixedDepositUpdate }) =>
      api.fixedDeposits.update(id, data),
    onSuccess: (_, variables) => {
      // Invalidate specific fixed deposit and all lists
      queryClient.invalidateQueries({ queryKey: fixedDepositKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: fixedDepositKeys.all });
    },
  });
}

/**
 * Delete a fixed deposit
 */
export function useDeleteFixedDeposit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.fixedDeposits.delete(id),
    onSuccess: () => {
      // Invalidate all fixed deposit queries
      queryClient.invalidateQueries({ queryKey: fixedDepositKeys.all });
    },
  });
}

/**
 * Calculate interest for given parameters (utility, does not mutate state)
 */
export function useCalculateInterest() {
  return useMutation({
    mutationFn: (data: InterestCalculationRequest) => api.fixedDeposits.calculateInterest(data),
  });
}
