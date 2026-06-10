import { useState, useMemo, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'motion/react';
import { PageHeader } from '../components/layout';
import {
  Card,
  Button,
  Badge,
  Input,
  Select,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableEmpty,
  TableSkeleton,
  Modal,
  ModalFooter,
} from '../components/ui';
import { useTransactions, useUnitTrusts, useCreateTransaction, useDeleteTransaction, useFetchPrices } from '../api/hooks';
import { api } from '../api/client';
import { formatCurrency, formatUnits, formatDate, formatDateForInput } from '../lib/formatters';
import type { TransactionCreate, TransactionType } from '../types';
import styles from './Transactions.module.css';

export function Transactions() {
  const [searchParams, setSearchParams] = useSearchParams();
  const showAddModal = searchParams.get('action') === 'add';
  // When opened from a specific holding, pre-select that fund in the modal.
  const presetFundId = Number(searchParams.get('fund')) || 0;
  
  const { data: transactions, isLoading } = useTransactions();
  const { data: unitTrusts } = useUnitTrusts();
  
  // Filters
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  // Initialize from the `fund` query param so links like /transactions?fund=7 filter on load.
  const [fundFilter, setFundFilter] = useState<string>(searchParams.get('fund') ?? '');

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(showAddModal);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  // Sync modal with URL
  useEffect(() => {
    setIsModalOpen(showAddModal);
  }, [showAddModal]);

  const closeModal = () => {
    setIsModalOpen(false);
    setSearchParams({});
  };

  const openModal = () => {
    setIsModalOpen(true);
    setSearchParams({ action: 'add' });
  };

  // Filter transactions
  const filteredTransactions = useMemo(() => {
    if (!transactions) return [];
    
    return transactions.filter((tx) => {
      // Search filter
      if (search) {
        const searchLower = search.toLowerCase();
        const matchesSearch = 
          tx.unit_trust.name.toLowerCase().includes(searchLower) ||
          tx.unit_trust.symbol.toLowerCase().includes(searchLower) ||
          tx.notes?.toLowerCase().includes(searchLower);
        if (!matchesSearch) return false;
      }
      
      // Type filter
      if (typeFilter && tx.transaction_type !== typeFilter) {
        return false;
      }
      
      // Fund filter
      if (fundFilter && tx.unit_trust_id !== Number(fundFilter)) {
        return false;
      }
      
      return true;
    });
  }, [transactions, search, typeFilter, fundFilter]);

  const fundOptions = useMemo(() => {
    if (!unitTrusts) return [];
    return unitTrusts.map((fund) => ({
      value: String(fund.id),
      label: `${fund.symbol} - ${fund.name}`,
    }));
  }, [unitTrusts]);

  return (
    <div className={styles.page}>
      <PageHeader
        title="Transactions"
        description="View and manage your transaction history"
        action={
          <Button onClick={openModal}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            Add Transaction
          </Button>
        }
      />

      {/* Filters */}
      <motion.div
        className={styles.filters}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Input
          placeholder="Search transactions..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          leftIcon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
              <path d="M11 11L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          }
          fullWidth={false}
          className={styles.searchInput}
        />
        <Select
          options={[
            { value: '', label: 'All Types' },
            { value: 'buy', label: 'Buy' },
            { value: 'sell', label: 'Sell' },
          ]}
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          fullWidth={false}
          className={styles.filterSelect}
        />
        <Select
          options={[{ value: '', label: 'All Funds' }, ...fundOptions]}
          value={fundFilter}
          onChange={(e) => setFundFilter(e.target.value)}
          fullWidth={false}
          className={styles.filterSelect}
        />
      </motion.div>

      {/* Transactions Table */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
      >
        <Card padding="none">
          <Table>
            <TableHeader>
              <TableRow hoverable={false}>
                <TableHead>Date</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Fund</TableHead>
                <TableHead align="right">Units</TableHead>
                <TableHead align="right">Price</TableHead>
                <TableHead align="right">Total</TableHead>
                <TableHead align="right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableSkeleton rows={5} columns={7} />
              ) : filteredTransactions.length === 0 ? (
                <TableEmpty
                  colSpan={7}
                  message={search || typeFilter || fundFilter ? "No transactions match your filters" : "No transactions yet"}
                  icon={
                    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                      <path d="M8 14H32M8 14L12 10M8 14L12 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      <path d="M32 26H8M32 26L28 22M32 26L28 30" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  }
                />
              ) : (
                filteredTransactions.map((tx) => (
                  <TableRow key={tx.id}>
                    <TableCell mono>
                      {formatDate(tx.transaction_date)}
                    </TableCell>
                    <TableCell>
                      <Badge variant={tx.transaction_type === 'buy' ? 'positive' : 'negative'}>
                        {tx.transaction_type === 'buy' ? 'Buy' : 'Sell'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className={styles.fundCell}>
                        <span className={styles.fundSymbol}>{tx.unit_trust.symbol}</span>
                        <span className={styles.fundName}>{tx.unit_trust.name}</span>
                      </div>
                    </TableCell>
                    <TableCell align="right" mono>
                      {formatUnits(tx.units)}
                    </TableCell>
                    <TableCell align="right" mono>
                      {formatCurrency(tx.price_per_unit, { maximumFractionDigits: 4 })}
                    </TableCell>
                    <TableCell align="right" mono>
                      {formatCurrency(tx.units * tx.price_per_unit)}
                    </TableCell>
                    <TableCell align="right">
                      <div className={styles.actionCell}>
                        {tx.notes && (
                          <span className={styles.notesIcon} title={tx.notes}>
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                              <path d="M3 3H13V13H3V3Z" stroke="currentColor" strokeWidth="1.5" />
                              <path d="M5 6H11M5 8H11M5 10H8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                            </svg>
                          </span>
                        )}
                        <button
                          className={styles.deleteButton}
                          onClick={() => setDeleteId(tx.id)}
                          aria-label="Delete transaction"
                        >
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M3 4H13M6 4V3C6 2.44772 6.44772 2 7 2H9C9.55228 2 10 2.44772 10 3V4M12 4V13C12 13.5523 11.5523 14 11 14H5C4.44772 14 4 13.5523 4 13V4H12Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                          </svg>
                        </button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </Card>
      </motion.div>

      {/* Add Transaction Modal */}
      <AddTransactionModal
        key={`add-${presetFundId}`}
        isOpen={isModalOpen}
        onClose={closeModal}
        unitTrusts={unitTrusts || []}
        initialFundId={presetFundId}
      />

      {/* Delete Confirmation Modal */}
      <DeleteTransactionModal
        transactionId={deleteId}
        onClose={() => setDeleteId(null)}
      />
    </div>
  );
}

// Add Transaction Modal Component
function AddTransactionModal({
  isOpen,
  onClose,
  unitTrusts,
  initialFundId = 0,
}: {
  isOpen: boolean;
  onClose: () => void;
  unitTrusts: Array<{ id: number; name: string; symbol: string }>;
  initialFundId?: number;
}) {
  const createTransaction = useCreateTransaction();
  const fetchPrices = useFetchPrices();

  const [formData, setFormData] = useState<TransactionCreate>({
    unit_trust_id: initialFundId,
    transaction_type: 'buy',
    units: 0,
    price_per_unit: undefined,
    transaction_date: formatDateForInput(new Date()),
    notes: '',
  });

  // Free-text price input (kept separate so an empty string maps to "use daily price").
  const [priceInput, setPriceInput] = useState('');
  const [fetchMessage, setFetchMessage] = useState<string | null>(null);

  // 'units': enter units directly. 'amount': enter total invested and derive units = amount / price.
  const [mode, setMode] = useState<'units' | 'amount'>('units');
  const [amountInput, setAmountInput] = useState('');

  const [errors, setErrors] = useState<Record<string, string>>({});

  const parsedPrice = Number(priceInput);
  const parsedAmount = Number(amountInput);

  // In amount mode the three fields (amount, price, units) stay consistent via
  // amount = units × price. Editing one recomputes a dependent field, but each
  // field remains directly editable so the user can fine-tune the result.
  const setUnits = (units: number) => setFormData((prev) => ({ ...prev, units }));
  // Derived units are rounded to 4 dp (the Units input step) to avoid float noise.
  const deriveUnits = (amount: number, price: number) => Number((amount / price).toFixed(4));

  const handleAmountChange = (value: string) => {
    setAmountInput(value);
    const a = Number(value);
    if (a > 0 && parsedPrice > 0) setUnits(deriveUnits(a, parsedPrice));
  };

  const handlePriceChange = (value: string) => {
    setPriceInput(value);
    setFetchMessage(null);
    if (mode === 'amount') {
      const p = Number(value);
      if (p > 0 && parsedAmount > 0) setUnits(deriveUnits(parsedAmount, p));
    }
  };

  const handleUnitsChange = (value: string) => {
    const u = Number(value);
    setUnits(u);
    // Keep the entered amount in sync with the (possibly hand-tuned) unit count.
    if (mode === 'amount' && parsedPrice > 0) {
      setAmountInput(u > 0 ? String(Number((u * parsedPrice).toFixed(2))) : '');
    }
  };

  const handleFetchPrice = async () => {
    if (!formData.unit_trust_id || !formData.transaction_date) return;
    setFetchMessage(null);
    const dateStr = formData.transaction_date;
    try {
      const result = await fetchPrices.mutateAsync({
        unitTrustId: formData.unit_trust_id,
        startDate: dateStr,
        endDate: dateStr,
      });
      let match = result.prices.find((p) => p.date.startsWith(dateStr));
      if (!match) {
        // Price already existed (not in the saved list) - read it back.
        const all = await api.prices.getForFund(formData.unit_trust_id);
        match = all.find((p) => p.date.startsWith(dateStr));
      }
      if (match) {
        // A buy fills at the buy (creation) price and a sell at the sell
        // (redemption) price when the fund quotes them, else the NAV.
        const effectivePrice =
          formData.transaction_type === 'buy'
            ? (match.buy_price ?? match.price)
            : (match.sell_price ?? match.price);
        setPriceInput(String(effectivePrice));
        setFormData((prev) => ({ ...prev, price_per_unit: effectivePrice }));
        if (mode === 'amount' && parsedAmount > 0)
          setUnits(deriveUnits(parsedAmount, effectivePrice));
      } else {
        setFetchMessage('No price found for this date. Enter it manually.');
      }
    } catch {
      setFetchMessage('Could not fetch a price. Enter it manually.');
    }
  };

  const resetForm = () => {
    setFormData({
      unit_trust_id: 0,
      transaction_type: 'buy',
      units: 0,
      price_per_unit: undefined,
      transaction_date: formatDateForInput(new Date()),
      notes: '',
    });
    setPriceInput('');
    setAmountInput('');
    setMode('units');
    setFetchMessage(null);
    setErrors({});
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.unit_trust_id) {
      newErrors.unit_trust_id = 'Please select a fund';
    }
    if (!formData.transaction_date) {
      newErrors.transaction_date = 'Please select a date';
    }

    if (mode === 'amount') {
      if (parsedAmount <= 0) {
        newErrors.amount = 'Amount must be greater than 0';
      }
      // Price is required in amount mode since units are derived from it.
      if (!(parsedPrice > 0)) {
        newErrors.price = 'Enter or fetch a price to compute units';
      }
      if (formData.units <= 0) {
        newErrors.units = 'Units must be greater than 0';
      }
    } else if (formData.units <= 0) {
      newErrors.units = 'Units must be greater than 0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    try {
      if (mode === 'amount') {
        await createTransaction.mutateAsync({
          ...formData,
          units: formData.units,
          price_per_unit: parsedPrice,
        });
      } else {
        const trimmed = priceInput.trim();
        await createTransaction.mutateAsync({
          ...formData,
          price_per_unit: trimmed ? Number(trimmed) : undefined,
        });
      }
      onClose();
      resetForm();
    } catch (error) {
      console.error('Failed to create transaction:', error);
    }
  };

  const fundOptions = unitTrusts.map((fund) => ({
    value: fund.id,
    label: `${fund.symbol} - ${fund.name}`,
  }));

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add Transaction"
      description="Record a new buy or sell transaction"
      size="md"
    >
      <form onSubmit={handleSubmit} className={styles.form}>
        <Select
          label="Fund"
          options={fundOptions}
          value={String(formData.unit_trust_id || '')}
          onChange={(e) => setFormData({ ...formData, unit_trust_id: Number(e.target.value) })}
          placeholder="Select a fund"
          error={errors.unit_trust_id}
        />
        
        <Select
          label="Transaction Type"
          options={[
            { value: 'buy', label: 'Buy' },
            { value: 'sell', label: 'Sell' },
          ]}
          value={formData.transaction_type}
          onChange={(e) => setFormData({ ...formData, transaction_type: e.target.value as TransactionType })}
        />
        
        <div className={styles.modeField}>
          <span className={styles.priceLabel}>Enter by</span>
          <div className={styles.modeToggle}>
            {(['units', 'amount'] as const).map((m) => (
              <button
                key={m}
                type="button"
                className={`${styles.modeButton} ${mode === m ? styles.modeActive : ''}`}
                onClick={() => {
                  setMode(m);
                  setErrors({});
                }}
              >
                {m === 'units' ? 'Units' : 'Amount'}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.formRow}>
          {mode === 'units' ? (
            <Input
              label="Units"
              type="number"
              step="0.0001"
              min="0"
              value={formData.units || ''}
              onChange={(e) => setFormData({ ...formData, units: Number(e.target.value) })}
              error={errors.units}
            />
          ) : (
            <Input
              label="Amount invested"
              type="number"
              step="0.01"
              min="0"
              value={amountInput}
              onChange={(e) => handleAmountChange(e.target.value)}
              error={errors.amount}
              placeholder="Total amount paid"
            />
          )}

          <Input
            label="Transaction Date"
            type="date"
            value={formData.transaction_date}
            onChange={(e) => setFormData({ ...formData, transaction_date: e.target.value })}
            error={errors.transaction_date}
          />
        </div>

        <div className={styles.priceField}>
          <label className={styles.priceLabel} htmlFor="price-per-unit">
            {mode === 'amount' ? 'Price per unit' : 'Price per unit (optional)'}
          </label>
          <div className={styles.priceRow}>
            <Input
              id="price-per-unit"
              type="number"
              step="0.0001"
              min="0"
              value={priceInput}
              onChange={(e) => handlePriceChange(e.target.value)}
              placeholder={
                mode === 'amount'
                  ? 'Enter or fetch a price'
                  : 'Leave blank to use the daily price'
              }
              error={errors.price}
            />

            <Button
              variant="secondary"
              type="button"
              onClick={handleFetchPrice}
              loading={fetchPrices.isPending}
              disabled={!formData.unit_trust_id || !formData.transaction_date}
              className={styles.fetchPriceButton}
            >
              Fetch price
            </Button>
          </div>
          <p className={styles.priceHint}>The price you actually paid/received per unit</p>
        </div>
        {fetchMessage && <p className={styles.priceNote}>{fetchMessage}</p>}

        {mode === 'amount' && (
          <Input
            label="Units (calculated, editable)"
            type="number"
            step="0.0001"
            min="0"
            value={formData.units || ''}
            onChange={(e) => handleUnitsChange(e.target.value)}
            error={errors.units}
            hint="Auto-filled from amount ÷ price. Adjust if your statement differs."
          />
        )}

        <Input
          label="Notes (optional)"
          value={formData.notes || ''}
          onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
          placeholder="Add any notes..."
        />

        <ModalFooter>
          <Button variant="ghost" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={createTransaction.isPending}>
            Add Transaction
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  );
}

// Delete Confirmation Modal
function DeleteTransactionModal({
  transactionId,
  onClose,
}: {
  transactionId: number | null;
  onClose: () => void;
}) {
  const deleteTransaction = useDeleteTransaction();

  const handleDelete = async () => {
    if (!transactionId) return;
    
    try {
      await deleteTransaction.mutateAsync(transactionId);
      onClose();
    } catch (error) {
      console.error('Failed to delete transaction:', error);
    }
  };

  return (
    <Modal
      isOpen={transactionId !== null}
      onClose={onClose}
      title="Delete Transaction"
      description="Are you sure you want to delete this transaction? This action cannot be undone."
      size="sm"
    >
      <ModalFooter>
        <Button variant="ghost" onClick={onClose}>
          Cancel
        </Button>
        <Button variant="danger" onClick={handleDelete} loading={deleteTransaction.isPending}>
          Delete
        </Button>
      </ModalFooter>
    </Modal>
  );
}
