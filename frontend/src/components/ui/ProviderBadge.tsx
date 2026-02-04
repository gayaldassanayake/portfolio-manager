import { cn } from '../../lib/utils';
import type { Provider } from '../../types';
import styles from './ProviderBadge.module.css';

interface ProviderBadgeProps {
  provider: Provider | null;
  className?: string;
  showIcon?: boolean;
}

export function ProviderBadge({ provider, className, showIcon = false }: ProviderBadgeProps) {
  if (!provider) {
    return (
      <span className={cn(styles.badge, styles.none, className)}>
        {showIcon && <span className={styles.icon}>○</span>}
        No Provider
      </span>
    );
  }

  const providerConfig = {
    yahoo: {
      label: 'Yahoo',
      icon: '◈',
    },
    cal: {
      label: 'CAL',
      icon: '◆',
    },
  };

  const config = providerConfig[provider];

  return (
    <span className={cn(styles.badge, styles[provider], className)}>
      {showIcon && <span className={styles.icon}>{config.icon}</span>}
      {config.label}
    </span>
  );
}
