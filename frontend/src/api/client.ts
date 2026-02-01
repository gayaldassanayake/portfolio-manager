// ============================================
// API Client - Portfolio Management
// ============================================

import type {
  UnitTrust,
  UnitTrustWithStatsRaw,
  UnitTrustCreate,
  UnitTrustUpdate,
  Transaction,
  TransactionCreate,
  TransactionWithFund,
  Price,
  PriceCreate,
  PortfolioSummary,
  PortfolioPerformanceResponse,
  PortfolioHistoryPoint,
  PerformanceMetrics,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  public status: number;
  public data?: unknown;
  
  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Request options type
 */
interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  params?: Record<string, string | number | boolean | null | undefined>;
}

/**
 * Build URL with query parameters
 */
function buildUrl(
  endpoint: string,
  params?: Record<string, string | number | boolean | null | undefined>
): string {
  const url = new URL(`${API_BASE_URL}${endpoint}`);
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        url.searchParams.append(key, String(value));
      }
    });
  }
  
  return url.toString();
}

/**
 * Generic fetch wrapper with error handling
 */
async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { body, params, headers: customHeaders, ...restOptions } = options;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...customHeaders,
  };

  const config: RequestInit = {
    ...restOptions,
    headers,
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  const url = buildUrl(endpoint, params);
  
  const response = await fetch(url, config);

  // Handle non-JSON responses
  const contentType = response.headers.get('content-type');
  const isJson = contentType?.includes('application/json');

  if (!response.ok) {
    const errorData = isJson ? await response.json() : await response.text();
    throw new ApiError(
      errorData.detail || errorData.message || 'An error occurred',
      response.status,
      errorData
    );
  }

  // Return empty object for 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return isJson ? response.json() : (response.text() as Promise<T>);
}

// ============================================
// API Methods
// ============================================

export const api = {
  // Unit Trusts
  unitTrusts: {
    list: () => 
      request<UnitTrust[]>('/unit-trusts'),
    
    get: (id: number) => 
      request<UnitTrust>(`/unit-trusts/${id}`),
    
    getWithStats: (id: number) => 
      request<UnitTrustWithStatsRaw>(`/unit-trusts/${id}/with-stats`),
    
    create: (data: UnitTrustCreate) => 
      request<UnitTrust>('/unit-trusts', {
        method: 'POST',
        body: data,
      }),
    
    update: (id: number, data: UnitTrustUpdate) => 
      request<UnitTrust>(`/unit-trusts/${id}`, {
        method: 'PUT',
        body: data,
      }),
    
    delete: (id: number) => 
      request<void>(`/unit-trusts/${id}`, {
        method: 'DELETE',
      }),
  },

  // Transactions - backend returns flattened format, we transform to nested
  transactions: {
    list: async (): Promise<TransactionWithFund[]> => {
      const data = await request<Transaction[]>('/transactions');
      // Transform flattened backend response to nested format
      return data.map((tx) => ({
        id: tx.id,
        unit_trust_id: tx.unit_trust_id,
        units: tx.units,
        price_per_unit: tx.price_per_unit,
        transaction_date: tx.transaction_date,
        created_at: tx.created_at,
        notes: null,
        // Backend doesn't return transaction_type, we infer from context or default to 'buy'
        transaction_type: 'buy' as const,
        unit_trust: {
          id: tx.unit_trust_id,
          name: tx.unit_trust_name,
          symbol: tx.unit_trust_symbol,
        },
      }));
    },
    
    get: (id: number) => 
      request<Transaction>(`/transactions/${id}`),
    
    create: (data: TransactionCreate) => 
      request<Transaction>('/transactions', {
        method: 'POST',
        body: data,
      }),
    
    delete: (id: number) => 
      request<void>(`/transactions/${id}`, {
        method: 'DELETE',
      }),
  },

  // Prices
  prices: {
    getForFund: (unitTrustId: number) => 
      request<Price[]>('/prices', {
        params: { unit_trust_id: unitTrustId },
      }),
    
    create: (data: PriceCreate) => 
      request<Price>('/prices', {
        method: 'POST',
        body: data,
      }),
  },

  // Portfolio
  portfolio: {
    getSummary: () => 
      request<PortfolioSummary>('/portfolio/summary'),
    
    // Returns the full performance object with summary, metrics, and history
    getPerformance: () => 
      request<PortfolioPerformanceResponse>('/portfolio/performance'),
    
    // Returns array of history points
    getHistory: () => 
      request<PortfolioHistoryPoint[]>('/portfolio/history'),
    
    getMetrics: () => 
      request<PerformanceMetrics>('/portfolio/metrics'),
  },
};

export default api;
