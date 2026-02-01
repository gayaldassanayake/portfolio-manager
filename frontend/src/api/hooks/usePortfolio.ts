import { useQuery } from '@tanstack/react-query';
import { api } from '../client';
import type { 
  PortfolioSummary, 
  PortfolioPerformanceResponse, 
  PortfolioHistoryPoint, 
  PerformanceMetrics 
} from '../../types';

// Query keys
export const portfolioKeys = {
  all: ['portfolio'] as const,
  summary: () => [...portfolioKeys.all, 'summary'] as const,
  performance: () => [...portfolioKeys.all, 'performance'] as const,
  history: () => [...portfolioKeys.all, 'history'] as const,
  metrics: () => [...portfolioKeys.all, 'metrics'] as const,
};

/**
 * Fetch portfolio summary
 */
export function usePortfolioSummary() {
  return useQuery<PortfolioSummary>({
    queryKey: portfolioKeys.summary(),
    queryFn: () => api.portfolio.getSummary(),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  });
}

/**
 * Fetch portfolio performance (includes summary, metrics, and history)
 * This is the main endpoint that returns everything
 */
export function usePortfolioPerformance() {
  return useQuery<PortfolioPerformanceResponse>({
    queryKey: portfolioKeys.performance(),
    queryFn: () => api.portfolio.getPerformance(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Fetch portfolio history (array of date/value points)
 */
export function usePortfolioHistory() {
  return useQuery<PortfolioHistoryPoint[]>({
    queryKey: portfolioKeys.history(),
    queryFn: () => api.portfolio.getHistory(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Fetch portfolio performance metrics
 */
export function usePortfolioMetrics() {
  return useQuery<PerformanceMetrics>({
    queryKey: portfolioKeys.metrics(),
    queryFn: () => api.portfolio.getMetrics(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
