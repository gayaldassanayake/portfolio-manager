import { format, formatDistanceToNow, parseISO, isValid } from 'date-fns';

// ============================================
// Number Formatters
// ============================================

/**
 * Format a number as currency (default: MYR)
 */
export function formatCurrency(
  value: number | null | undefined,
  options: {
    currency?: string;
    minimumFractionDigits?: number;
    maximumFractionDigits?: number;
    compact?: boolean;
  } = {}
): string {
  if (value === null || value === undefined) return '—';
  
  const {
    currency = 'MYR',
    minimumFractionDigits = 2,
    maximumFractionDigits = 2,
    compact = false,
  } = options;

  if (compact && Math.abs(value) >= 1000) {
    const formatter = new Intl.NumberFormat('en-MY', {
      style: 'currency',
      currency,
      notation: 'compact',
      maximumFractionDigits: 1,
    });
    return formatter.format(value);
  }

  const formatter = new Intl.NumberFormat('en-MY', {
    style: 'currency',
    currency,
    minimumFractionDigits,
    maximumFractionDigits,
  });

  return formatter.format(value);
}

/**
 * Format a number with thousand separators
 */
export function formatNumber(
  value: number | null | undefined,
  options: {
    minimumFractionDigits?: number;
    maximumFractionDigits?: number;
    compact?: boolean;
  } = {}
): string {
  if (value === null || value === undefined) return '—';

  const {
    minimumFractionDigits = 0,
    maximumFractionDigits = 2,
    compact = false,
  } = options;

  const formatter = new Intl.NumberFormat('en-MY', {
    minimumFractionDigits,
    maximumFractionDigits,
    notation: compact ? 'compact' : 'standard',
  });

  return formatter.format(value);
}

/**
 * Format a percentage value
 */
export function formatPercentage(
  value: number | null | undefined,
  options: {
    minimumFractionDigits?: number;
    maximumFractionDigits?: number;
    showSign?: boolean;
  } = {}
): string {
  if (value === null || value === undefined) return '—';

  const {
    minimumFractionDigits = 2,
    maximumFractionDigits = 2,
    showSign = true,
  } = options;

  const formatter = new Intl.NumberFormat('en-MY', {
    minimumFractionDigits,
    maximumFractionDigits,
    signDisplay: showSign ? 'exceptZero' : 'auto',
  });

  return `${formatter.format(value)}%`;
}

/**
 * Format units (shares/units of funds)
 */
export function formatUnits(
  value: number | null | undefined,
  decimals: number = 4
): string {
  if (value === null || value === undefined) return '—';

  return formatNumber(value, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Format price per unit
 */
export function formatPrice(
  value: number | null | undefined,
  decimals: number = 4
): string {
  if (value === null || value === undefined) return '—';

  return formatCurrency(value, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

// ============================================
// Date Formatters
// ============================================

/**
 * Format a date string to display format
 */
export function formatDate(
  date: string | Date | null | undefined,
  formatStr: string = 'MMM d, yyyy'
): string {
  if (!date) return '—';

  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  
  if (!isValid(dateObj)) return '—';

  return format(dateObj, formatStr);
}

/**
 * Format date with time
 */
export function formatDateTime(
  date: string | Date | null | undefined
): string {
  return formatDate(date, 'MMM d, yyyy HH:mm');
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(
  date: string | Date | null | undefined
): string {
  if (!date) return '—';

  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  
  if (!isValid(dateObj)) return '—';

  return formatDistanceToNow(dateObj, { addSuffix: true });
}

/**
 * Format date for input fields (YYYY-MM-DD)
 */
export function formatDateForInput(
  date: string | Date | null | undefined
): string {
  if (!date) return '';

  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  
  if (!isValid(dateObj)) return '';

  return format(dateObj, 'yyyy-MM-dd');
}

/**
 * Format date for API requests
 */
export function formatDateForApi(
  date: string | Date | null | undefined
): string | null {
  if (!date) return null;

  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  
  if (!isValid(dateObj)) return null;

  return format(dateObj, 'yyyy-MM-dd');
}

// ============================================
// Display Helpers
// ============================================

/**
 * Get color class based on positive/negative value
 */
export function getValueColorClass(value: number | null | undefined): string {
  if (value === null || value === undefined || value === 0) {
    return 'text-secondary';
  }
  return value > 0 ? 'text-positive' : 'text-negative';
}

/**
 * Get background color class based on positive/negative value
 */
export function getValueBgClass(value: number | null | undefined): string {
  if (value === null || value === undefined || value === 0) {
    return '';
  }
  return value > 0 ? 'bg-positive' : 'bg-negative';
}

/**
 * Format gain/loss with color indicator
 */
export function formatGainLoss(
  value: number | null | undefined,
  percentage?: number | null
): { text: string; color: string; sign: string } {
  if (value === null || value === undefined) {
    return { text: '—', color: 'text-secondary', sign: '' };
  }

  const sign = value >= 0 ? '+' : '';
  const color = value >= 0 ? 'text-positive' : 'text-negative';
  
  let text = `${sign}${formatCurrency(value)}`;
  
  if (percentage !== null && percentage !== undefined) {
    text += ` (${formatPercentage(percentage)})`;
  }

  return { text, color, sign };
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 3)}...`;
}

/**
 * Format transaction type for display
 */
export function formatTransactionType(type: 'buy' | 'sell'): string {
  return type.charAt(0).toUpperCase() + type.slice(1);
}
