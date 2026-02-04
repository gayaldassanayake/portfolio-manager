import { useState, useMemo } from 'react';
import { motion } from 'motion/react';
import { PageHeader } from '../components/layout';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui';
import { StatCard } from '../components/features';
import { PortfolioChart } from '../components/charts';
import { usePortfolioPerformance, usePortfolioMetrics } from '../api/hooks';
import { formatCurrency, formatPercentage } from '../lib/formatters';
import styles from './Performance.module.css';

type TimeRange = 30 | 90 | 180 | 365;

export function Performance() {
  const [timeRange, setTimeRange] = useState<TimeRange>(365);
  
  const { data: performance, isLoading: perfLoading } = usePortfolioPerformance();
  const { data: metrics } = usePortfolioMetrics();

  // Transform performance data for chart - filter by time range
  const chartData = useMemo(() => {
    if (!performance?.history) return [];
    
    const now = new Date();
    const cutoffDate = new Date(now.getTime() - timeRange * 24 * 60 * 60 * 1000);
    
    return performance.history
      .filter((p) => new Date(p.date) >= cutoffDate)
      .map((p) => ({
        date: p.date,
        value: p.value,
      }));
  }, [performance, timeRange]);

  // Calculate period return from filtered chart data
  const periodReturn = useMemo(() => {
    if (chartData.length < 2) return null;
    const first = chartData[0];
    const last = chartData[chartData.length - 1];
    const change = last.value - first.value;
    const percentage = first.value > 0 ? (change / first.value) * 100 : 0;
    return { change, percentage };
  }, [chartData]);

  const timeRangeOptions: { value: TimeRange; label: string }[] = [
    { value: 30, label: '1M' },
    { value: 90, label: '3M' },
    { value: 180, label: '6M' },
    { value: 365, label: '1Y' },
  ];

  // Format percentage values (backend returns as decimals, e.g., 0.06 for 6%)
  const formatMetricPercent = (value: number | null | undefined) => {
    if (value === null || value === undefined) return '—';
    return formatPercentage(value * 100);
  };

  return (
    <div className={styles.page}>
      <PageHeader
        title="Performance"
        description="Track your portfolio's performance over time"
      />

      {/* Main Chart */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card className={styles.chartCard}>
          <CardHeader
            action={
              <div className={styles.timeRangeSelector}>
                {timeRangeOptions.map((option) => (
                  <button
                    key={option.value}
                    className={`${styles.timeRangeButton} ${timeRange === option.value ? styles.active : ''}`}
                    onClick={() => setTimeRange(option.value)}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            }
          >
            <div className={styles.chartHeader}>
              <CardTitle>Portfolio Value</CardTitle>
              {periodReturn && (
                <div className={styles.periodReturn}>
                  <span className={periodReturn.change >= 0 ? styles.positive : styles.negative}>
                    {periodReturn.change >= 0 ? '+' : ''}
                    {formatCurrency(periodReturn.change)}
                  </span>
                  <span className={`${styles.periodPercent} ${periodReturn.change >= 0 ? styles.positive : styles.negative}`}>
                    ({formatPercentage(periodReturn.percentage)})
                  </span>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {perfLoading ? (
              <div className="skeleton" style={{ height: '400px', borderRadius: 'var(--radius-md)' }} />
            ) : chartData.length > 0 ? (
              <PortfolioChart data={chartData} height={400} />
            ) : (
              <div className={styles.noData}>
                <p>No performance data available</p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Returns Section - Four Key Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Returns</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={styles.returnsGrid}>
              <div className={styles.returnItem}>
                <span className={styles.returnLabel}>Net Return</span>
                <span className={`${styles.returnValue} ${metrics && metrics.net_return >= 0 ? styles.positive : styles.negative}`}>
                  {formatMetricPercent(metrics?.net_return)}
                </span>
                <span className={styles.returnDescription}>
                  Total return including realized gains
                </span>
              </div>
              <div className={styles.returnItem}>
                <span className={styles.returnLabel}>Unrealized ROI</span>
                <span className={`${styles.returnValue} ${metrics && metrics.unrealized_roi >= 0 ? styles.positive : styles.negative}`}>
                  {formatMetricPercent(metrics?.unrealized_roi)}
                </span>
                <span className={styles.returnDescription}>
                  Current holdings vs cost basis (FIFO)
                </span>
              </div>
              <div className={styles.returnItem}>
                <span className={styles.returnLabel}>Time-Weighted Return</span>
                <span className={`${styles.returnValue} ${metrics && (metrics.twr_annualized ?? 0) >= 0 ? styles.positive : styles.negative}`}>
                  {metrics?.twr_annualized != null ? formatMetricPercent(metrics.twr_annualized) : '—'}
                </span>
                <span className={styles.returnDescription}>
                  Annualized investment performance
                </span>
              </div>
              <div className={styles.returnItem}>
                <span className={styles.returnLabel}>Money-Weighted Return</span>
                <span className={`${styles.returnValue} ${metrics && (metrics.mwr_annualized ?? 0) >= 0 ? styles.positive : styles.negative}`}>
                  {metrics?.mwr_annualized != null ? formatMetricPercent(metrics.mwr_annualized) : '—'}
                </span>
                <span className={styles.returnDescription}>
                  Annualized personal return (IRR)
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Risk & Volatility Metrics */}
      <section className={styles.metricsGrid}>
        <StatCard
          label="Daily Return"
          value={formatMetricPercent(metrics?.daily_return)}
          delay={0}
        />
        <StatCard
          label="Volatility"
          value={formatMetricPercent(metrics?.volatility)}
          delay={1}
        />
        <StatCard
          label="Sharpe Ratio"
          value={metrics?.sharpe_ratio != null ? metrics.sharpe_ratio.toFixed(2) : '—'}
          delay={2}
        />
        <StatCard
          label="Max Drawdown"
          value={formatMetricPercent(metrics?.max_drawdown)}
          delay={3}
        />
        <StatCard
          label="Best Day"
          value={metrics?.best_day != null ? formatMetricPercent(metrics.best_day) : '—'}
          delay={4}
        />
        <StatCard
          label="Worst Day"
          value={metrics?.worst_day != null ? formatMetricPercent(metrics.worst_day) : '—'}
          delay={5}
        />
      </section>
    </div>
  );
}
