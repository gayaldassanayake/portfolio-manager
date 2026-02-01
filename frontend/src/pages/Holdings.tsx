import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { PageHeader } from '../components/layout';
import {
  Card,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableEmpty,
  TableSkeleton,
} from '../components/ui';
import { Sparkline } from '../components/charts';
import { useUnitTrusts } from '../api/hooks';
import '../lib/formatters';
import { sortBy } from '../lib/utils';
import type { SortDirection } from '../types';
import styles from './Holdings.module.css';

type SortKey = 'symbol' | 'name';

export function Holdings() {
  const { data: unitTrusts, isLoading, error } = useUnitTrusts();
  const [sortConfig, setSortConfig] = useState<{ key: SortKey; direction: SortDirection }>({
    key: 'symbol',
    direction: 'asc',
  });

  const sortedData = useMemo(() => {
    if (!unitTrusts) return [];
    return sortBy(unitTrusts, sortConfig.key, sortConfig.direction);
  }, [unitTrusts, sortConfig]);

  const handleSort = (key: SortKey) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  return (
    <div className={styles.page}>
      <PageHeader
        title="Holdings"
        description="All your unit trust investments"
      />

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card padding="none">
          <Table>
            <TableHeader>
              <TableRow hoverable={false}>
                <TableHead
                  sortable
                  sorted={sortConfig.key === 'symbol' ? sortConfig.direction : false}
                  onSort={() => handleSort('symbol')}
                >
                  Symbol
                </TableHead>
                <TableHead
                  sortable
                  sorted={sortConfig.key === 'name' ? sortConfig.direction : false}
                  onSort={() => handleSort('name')}
                >
                  Name
                </TableHead>
                <TableHead align="right">Description</TableHead>
                <TableHead align="center">Trend</TableHead>
                <TableHead align="right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableSkeleton rows={5} columns={5} />
              ) : error ? (
                <TableEmpty
                  colSpan={5}
                  message="Failed to load holdings"
                  icon={
                    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                      <circle cx="20" cy="20" r="18" stroke="currentColor" strokeWidth="2" />
                      <path d="M20 12V22M20 26V28" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                  }
                />
              ) : sortedData.length === 0 ? (
                <TableEmpty
                  colSpan={5}
                  message="No holdings found"
                  icon={
                    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                      <rect x="6" y="10" width="28" height="20" rx="2" stroke="currentColor" strokeWidth="2" />
                      <path d="M6 16H34" stroke="currentColor" strokeWidth="2" />
                    </svg>
                  }
                />
              ) : (
                sortedData.map((fund) => (
                  <TableRow key={fund.id}>
                    <TableCell mono>
                      <span className={styles.symbol}>{fund.symbol}</span>
                    </TableCell>
                    <TableCell>
                      <span className={styles.name}>{fund.name}</span>
                    </TableCell>
                    <TableCell align="right">
                      <span className={styles.description}>
                        {fund.description || '—'}
                      </span>
                    </TableCell>
                    <TableCell align="center">
                      <Sparkline 
                        data={[100, 102, 98, 105, 103, 108, 110]} 
                        width={60} 
                        height={20}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Link to={`/holdings/${fund.id}`} className={styles.viewLink}>
                        View Details
                      </Link>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </Card>
      </motion.div>
    </div>
  );
}
