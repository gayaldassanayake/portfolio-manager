import { useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { PageHeader } from '../components/layout';
import { Card, CardHeader, CardTitle, CardContent, Button } from '../components/ui';
import { ProviderBadge } from '../components/ui/ProviderBadge';
import { StatCard } from '../components/features';
import { UnitTrustFormModal } from '../components/features/UnitTrustFormModal';
import { FetchPricesModal } from '../components/features/FetchPricesModal';
import { PortfolioChart } from '../components/charts';
import { useUnitTrustWithStats, usePrices, useTransactions, useFetchPrices } from '../api/hooks';
import { formatCurrency, formatUnits, formatPercentage, formatDate } from '../lib/formatters';
import styles from './FundDetails.module.css';

type TimeframeKey = '1M' | '3M' | '6M' | '1Y' | 'ALL';

const TIMEFRAMES: { key: TimeframeKey; label: string; days: number | null }[] = [
  { key: '1M', label: '1M', days: 30 },
  { key: '3M', label: '3M', days: 90 },
  { key: '6M', label: '6M', days: 180 },
  { key: '1Y', label: '1Y', days: 365 },
  { key: 'ALL', label: 'All', days: null },
];

// How many sample points to fetch when filling a sparse window. Old prices are
// fetched one-by-one from the provider, so we deliberately spread a small number
// of requests across the window rather than fetching every single day.
const SAMPLE_COUNT = 10;

function toISODate(d: Date): string {
  return d.toISOString().split('T')[0];
}

// Nudge weekend dates onto the nearest weekday so sampled fetches are more
// likely to hit a day that actually has a published NAV.
function snapToWeekday(d: Date): Date {
  const day = d.getDay();
  const out = new Date(d);
  if (day === 0) out.setDate(out.getDate() + 1); // Sun -> Mon
  else if (day === 6) out.setDate(out.getDate() - 1); // Sat -> Fri
  return out;
}

// Evenly spaced, de-duplicated, weekday-snapped dates across [start, end].
function sampleDates(start: Date, end: Date, count: number): string[] {
  const startMs = start.getTime();
  const endMs = end.getTime();
  if (endMs <= startMs || count <= 1) return [toISODate(snapToWeekday(end))];
  const seen = new Set<string>();
  for (let i = 0; i < count; i++) {
    const t = startMs + ((endMs - startMs) * i) / (count - 1);
    seen.add(toISODate(snapToWeekday(new Date(t))));
  }
  return [...seen];
}

export function FundDetails() {
  const { id } = useParams<{ id: string }>();
  const fundId = Number(id);

  const { data: fund, isLoading: fundLoading } = useUnitTrustWithStats(fundId);
  const { data: prices, isLoading: pricesLoading } = usePrices(fundId);
  const { data: allTransactions } = useTransactions();
  const fetchPrices = useFetchPrices();

  const [showEditModal, setShowEditModal] = useState(false);
  const [showFetchModal, setShowFetchModal] = useState(false);
  const [timeframe, setTimeframe] = useState<TimeframeKey>('1M');
  // null = idle; otherwise progress of the sampled fill.
  const [fillProgress, setFillProgress] = useState<{ done: number; total: number } | null>(null);

  // Filter transactions for this fund
  const fundTransactions = useMemo(() => {
    if (!allTransactions) return [];
    return allTransactions
      .filter((t) => t.unit_trust_id === fundId)
      .sort((a, b) => new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime())
      .slice(0, 5);
  }, [allTransactions, fundId]);

  // Inclusive start of the currently selected window (null for "All").
  const windowStart = useMemo(() => {
    const days = TIMEFRAMES.find((t) => t.key === timeframe)?.days;
    if (!days) return null;
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() - days);
    return d;
  }, [timeframe]);

  // Transform prices for chart, filtered to the selected window.
  const chartData = useMemo(() => {
    if (!prices) return [];
    return prices
      .map((p) => ({ date: p.date, value: p.price }))
      .filter((p) => !windowStart || new Date(p.date) >= windowStart)
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [prices, windowStart]);

  // Most recent price entry that quotes buy/sell prices (equity funds only).
  // Used to surface the buy/sell spread alongside the NAV.
  const latestQuote = useMemo(() => {
    if (!prices) return null;
    const quoted = prices
      .filter((p) => p.buy_price != null || p.sell_price != null)
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    return quoted[0] ?? null;
  }, [prices]);

  // Dates already stored (YYYY-MM-DD) so we never re-request them when filling.
  const existingDates = useMemo(() => {
    return new Set((prices ?? []).map((p) => p.date.split('T')[0]));
  }, [prices]);

  // Fetch a small evenly-spaced sample of prices across the selected window.
  const handleFillWindow = async () => {
    if (!fund?.provider || fillProgress) return;
    const end = new Date();
    end.setHours(0, 0, 0, 0);
    const start = windowStart ?? (() => {
      const d = new Date(end);
      d.setDate(d.getDate() - 365); // "All" with no stored data: sample the last year
      return d;
    })();

    const targets = sampleDates(start, end, SAMPLE_COUNT).filter((d) => !existingDates.has(d));
    if (targets.length === 0) return;

    setFillProgress({ done: 0, total: targets.length });
    for (let i = 0; i < targets.length; i++) {
      try {
        await fetchPrices.mutateAsync({
          unitTrustId: fundId,
          startDate: targets[i],
          endDate: targets[i],
        });
      } catch {
        // Skip dates the provider can't serve (weekends/holidays); keep going.
      }
      setFillProgress({ done: i + 1, total: targets.length });
    }
    setFillProgress(null);
  };

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
          <div className={styles.headerActions}>
            {fund.provider && (
              <Button variant="secondary" onClick={() => setShowFetchModal(true)}>
                Fetch Prices
              </Button>
            )}
            <Button variant="secondary" onClick={() => setShowEditModal(true)}>
              Edit Fund
            </Button>
            <Link to={`/transactions?action=add&fund=${fundId}`}>
              <Button>Add Transaction</Button>
            </Link>
          </div>
        }
      />

      {/* Provider Badge */}
      {fund.provider && (
        <div className={styles.providerSection}>
          <ProviderBadge provider={fund.provider} showIcon />
        </div>
      )}

      {/* Stats Grid */}
      <section className={styles.statsGrid}>
        {/* Row 1 — outcome: invested → worth now → result */}
        <StatCard
          label="Total Cost"
          value={formatCurrency(fund.total_cost)}
          delay={0}
        />
        <StatCard
          label="Current Value"
          value={formatCurrency(fund.current_value)}
          delay={1}
        />
        <StatCard
          label="Gain/Loss"
          value={formatCurrency(fund.gain_loss)}
          change={fund.gain_loss_percentage !== null ? {
            value: formatPercentage(fund.gain_loss_percentage),
            type: changeType as 'positive' | 'negative' | 'neutral',
          } : undefined}
          delay={2}
        />
        {/* Row 2 — mechanics: units held → paid per unit → worth per unit */}
        <StatCard
          label="Total Units"
          value={formatUnits(fund.total_units)}
          delay={3}
        />
        <StatCard
          label="Avg Purchase Price"
          value={formatCurrency(fund.avg_purchase_price, { maximumFractionDigits: 4 })}
          delay={4}
        />
        <StatCard
          label="Latest Price"
          value={formatCurrency(fund.latest_price, { maximumFractionDigits: 4 })}
          delay={5}
        />
        {latestQuote && (
          <>
            <StatCard
              label="Buy Price"
              value={formatCurrency(latestQuote.buy_price, { maximumFractionDigits: 4 })}
              delay={6}
            />
            <StatCard
              label="Sell Price"
              value={formatCurrency(latestQuote.sell_price, { maximumFractionDigits: 4 })}
              delay={7}
            />
          </>
        )}
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
            <CardHeader
              action={
                <div className={styles.chartControls}>
                  <div className={styles.timeframes}>
                    {TIMEFRAMES.map((tf) => (
                      <button
                        key={tf.key}
                        type="button"
                        className={`${styles.timeframeButton} ${
                          timeframe === tf.key ? styles.timeframeActive : ''
                        }`}
                        onClick={() => setTimeframe(tf.key)}
                      >
                        {tf.label}
                      </button>
                    ))}
                  </div>
                  {fund.provider && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={handleFillWindow}
                      loading={fillProgress !== null}
                      disabled={fillProgress !== null}
                    >
                      {fillProgress
                        ? `Fetching ${fillProgress.done}/${fillProgress.total}`
                        : 'Fetch prices'}
                    </Button>
                  )}
                </div>
              }
            >
              <CardTitle>Price History</CardTitle>
            </CardHeader>
            <CardContent>
              {pricesLoading ? (
                <div className="skeleton" style={{ height: '300px', borderRadius: 'var(--radius-md)' }} />
              ) : chartData.length > 0 ? (
                <>
                  <PortfolioChart data={chartData} height={300} />
                  {chartData.length < 5 && fund.provider && (
                    <p className={styles.sparseHint}>
                      Only {chartData.length} {chartData.length === 1 ? 'price' : 'prices'} in this
                      window. Use “Fetch prices” to pull a sample across the range.
                    </p>
                  )}
                </>
              ) : (
                <div className={styles.noData}>
                  <p>No price history in this window</p>
                  {fund.provider && (
                    <p className={styles.noDataHint}>Use “Fetch prices” to populate it.</p>
                  )}
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

      {/* Modals */}
      <UnitTrustFormModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        unitTrust={fund}
        onSuccess={() => {
          setShowEditModal(false);
        }}
      />

      {fund.provider && (
        <FetchPricesModal
          isOpen={showFetchModal}
          onClose={() => setShowFetchModal(false)}
          unitTrust={fund}
          onSuccess={() => {
            setShowFetchModal(false);
          }}
        />
      )}
    </div>
  );
}
