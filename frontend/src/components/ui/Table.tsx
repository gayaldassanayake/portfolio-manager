import { cn } from '../../lib/utils';
import styles from './Table.module.css';

interface TableProps {
  children: React.ReactNode;
  className?: string;
}

export function Table({ children, className }: TableProps) {
  return (
    <div className={styles.wrapper}>
      <table className={cn(styles.table, className)}>
        {children}
      </table>
    </div>
  );
}

interface TableHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export function TableHeader({ children, className }: TableHeaderProps) {
  return (
    <thead className={cn(styles.header, className)}>
      {children}
    </thead>
  );
}

interface TableBodyProps {
  children: React.ReactNode;
  className?: string;
}

export function TableBody({ children, className }: TableBodyProps) {
  return (
    <tbody className={cn(styles.body, className)}>
      {children}
    </tbody>
  );
}

interface TableRowProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export function TableRow({ children, className, onClick, hoverable = true }: TableRowProps) {
  return (
    <tr 
      className={cn(
        styles.row, 
        hoverable && styles.hoverable,
        onClick && styles.clickable, 
        className
      )}
      onClick={onClick}
    >
      {children}
    </tr>
  );
}

interface TableHeadProps {
  children: React.ReactNode;
  className?: string;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  sorted?: 'asc' | 'desc' | false;
  onSort?: () => void;
}

export function TableHead({ 
  children, 
  className, 
  align = 'left',
  sortable = false,
  sorted = false,
  onSort,
}: TableHeadProps) {
  return (
    <th 
      className={cn(
        styles.head, 
        styles[`align-${align}`],
        sortable && styles.sortable,
        sorted && styles.sorted,
        className
      )}
      onClick={sortable ? onSort : undefined}
    >
      <span className={styles.headContent}>
        {children}
        {sortable && (
          <span className={styles.sortIcon}>
            {sorted === 'asc' && (
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M6 3L10 8H2L6 3Z" fill="currentColor" />
              </svg>
            )}
            {sorted === 'desc' && (
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M6 9L2 4H10L6 9Z" fill="currentColor" />
              </svg>
            )}
            {!sorted && (
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M6 2L9 5H3L6 2Z" fill="currentColor" opacity="0.3" />
                <path d="M6 10L3 7H9L6 10Z" fill="currentColor" opacity="0.3" />
              </svg>
            )}
          </span>
        )}
      </span>
    </th>
  );
}

interface TableCellProps {
  children: React.ReactNode;
  className?: string;
  align?: 'left' | 'center' | 'right';
  mono?: boolean;
}

export function TableCell({ 
  children, 
  className, 
  align = 'left',
  mono = false,
}: TableCellProps) {
  return (
    <td className={cn(
      styles.cell, 
      styles[`align-${align}`],
      mono && styles.mono,
      className
    )}>
      {children}
    </td>
  );
}

// Empty state component
interface TableEmptyProps {
  colSpan: number;
  message?: string;
  icon?: React.ReactNode;
}

export function TableEmpty({ 
  colSpan, 
  message = 'No data available',
  icon,
}: TableEmptyProps) {
  return (
    <tr>
      <td colSpan={colSpan} className={styles.empty}>
        {icon && <span className={styles.emptyIcon}>{icon}</span>}
        <span className={styles.emptyMessage}>{message}</span>
      </td>
    </tr>
  );
}

// Loading skeleton for table
interface TableSkeletonProps {
  rows?: number;
  columns?: number;
}

export function TableSkeleton({ rows = 5, columns = 5 }: TableSkeletonProps) {
  return (
    <>
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <tr key={rowIndex} className={styles.row}>
          {Array.from({ length: columns }).map((_, colIndex) => (
            <td key={colIndex} className={styles.cell}>
              <div className={cn(styles.skeleton, 'skeleton')} />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}
