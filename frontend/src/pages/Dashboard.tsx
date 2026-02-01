import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { PageHeader } from '../components/layout';
import { Card, CardHeader, CardTitle, CardContent, Button } from '../components/ui';
import { HeroStat, StatCard } from '../components/features';
import { PortfolioChart, Sparkline } from '../components/charts';
import { usePortfolioSummary, usePortfolioPerformance, useUnitTrusts } from '../api/hooks';
import { formatCurrency, formatPercentage } from '../lib/formatters';
import styles from './Dashboard.module.css';

export function Dashboard() {
  const { data: summary, isLoading: summaryLoading } = usePortfolioSummary();
  const { data: performance, isLoading: perfLoading } = usePortfolioPerformance();
  const { data: unitTrusts } = useUnitTrusts();

  // Transform performance data for chart - extract history from the performance response
  const chartData = useMemo(() => {
    if (!performance?.history) return [];
    return performance.history.map((p) => ({
      date: p.date,
      value: p.value,
    }));
  }, [performance]);

  // Get change type from summary
  const changeType = useMemo(() => {
    if (!summary) return 'neutral';
    return summary.total_gain_loss >= 0 ? 'positive' : 'negative';
  }, [summary]);

  return (
    <div className={styles.page}>
      <PageHeader
        title="Dashboard"
        description="Your portfolio at a glance"
      />

      {/* Hero Section - Total Portfolio Value */}
      <section className={styles.heroSection}>
        {summaryLoading ? (
          <div className={styles.heroSkeleton}>
            <div className="skeleton" style={{ width: '120px', height: '16px', marginBottom: '12px' }} />
            <div className="skeleton" style={{ width: '280px', height: '48px', marginBottom: '16px' }} />
            <div className="skeleton" style={{ width: '200px', height: '20px' }} />
          </div>
        ) : summary ? (
          <HeroStat
            label="Total Portfolio Value"
            value={formatCurrency(summary.current_value)}
            change={{
              amount: formatCurrency(summary.total_gain_loss),
              percentage: formatPercentage(summary.roi_percentage),
              type: changeType as 'positive' | 'negative' | 'neutral',
            }}
          />
        ) : null}
      </section>

      {/* Stats Grid */}
      <section className={styles.statsGrid}>
        <StatCard
          label="Total Invested"
          value={summary ? formatCurrency(summary.total_invested) : '—'}
          delay={1}
          icon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 1V15M12 4H6C4.89543 4 4 4.89543 4 6C4 7.10457 4.89543 8 6 8H10C11.1046 8 12 8.89543 12 10C12 11.1046 11.1046 12 10 12H4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          }
        />
        <StatCard
          label="Total Gain/Loss"
          value={summary ? formatCurrency(summary.total_gain_loss) : '—'}
          change={summary ? {
            value: formatPercentage(summary.roi_percentage),
            type: summary.total_gain_loss >= 0 ? 'positive' : 'negative',
          } : undefined}
          delay={2}
        />
        <StatCard
          label="Holdings"
          value={summary ? String(summary.holding_count) : '—'}
          delay={3}
          icon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
              <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
              <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
              <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          }
        />
        <StatCard
          label="Total Units"
          value={summary ? summary.total_units.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}
          delay={4}
        />
      </section>

      {/* Main Content Grid */}
      <div className={styles.contentGrid}>
        {/* Performance Chart */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <Card className={styles.chartCard}>
            <CardHeader
              action={
                <Link to="/performance">
                  <Button variant="ghost" size="sm">
                    View Details
                  </Button>
                </Link>
              }
            >
              <CardTitle>Portfolio Performance</CardTitle>
            </CardHeader>
            <CardContent>
              {perfLoading ? (
                <div className="skeleton" style={{ height: '240px', borderRadius: 'var(--radius-md)' }} />
              ) : (
                <PortfolioChart data={chartData} height={240} />
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Holdings Preview */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Card className={styles.holdingsCard}>
            <CardHeader
              action={
                <Link to="/holdings">
                  <Button variant="ghost" size="sm">
                    View All
                  </Button>
                </Link>
              }
            >
              <CardTitle>Holdings</CardTitle>
            </CardHeader>
            <CardContent>
              {unitTrusts && unitTrusts.length > 0 ? (
                <div className={styles.holdingsList}>
                  {unitTrusts.slice(0, 5).map((fund, index) => (
                    <Link
                      key={fund.id}
                      to={`/holdings/${fund.id}`}
                      className={styles.holdingItem}
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      <div className={styles.holdingInfo}>
                        <span className={styles.holdingSymbol}>{fund.symbol}</span>
                        <span className={styles.holdingName}>{fund.name}</span>
                      </div>
                      <div className={styles.holdingChart}>
                        <Sparkline data={[100, 105, 103, 108, 106, 112, 115]} />
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className={styles.emptyState}>
                  <p>No holdings yet</p>
                  <Link to="/transactions">
                    <Button size="sm">Add Transaction</Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.section
        className={styles.quickActions}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.4 }}
      >
        <Card padding="lg">
          <div className={styles.actionsContent}>
            <div className={styles.actionsText}>
              <h3 className={styles.actionsTitle}>Quick Actions</h3>
              <p className={styles.actionsDescription}>
                Record a new transaction or view your complete history
              </p>
            </div>
            <div className={styles.actionsButtons}>
              <Link to="/transactions?action=add">
                <Button>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                  Add Transaction
                </Button>
              </Link>
              <Link to="/transactions">
                <Button variant="secondary">View History</Button>
              </Link>
            </div>
          </div>
        </Card>
      </motion.section>
    </div>
  );
}
