import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Modal, ModalFooter, Button, Input } from '../ui';
import { ProviderBadge } from '../ui/ProviderBadge';
import { useFetchPrices, useBulkFetchPrices } from '../../api/hooks/usePriceFetch';
import type { UnitTrust, PriceFetchResult, BulkPriceFetchResponse } from '../../types';
import styles from './FetchPricesModal.module.css';

interface FetchPricesModalProps {
  isOpen: boolean;
  onClose: () => void;
  unitTrust?: UnitTrust; // If provided, single fetch; otherwise bulk fetch
  unitTrusts?: UnitTrust[]; // For bulk fetch
  onSuccess?: () => void;
}

interface DatePreset {
  label: string;
  days: number;
}

const DATE_PRESETS: DatePreset[] = [
  { label: 'Today', days: 0 },
  { label: '7 Days', days: 7 },
  { label: '30 Days', days: 30 },
  { label: '90 Days', days: 90 },
];

function getTodayString(): string {
  return new Date().toISOString().split('T')[0];
}

function getDateString(daysAgo: number): string {
  const date = new Date();
  date.setDate(date.getDate() - daysAgo);
  return date.toISOString().split('T')[0];
}

export function FetchPricesModal({
  isOpen,
  onClose,
  unitTrust,
  unitTrusts = [],
  onSuccess,
}: FetchPricesModalProps) {
  const isBulkMode = !unitTrust;
  const fetchMutation = useFetchPrices();
  const bulkFetchMutation = useBulkFetchPrices();

  const [startDate, setStartDate] = useState(getTodayString());
  const [endDate, setEndDate] = useState(getTodayString());
  const [result, setResult] = useState<PriceFetchResult | BulkPriceFetchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setStartDate(getTodayString());
      setEndDate(getTodayString());
      setResult(null);
      setError(null);
    }
  }, [isOpen]);

  const applyPreset = (days: number) => {
    const end = getTodayString();
    const start = days === 0 ? end : getDateString(days);
    setStartDate(start);
    setEndDate(end);
  };

  const handleFetch = async () => {
    setResult(null);
    setError(null);

    try {
      if (isBulkMode) {
        // Bulk fetch for all funds with providers
        const fundsWithProviders = unitTrusts.filter((ut) => ut.provider);
        const unitTrustIds = fundsWithProviders.map((ut) => ut.id);

        if (unitTrustIds.length === 0) {
          setError('No funds have configured providers. Please add a provider to at least one fund.');
          return;
        }

        const response = await bulkFetchMutation.mutateAsync({
          unitTrustIds,
          startDate,
          endDate,
        });
        setResult(response);
      } else if (unitTrust) {
        // Single fetch
        if (!unitTrust.provider) {
          setError('This fund does not have a provider configured.');
          return;
        }

        const response = await fetchMutation.mutateAsync({
          unitTrustId: unitTrust.id,
          startDate,
          endDate,
        });
        setResult(response);
      }

      onSuccess?.();
    } catch (err: any) {
      setError(err.message || 'Failed to fetch prices. Please try again.');
    }
  };

  const isPending = fetchMutation.isPending || bulkFetchMutation.isPending;
  const showResults = result !== null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isBulkMode ? 'Bulk Fetch Prices' : `Fetch Prices - ${unitTrust?.symbol}`}
      description={
        isBulkMode
          ? 'Fetch prices for all funds with configured providers'
          : `Fetch prices from ${unitTrust?.provider?.toUpperCase() || 'provider'}`
      }
      size="lg"
    >
      <div className={styles.content}>
        {/* Provider Info - Single Mode */}
        {!isBulkMode && unitTrust && (
          <div className={styles.fundInfo}>
            <div className={styles.fundHeader}>
              <div>
                <h4 className={styles.fundName}>{unitTrust.name}</h4>
                <p className={styles.fundSymbol}>{unitTrust.symbol}</p>
              </div>
              {unitTrust.provider && <ProviderBadge provider={unitTrust.provider} showIcon />}
            </div>
          </div>
        )}

        {/* Bulk Mode Info */}
        {isBulkMode && (
          <div className={styles.bulkInfo}>
            <p className={styles.bulkDescription}>
              {unitTrusts.filter((ut) => ut.provider).length} of {unitTrusts.length} funds have
              configured providers
            </p>
          </div>
        )}

        {/* Date Selection */}
        {!showResults && (
          <div className={styles.dateSection}>
            <div className={styles.presets}>
              {DATE_PRESETS.map((preset) => (
                <button
                  key={preset.label}
                  type="button"
                  className={styles.preset}
                  onClick={() => applyPreset(preset.days)}
                  disabled={isPending}
                >
                  {preset.label}
                </button>
              ))}
            </div>

            <div className={styles.dateInputs}>
              <Input
                type="date"
                label="Start Date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                disabled={isPending}
                max={endDate}
              />
              <Input
                type="date"
                label="End Date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                disabled={isPending}
                min={startDate}
              />
            </div>
          </div>
        )}

        {/* Error Display */}
        <AnimatePresence mode="wait">
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={styles.error}
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="2" />
                <path d="M10 6V10M10 13V14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
              <p>{error}</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results Display */}
        <AnimatePresence mode="wait">
          {showResults && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className={styles.results}
            >
              {isBulkMode && 'total_requested' in result ? (
                // Bulk results
                <BulkResults result={result} />
              ) : 'unit_trust_id' in result ? (
                // Single result
                <SingleResult result={result} />
              ) : null}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <ModalFooter>
        <Button variant="ghost" onClick={onClose} disabled={isPending}>
          {showResults ? 'Done' : 'Cancel'}
        </Button>
        {!showResults && (
          <Button onClick={handleFetch} loading={isPending}>
            Fetch Prices
          </Button>
        )}
      </ModalFooter>
    </Modal>
  );
}

