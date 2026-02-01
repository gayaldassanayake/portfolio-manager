import { useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { PageHeader } from '../components/layout';
import { Card, CardHeader, CardTitle, CardContent, Button } from '../components/ui';
import { StatCard } from '../components/features';
import { PortfolioChart } from '../components/charts';
import { useUnitTrustWithStats, usePrices, useTransactions } from '../api/hooks';
import { formatCurrency, formatUnits, formatPercentage, formatDate } from '../lib/formatters';
import styles from './FundDetails.module.css';

export function FundDetails() {
  const { id } = useParams<{ id: string }>();
  const fundId = Number(id);

  const { data: fund, isLoading: fundLoading } = useUnitTrustWithStats(fundId);
  const { data: prices, isLoading: pricesLoading } = usePrices(fundId);
  const { data: allTransactions } = useTransactions();

  // Filter transactions for this fund
  const fundTransactions = useMemo(() => {
    if (!allTransactions) return [];
    return allTransactions
      .filter((t) => t.unit_trust_id === fundId)
      .sort((a, b) => new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime())
      .slice(0, 5);
  }, [allTransactions, fundId]);

  // Transform prices for chart
  const chartData = useMemo(() => {
    if (!prices) return [];
    return prices
      .map((p) => ({ date: p.date, value: p.price }))
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [prices]);

  const changeType = useMemo(() => {
    if (!fund || fund.gain_loss === null) return 'neutral';
    return fund.gain_loss >= 0 ? 'positive' : 'negative';
  }, [fund]);

  if (fundLoading) {
    return (
      <div className={styles.page}>
        <div className="skeleton" style={{ width: '200px', height: '32px', marginBottom: '24px' }} />
        <div className="skeleton" style={{ height: '400px', borderRadius: 'var(--radius-lg)' }} />
      </div>
    );
  }

  if (!fund) {
    return (
      <div className={styles.page}>
        <div className={styles.notFound}>
          <h2>Fund not found</h2>
          <p>The fund you're looking for doesn't exist.</p>
          <Link to="/holdings">
            <Button>Back to Holdings</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <PageHeader
        title={fund.symbol}
        description={fund.name}
        action={
          <Link to="/transactions?action=add">
            <Button>Add Transaction</Button>
          </Link>
        }
      />

      {/* Stats Grid */}
      <section className={styles.statsGrid}>
        <StatCard
          label="Current Value"
          value={formatCurrency(fund.current_value)}
          delay={0}
        />
        <StatCard
          label="Total Units"
          value={formatUnits(fund.total_units)}
          delay={1}
        />
        <StatCard
          label="Avg Purchase Price"
          value={formatCurrency(fund.avg_purchase_price, { maximumFractionDigits: 4 })}
          delay={2}
        />
        <StatCard
          label="Latest Price"
          value={formatCurrency(fund.latest_price, { maximumFractionDigits: 4 })}
          delay={3}
        />
        <StatCard
          label="Total Cost"
          value={formatCurrency(fund.total_cost)}
          delay={4}
        />
        <StatCard
          label="Gain/Loss"
          value={formatCurrency(fund.gain_loss)}
          change={fund.gain_loss_percentage !== null ? {
            value: formatPercentage(fund.gain_loss_percentage),
            type: changeType as 'positive' | 'negative' | 'neutral',
          } : undefined}
          delay={5}
        />
      </section>

      {/* Main Content */}
      <div className={styles.contentGrid}>
        {/* Price History Chart */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <Card className={styles.chartCard}>
            <CardHeader>
              <CardTitle>Price History</CardTitle>
            </CardHeader>
            <CardContent>
              {pricesLoading ? (
                <div className="skeleton" style={{ height: '300px', borderRadius: 'var(--radius-md)' }} />
              ) : chartData.length > 0 ? (
                <PortfolioChart data={chartData} height={300} />
              ) : (
                <div className={styles.noData}>
                  <p>No price history available</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Recent Transactions */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Card className={styles.transactionsCard}>
            <CardHeader
              action={
                <Link to={`/transactions?fund=${fundId}`}>
                  <Button variant="ghost" size="sm">View All</Button>
                </Link>
              }
            >
              <CardTitle>Recent Transactions</CardTitle>
            </CardHeader>
            <CardContent>
              {fundTransactions.length > 0 ? (
                <div className={styles.transactionsList}>
                  {fundTransactions.map((tx) => (
                    <div key={tx.id} className={styles.transactionItem}>
                      <div className={styles.txInfo}>
                        <span className={styles.txDate}>
                          {formatDate(tx.transaction_date)}
                        </span>
                      </div>
                      <div className={styles.txDetails}>
                        <span className={styles.txUnits}>
                          {formatUnits(tx.units)} units
                        </span>
                        <span className={styles.txPrice}>
                          @ {formatCurrency(tx.price_per_unit, { maximumFractionDigits: 4 })}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className={styles.noData}>
                  <p>No transactions yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Fund Info */}
      {fund.description && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.4 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>About</CardTitle>
            </CardHeader>
            <CardContent>
              <p className={styles.fundDescription}>{fund.description}</p>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
