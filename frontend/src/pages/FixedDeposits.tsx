import { useState, useMemo } from 'react';
import { motion } from 'motion/react';
import { PageHeader } from '../components/layout';
import {
  Card,
  Button,
  Badge,
  Input,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableEmpty,
  TableSkeleton,
} from '../components/ui';
import { FixedDepositFormModal } from '../components/features/FixedDepositFormModal';
import { useFixedDeposits } from '../api/hooks';
import { formatCurrency, formatDate } from '../lib/formatters';
import type { FixedDepositWithValue } from '../types';
import styles from './FixedDeposits.module.css';

type StatusFilter = 'all' | 'active' | 'matured';

export function FixedDeposits() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedFD, setSelectedFD] = useState<FixedDepositWithValue | undefined>();

  const { data: fixedDeposits, isLoading } = useFixedDeposits({ status: statusFilter });

  // Filter by search
  const filteredFDs = useMemo(() => {
    if (!fixedDeposits) return [];

    return fixedDeposits.filter((fd) => {
      if (search) {
        const searchLower = search.toLowerCase();
        const matchesSearch =
          fd.institution_name.toLowerCase().includes(searchLower) ||
          fd.account_number.toLowerCase().includes(searchLower) ||
          fd.notes?.toLowerCase().includes(searchLower);
        if (!matchesSearch) return false;
      }
      return true;
    });
  }, [fixedDeposits, search]);

  const openAddModal = () => {
    setSelectedFD(undefined);
    setIsModalOpen(true);
  };

  const openEditModal = (fd: FixedDepositWithValue) => {
    setSelectedFD(fd);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedFD(undefined);
  };

  const getStatusBadge = (fd: FixedDepositWithValue) => {
    if (fd.is_matured) {
      return <Badge variant="default">Matured</Badge>;
    } else if (fd.days_to_maturity <= 7) {
      return <Badge variant="negative">Due Soon</Badge>;
    } else if (fd.days_to_maturity <= 30) {
      return <Badge variant="warning">Maturing</Badge>;
    } else {
      return <Badge variant="positive">Active</Badge>;
    }
  };

  const stats = useMemo(() => {
    if (!fixedDeposits) return { total: 0, active: 0, matured: 0 };

    const active = fixedDeposits.filter((fd) => !fd.is_matured).length;
    const matured = fixedDeposits.filter((fd) => fd.is_matured).length;

    return {
      total: fixedDeposits.length,
      active,
      matured,
    };
  }, [fixedDeposits]);

  return (
    <div className={styles.page}>
      <PageHeader
        title="Fixed Deposits"
        description="Manage your fixed deposit investments"
        action={
          <Button onClick={openAddModal}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            Add Fixed Deposit
          </Button>
        }
      />

      {/* Filter Tabs */}
      <motion.div
        className={styles.tabs}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <button
          className={`${styles.tab} ${statusFilter === 'all' ? styles.tabActive : ''}`}
          onClick={() => setStatusFilter('all')}
        >
          All
          {!isLoading && <span className={styles.tabCount}>{stats.total}</span>}
        </button>
        <button
          className={`${styles.tab} ${statusFilter === 'active' ? styles.tabActive : ''}`}
          onClick={() => setStatusFilter('active')}
        >
          Active
          {!isLoading && <span className={styles.tabCount}>{stats.active}</span>}
        </button>
        <button
          className={`${styles.tab} ${statusFilter === 'matured' ? styles.tabActive : ''}`}
          onClick={() => setStatusFilter('matured')}
        >
          Matured
          {!isLoading && <span className={styles.tabCount}>{stats.matured}</span>}
        </button>
      </motion.div>

      {/* Search */}
      <motion.div
        className={styles.filters}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
      >
        <Input
          placeholder="Search by institution or account..."
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
      </motion.div>

      {/* Fixed Deposits Table */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.2 }}
      >
        <Card padding="none">
          <Table>
            <TableHeader>
              <TableRow hoverable={false}>
                <TableHead>Institution</TableHead>
                <TableHead>Account</TableHead>
                <TableHead align="right">Principal</TableHead>
                <TableHead align="right">Rate</TableHead>
                <TableHead align="right">Current Value</TableHead>
                <TableHead>Maturity Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead align="right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableSkeleton rows={5} columns={8} />
              ) : filteredFDs.length === 0 ? (
                <TableEmpty
                  colSpan={8}
                  message={
                    search
                      ? 'No fixed deposits match your search'
                      : statusFilter === 'active'
                        ? 'No active fixed deposits'
                        : statusFilter === 'matured'
                          ? 'No matured fixed deposits'
                          : 'No fixed deposits yet'
                  }
                  icon={
                    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                      <rect
                        x="8"
                        y="12"
                        width="24"
                        height="16"
                        rx="2"
                        stroke="currentColor"
                        strokeWidth="2"
                      />
                      <path d="M8 16H32" stroke="currentColor" strokeWidth="2" />
                      <circle cx="20" cy="22" r="2" fill="currentColor" />
                    </svg>
                  }
                />
              ) : (
                filteredFDs.map((fd) => (
                  <TableRow key={fd.id}>
                    <TableCell>
                      <span className={styles.institutionName}>{fd.institution_name}</span>
                    </TableCell>
                    <TableCell mono>{fd.account_number}</TableCell>
                    <TableCell align="right" mono>
                      {formatCurrency(fd.principal_amount)}
                    </TableCell>
                    <TableCell align="right" mono>
                      {fd.interest_rate.toFixed(2)}%
                    </TableCell>
                    <TableCell align="right" mono>
                      <div className={styles.valueCell}>
                        <span className={styles.currentValue}>
                          {formatCurrency(fd.current_value)}
                        </span>
                        <span className={styles.accruedInterest}>
                          +{formatCurrency(fd.accrued_interest)}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell mono>
                      <div className={styles.dateCell}>
                        <span>{formatDate(fd.maturity_date)}</span>
                        {!fd.is_matured && (
                          <span className={styles.daysRemaining}>
                            {fd.days_to_maturity} days
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(fd)}</TableCell>
                    <TableCell align="right">
                      <div className={styles.actionCell}>
                        <button
                          className={styles.editButton}
                          onClick={() => openEditModal(fd)}
                          aria-label="Edit fixed deposit"
                        >
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path
                              d="M11.5 2.5L13.5 4.5L5.5 12.5L3 13L3.5 10.5L11.5 2.5Z"
                              stroke="currentColor"
                              strokeWidth="1.5"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
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

      {/* Form Modal */}
      <FixedDepositFormModal
        isOpen={isModalOpen}
        onClose={closeModal}
        fixedDeposit={selectedFD}
      />
    </div>
  );
}
