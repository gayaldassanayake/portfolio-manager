import { motion } from 'motion/react';
import { cn } from '../../lib/utils';
import styles from './StatCard.module.css';

interface StatCardProps {
  label: string;
  value: string;
  change?: {
    value: string;
    type: 'positive' | 'negative' | 'neutral';
  };
  icon?: React.ReactNode;
  trend?: React.ReactNode;
  className?: string;
  delay?: number;
}

export function StatCard({
  label,
  value,
  change,
  icon,
  trend,
  className,
  delay = 0,
}: StatCardProps) {
  return (
    <motion.div
      className={cn(styles.card, className)}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: delay * 0.05, ease: 'easeOut' }}
    >
      <div className={styles.header}>
        <span className={styles.label}>{label}</span>
        {icon && <span className={styles.icon}>{icon}</span>}
      </div>
      
      <div className={styles.content}>
        <span className={styles.value}>{value}</span>
        {change && (
          <span className={cn(styles.change, styles[change.type])}>
            {change.type === 'positive' && (
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M6 2L10 7H2L6 2Z" fill="currentColor" />
              </svg>
            )}
            {change.type === 'negative' && (
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M6 10L2 5H10L6 10Z" fill="currentColor" />
              </svg>
            )}
            {change.value}
          </span>
        )}
      </div>

      {trend && <div className={styles.trend}>{trend}</div>}
    </motion.div>
  );
}

// Large hero stat for the main portfolio value
interface HeroStatProps {
  label: string;
  value: string;
  previousValue?: string;
  change?: {
    amount: string;
    percentage: string;
    type: 'positive' | 'negative' | 'neutral';
  };
  className?: string;
}

export function HeroStat({
  label,
  value,
  previousValue,
  change,
  className,
}: HeroStatProps) {
  return (
    <motion.div
      className={cn(styles.heroCard, className)}
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
    >
      <span className={styles.heroLabel}>{label}</span>
      
      <div className={styles.heroValueWrapper}>
        <motion.span 
          className={styles.heroValue}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          {value}
        </motion.span>
      </div>

      {change && (
        <motion.div 
          className={styles.heroChange}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <span className={cn(styles.heroChangeAmount, styles[change.type])}>
            {change.type === 'positive' && '+'}
            {change.amount}
          </span>
          <span className={cn(styles.heroChangePercent, styles[change.type])}>
            ({change.type === 'positive' && '+'}
            {change.percentage})
          </span>
          {previousValue && (
            <span className={styles.heroPrevious}>
              from {previousValue}
            </span>
          )}
        </motion.div>
      )}

      {/* Decorative glow effect */}
      <div className={cn(styles.heroGlow, change && styles[change.type])} />
    </motion.div>
  );
}
