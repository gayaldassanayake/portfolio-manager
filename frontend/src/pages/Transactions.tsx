import { useState, useMemo, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'motion/react';
import { PageHeader } from '../components/layout';
import {
  Card,
  Button,
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
import { useTransactions, useUnitTrusts, useCreateTransaction, useDeleteTransaction } from '../api/hooks';
import { formatCurrency, formatUnits, formatDate, formatDateForInput } from '../lib/formatters';
import type { TransactionCreate, TransactionType } from '../types';
import styles from './Transactions.module.css';

export function Transactions() {
  const [searchParams, setSearchParams] = useSearchParams();
  const showAddModal = searchParams.get('action') === 'add';
  
  const { data: transactions, isLoading } = useTransactions();
  const { data: unitTrusts } = useUnitTrusts();
  
  // Filters
  const [search, setSearch] = useState('');
  const [fundFilter, setFundFilter] = useState<string>('');

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
      
      // Fund filter
      if (fundFilter && tx.unit_trust_id !== Number(fundFilter)) {
        return false;
      }
      
      return true;
    });
  }, [transactions, search, fundFilter]);

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
{/* Type filter hidden - backend doesn't return transaction_type */}
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
                  colSpan={6}
                  message={search || fundFilter ? "No transactions match your filters" : "No transactions yet"}
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
                      <button
                        className={styles.deleteButton}
                        onClick={() => setDeleteId(tx.id)}
                        aria-label="Delete transaction"
                      >
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                          <path d="M3 4H13M6 4V3C6 2.44772 6.44772 2 7 2H9C9.55228 2 10 2.44772 10 3V4M12 4V13C12 13.5523 11.5523 14 11 14H5C4.44772 14 4 13.5523 4 13V4H12Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                        </svg>
                      </button>
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
        isOpen={isModalOpen}
        onClose={closeModal}
        unitTrusts={unitTrusts || []}
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
}: {
  isOpen: boolean;
  onClose: () => void;
  unitTrusts: Array<{ id: number; name: string; symbol: string }>;
}) {
  const createTransaction = useCreateTransaction();
  
  const [formData, setFormData] = useState<TransactionCreate>({
    unit_trust_id: 0,
    transaction_type: 'buy',
    units: 0,
    price_per_unit: 0,
    transaction_date: formatDateForInput(new Date()),
    notes: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.unit_trust_id) {
      newErrors.unit_trust_id = 'Please select a fund';
    }
    if (formData.units <= 0) {
      newErrors.units = 'Units must be greater than 0';
    }
    if (formData.price_per_unit <= 0) {
      newErrors.price_per_unit = 'Price must be greater than 0';
    }
    if (!formData.transaction_date) {
      newErrors.transaction_date = 'Please select a date';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) return;
    
    try {
      await createTransaction.mutateAsync(formData);
      onClose();
      // Reset form
      setFormData({
        unit_trust_id: 0,
        transaction_type: 'buy',
        units: 0,
        price_per_unit: 0,
        transaction_date: formatDateForInput(new Date()),
        notes: '',
      });
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
        
        <div className={styles.formRow}>
          <Input
            label="Units"
            type="number"
            step="0.0001"
            min="0"
            value={formData.units || ''}
            onChange={(e) => setFormData({ ...formData, units: Number(e.target.value) })}
            error={errors.units}
          />
          
          <Input
            label="Price per Unit"
            type="number"
            step="0.0001"
            min="0"
            value={formData.price_per_unit || ''}
            onChange={(e) => setFormData({ ...formData, price_per_unit: Number(e.target.value) })}
            error={errors.price_per_unit}
          />
        </div>
        
        <Input
          label="Transaction Date"
          type="date"
          value={formData.transaction_date}
          onChange={(e) => setFormData({ ...formData, transaction_date: e.target.value })}
          error={errors.transaction_date}
        />
        
        <Input
          label="Notes (optional)"
          value={formData.notes || ''}
          onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
          placeholder="Add any notes..."
        />

        {formData.units > 0 && formData.price_per_unit > 0 && (
          <div className={styles.totalPreview}>
            <span>Total:</span>
            <span className={styles.totalValue}>
              {formatCurrency(formData.units * formData.price_per_unit)}
            </span>
          </div>
        )}

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
