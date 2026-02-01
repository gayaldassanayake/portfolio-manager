import { cn } from '../../lib/utils';
import styles from './Badge.module.css';

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'positive' | 'negative' | 'warning' | 'accent';
  size?: 'sm' | 'md';
}

export function Badge({
  children,
  className,
  variant = 'default',
  size = 'md',
}: BadgeProps) {
  return (
    <span className={cn(styles.badge, styles[variant], styles[size], className)}>
      {children}
    </span>
  );
}

// Specialized badges for common use cases
interface ValueBadgeProps {
  value: number;
  className?: string;
  showSign?: boolean;
  formatter?: (value: number) => string;
}

export function ValueBadge({
  value,
  className,
  showSign = true,
  formatter = (v) => `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`,
}: ValueBadgeProps) {
  const variant = value > 0 ? 'positive' : value < 0 ? 'negative' : 'default';
  
  return (
    <Badge variant={variant} className={className}>
      {showSign && value > 0 && '+'}
      {formatter(value)}
    </Badge>
  );
}

interface TypeBadgeProps {
  type: 'buy' | 'sell';
  className?: string;
}

export function TypeBadge({ type, className }: TypeBadgeProps) {
  return (
    <Badge 
      variant={type === 'buy' ? 'positive' : 'negative'} 
      className={className}
      size="sm"
    >
      {type.toUpperCase()}
    </Badge>
  );
}
