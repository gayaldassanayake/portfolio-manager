// ============================================
// API Response Types - Portfolio Management
// Aligned with actual backend responses
// ============================================

// Unit Trust (Fund) types
export interface UnitTrust {
  id: number;
  name: string;
  symbol: string;
  description: string | null;
  created_at: string;
}

// Backend returns this structure for /unit-trusts/:id/with-stats
export interface UnitTrustWithStatsRaw {
  id: number;
  name: string;
  symbol: string;
  description: string | null;
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
}

export interface UnitTrustUpdate {
  name?: string;
  symbol?: string;
  description?: string;
}

// Transaction types
export type TransactionType = 'buy' | 'sell';

// Backend transaction response (flattened format)
export interface Transaction {
  id: number;
  unit_trust_id: number;
  units: number;
  price_per_unit: number;
  transaction_date: string;
  created_at: string;
  unit_trust_name: string;
  unit_trust_symbol: string;
}

// For frontend display, we create a nested structure
export interface TransactionWithFund {
  id: number;
  unit_trust_id: number;
  units: number;
  price_per_unit: number;
  transaction_date: string;
  created_at: string;
  notes?: string | null;
  transaction_type: TransactionType;
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
  price_per_unit: number;
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

// Portfolio types - matching actual backend response
export interface PortfolioSummary {
  total_invested: number;
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
  annualized_return: number;
  max_drawdown: number;
  sharpe_ratio: number | null;
  // Placeholders for future backend implementation
  best_day?: number | null;
  worst_day?: number | null;
  total_return?: number | null;
  total_return_percentage?: number | null;
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
