import { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { formatCurrency } from '../../lib/formatters';
import styles from './PortfolioChart.module.css';

interface DataPoint {
  date: string;
  value: number;
}

interface PortfolioChartProps {
  data: DataPoint[];
  height?: number;
  showGrid?: boolean;
  showAxis?: boolean;
  gradient?: boolean;
  className?: string;
}

export function PortfolioChart({
  data,
  height = 300,
  showGrid = true,
  showAxis = true,
  gradient = true,
  className,
}: PortfolioChartProps) {
  const chartData = useMemo(() => {
    return data.map((point) => ({
      ...point,
      formattedDate: format(parseISO(point.date), 'MMM d'),
      fullDate: format(parseISO(point.date), 'MMM d, yyyy'),
    }));
  }, [data]);

  const { minValue, maxValue, isPositive } = useMemo(() => {
    if (chartData.length === 0) return { minValue: 0, maxValue: 0, isPositive: true };
    const values = chartData.map((d) => d.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const first = chartData[0].value;
    const last = chartData[chartData.length - 1].value;
    return {
      minValue: min * 0.98,
      maxValue: max * 1.02,
      isPositive: last >= first,
    };
  }, [chartData]);

  const gradientId = `portfolio-gradient-${isPositive ? 'positive' : 'negative'}`;
  const strokeColor = isPositive ? 'var(--color-positive)' : 'var(--color-negative)';
  const fillColor = isPositive ? 'var(--color-positive)' : 'var(--color-negative)';

  if (chartData.length === 0) {
    return (
      <div className={styles.empty}>
        <p>No data available</p>
      </div>
    );
  }

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
          margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={fillColor} stopOpacity={0.2} />
              <stop offset="100%" stopColor={fillColor} stopOpacity={0} />
            </linearGradient>
          </defs>
          
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--color-surface-border)"
              vertical={false}
            />
          )}
          
          {showAxis && (
            <>
              <XAxis
                dataKey="formattedDate"
                axisLine={false}
                tickLine={false}
                tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }}
                dy={10}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={[minValue, maxValue]}
                axisLine={false}
                tickLine={false}
                tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }}
                tickFormatter={(value) => formatCurrency(value, { compact: true })}
                width={70}
              />
            </>
          )}
          
          <Tooltip
            content={<CustomTooltip />}
            cursor={{
              stroke: 'var(--color-text-muted)',
              strokeWidth: 1,
              strokeDasharray: '4 4',
            }}
          />
          
          <Area
            type="monotone"
            dataKey="value"
            stroke={strokeColor}
            strokeWidth={2}
            fill={gradient ? `url(#${gradientId})` : 'transparent'}
            animationDuration={1000}
            animationEasing="ease-out"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// Custom tooltip component
function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: DataPoint & { fullDate: string } }> }) {
  if (!active || !payload || payload.length === 0) return null;

  const data = payload[0].payload;
  
  return (
    <div className={styles.tooltip}>
      <span className={styles.tooltipDate}>{data.fullDate}</span>
      <span className={styles.tooltipValue}>{formatCurrency(data.value)}</span>
    </div>
  );
}

// Mini sparkline version for tables
interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  positive?: boolean;
}

export function Sparkline({ data, width = 80, height = 24, positive }: SparklineProps) {
  const isPositiveTrend = positive ?? (data.length > 1 && data[data.length - 1] >= data[0]);
  const color = isPositiveTrend ? 'var(--color-positive)' : 'var(--color-negative)';
  
  const chartData = data.map((value, index) => ({ value, index }));
  
  return (
    <div style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
          <defs>
            <linearGradient id={`sparkline-${isPositiveTrend}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.3} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.5}
            fill={`url(#sparkline-${isPositiveTrend})`}
            animationDuration={500}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
