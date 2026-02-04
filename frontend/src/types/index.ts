// ============================================
// API Response Types - Portfolio Management
// Aligned with actual backend responses
// ============================================

// Unit Trust (Fund) types
export type Provider = 'yahoo' | 'cal';

export interface UnitTrust {
  id: number;
  name: string;
  symbol: string;
  description: string | null;
  provider: Provider | null;
  provider_symbol: string | null;
  created_at: string;
}

// Backend returns this structure for /unit-trusts/:id/with-stats
export interface UnitTrustWithStatsRaw {
  id: number;
  name: string;
  symbol: string;
  description: string | null;
  provider: Provider | null;
  provider_symbol: string | null;
  created_at: string;
  total_units: number;
  avg_purchase_price: number;
  latest_price: number | null;
}

// Extended with calculated fields for frontend use
export interface UnitTrustWithStats extends UnitTrustWithStatsRaw {
  current_value: number | null;
  total_cost: number;
  gain_loss: number | null;
  gain_loss_percentage: number | null;
}

export interface UnitTrustCreate {
  name: string;
  symbol: string;
  description?: string;
  provider?: Provider | null;
  provider_symbol?: string | null;
}

export interface UnitTrustUpdate {
  name?: string;
  symbol?: string;
  description?: string;
  provider?: Provider | null;
  provider_symbol?: string | null;
}

// Transaction types
export type TransactionType = 'buy' | 'sell';

// Backend transaction response (flattened format with transaction_type and notes)
export interface Transaction {
  id: number;
  unit_trust_id: number;
  transaction_type: TransactionType;
  units: number;
  price_per_unit: number;
  transaction_date: string;
  notes: string | null;
  created_at: string;
  unit_trust_name: string;
  unit_trust_symbol: string;
}

// For frontend display, we create a nested structure
export interface TransactionWithFund {
  id: number;
  unit_trust_id: number;
  transaction_type: TransactionType;
  units: number;
  price_per_unit: number;
  transaction_date: string;
  notes: string | null;
  created_at: string;
  unit_trust: {
    id: number;
    name: string;
    symbol: string;
  };
}

export interface TransactionCreate {
  unit_trust_id: number;
  transaction_type: TransactionType;
  units: number;
  transaction_date: string;
  notes?: string;
}

// Price types
export interface Price {
  id: number;
  unit_trust_id: number;
  price: number;
  date: string;
  created_at: string;
}

export interface PriceCreate {
  unit_trust_id: number;
  price: number;
  date: string;
}

// Price fetch result types
export interface PriceFetchResult {
  unit_trust_id: number;
  symbol: string;
  provider: string;
  prices_fetched: number;
  prices_saved: number;
  prices: Price[];
}

export interface PriceFetchError {
  unit_trust_id: number;
  symbol: string;
  provider: string | null;
  error: string;
}

export interface BulkPriceFetchResponse {
  total_requested: number;
  successful: number;
  failed: number;
  results: PriceFetchResult[];
  errors: PriceFetchError[];
}

// Portfolio types - matching actual backend response
export interface PortfolioSummary {
  total_invested: number;
  total_withdrawn: number;
  current_value: number;
  total_gain_loss: number;
  roi_percentage: number;
  total_units: number;
  holding_count: number;
}

// Single history point
export interface PortfolioHistoryPoint {
  date: string;
  value: number;
}

// Full performance response from /portfolio/performance
export interface PortfolioPerformanceResponse {
  summary: PortfolioSummary;
  metrics: PerformanceMetrics;
  history: PortfolioHistoryPoint[];
}

// Metrics from backend
export interface PerformanceMetrics {
  daily_return: number;
  volatility: number;
  max_drawdown: number;
  sharpe_ratio: number | null;
  net_return: number;
  unrealized_roi: number;
  twr_annualized: number | null;
  mwr_annualized: number | null;
  best_day: number | null;
  worst_day: number | null;
}

// ============================================
// Frontend-specific Types
// ============================================

// Navigation
export interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

// Chart data
export interface ChartDataPoint {
  date: string;
  value: number;
  label?: string;
}

// Table sorting
export type SortDirection = 'asc' | 'desc';

export interface SortConfig {
  key: string;
  direction: SortDirection;
}

// Filter state
export interface TransactionFilters {
  search: string;
  type: TransactionType | 'all';
  fundId: number | null;
  dateFrom: string | null;
  dateTo: string | null;
}

// Form states
export interface FormError {
  field: string;
  message: string;
}

// Modal state
export interface ModalState {
  isOpen: boolean;
  type: 'add' | 'edit' | 'delete' | null;
  data?: unknown;
}

// Toast notifications
export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}