// Single fetch result component
function SingleResult({ result }: { result: PriceFetchResult }) {
  const skipped = result.prices_fetched - result.prices_saved;
  const hasSkipped = skipped > 0;

  return (
    <div className={styles.singleResult}>
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.1, type: 'spring', stiffness: 200 }}
        className={styles.successIcon}
      >
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
          <circle cx="24" cy="24" r="22" stroke="currentColor" strokeWidth="3" />
          <path
            d="M14 24L20 30L34 16"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </motion.div>

      <h3 className={styles.resultTitle}>Prices Fetched Successfully</h3>

      <div className={styles.stats}>
        <div className={styles.stat}>
          <span className={styles.statValue}>{result.prices_fetched}</span>
          <span className={styles.statLabel}>Fetched</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statValue}>{result.prices_saved}</span>
          <span className={styles.statLabel}>Saved</span>
        </div>
        {hasSkipped && (
          <div className={styles.stat}>
            <span className={styles.statValue}>{skipped}</span>
            <span className={styles.statLabel}>Skipped</span>
          </div>
        )}
      </div>

      {hasSkipped && (
        <p className={styles.hint}>
          {skipped} duplicate {skipped === 1 ? 'price was' : 'prices were'} skipped (already in
          database)
        </p>
      )}
    </div>
  );
}

// Bulk fetch results component
function BulkResults({ result }: { result: BulkPriceFetchResponse }) {
  const hasErrors = result.failed > 0;

  return (
    <div className={styles.bulkResult}>
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.1, type: 'spring', stiffness: 200 }}
        className={styles.successIcon}
      >
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
          <circle cx="24" cy="24" r="22" stroke="currentColor" strokeWidth="3" />
          <path
            d="M14 24L20 30L34 16"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </motion.div>

      <h3 className={styles.resultTitle}>Bulk Fetch Complete</h3>

      <div className={styles.stats}>
        <div className={styles.stat}>
          <span className={styles.statValue}>{result.total_requested}</span>
          <span className={styles.statLabel}>Requested</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statValue}>{result.successful}</span>
          <span className={styles.statLabel}>Successful</span>
        </div>
        {hasErrors && (
          <div className={styles.stat}>
            <span className={styles.statValue}>{result.failed}</span>
            <span className={styles.statLabel}>Failed</span>
          </div>
        )}
      </div>

      {/* Successful Results Summary */}
      {result.results.length > 0 && (
        <div className={styles.resultsList}>
          <h4 className={styles.resultsListTitle}>Successfully Fetched:</h4>
          {result.results.map((res) => (
            <div key={res.unit_trust_id} className={styles.resultItem}>
              <span className={styles.resultSymbol}>{res.symbol}</span>
              <span className={styles.resultDetail}>
                {res.prices_saved} saved ({res.prices_fetched - res.prices_saved} skipped)
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Errors */}
      {hasErrors && result.errors.length > 0 && (
        <div className={styles.errorsList}>
          <h4 className={styles.errorsListTitle}>Errors:</h4>
          {result.errors.map((err) => (
            <div key={err.unit_trust_id} className={styles.errorItem}>
              <span className={styles.errorSymbol}>{err.symbol}</span>
              <span className={styles.errorDetail}>{err.error}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
