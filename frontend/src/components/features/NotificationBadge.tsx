import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Badge } from '../ui';
import { usePendingNotifications, useDismissNotifications } from '../../api/hooks';
import { formatDate } from '../../lib/formatters';
import styles from './NotificationBadge.module.css';

export function NotificationBadge() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { data: notifications, isLoading } = usePendingNotifications();
  const dismissMutation = useDismissNotifications();

  const count = notifications?.length || 0;

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleDismissAll = async () => {
    if (!notifications || notifications.length === 0) return;

    const ids = notifications.map((n) => n.id);
    await dismissMutation.mutateAsync(ids);
    setIsOpen(false);
  };

  const handleDismiss = async (id: number) => {
    await dismissMutation.mutateAsync([id]);
  };

  const getNotificationTypeBadge = (type: string) => {
    switch (type) {
      case 'maturity_30_days':
        return <Badge variant="warning">30 Days</Badge>;
      case 'maturity_7_days':
        return <Badge variant="negative">7 Days</Badge>;
      case 'maturity_today':
        return <Badge variant="negative">Today</Badge>;
      default:
        return <Badge>{type}</Badge>;
    }
  };

  // Don't show if no notifications
  if (count === 0) {
    return null;
  }

  return (
    <div className={styles.container} ref={dropdownRef}>
      <button
        className={styles.trigger}
        onClick={() => setIsOpen(!isOpen)}
        aria-label={`${count} notification${count !== 1 ? 's' : ''}`}
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path
            d="M10 2C8.34315 2 7 3.34315 7 5V5.5C7 7.433 6.433 9 5.5 10C4.567 11 4 12.433 4 14V15H16V14C16 12.433 15.433 11 14.5 10C13.567 9 13 7.433 13 5.5V5C13 3.34315 11.6569 2 10 2Z"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M8 15V16C8 17.1046 8.89543 18 10 18C11.1046 18 12 17.1046 12 16V15"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
        {count > 0 && <span className={styles.badge}>{count > 9 ? '9+' : count}</span>}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            className={styles.dropdown}
            initial={{ opacity: 0, y: -8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.95 }}
            transition={{ duration: 0.15 }}
          >
            <div className={styles.header}>
              <h3 className={styles.title}>FD Maturity Notifications</h3>
              <button
                className={styles.dismissAllButton}
                onClick={handleDismissAll}
                disabled={dismissMutation.isPending}
              >
                Dismiss All
              </button>
            </div>

            <div className={styles.list}>
              {isLoading ? (
                <div className={styles.loading}>Loading...</div>
              ) : notifications && notifications.length > 0 ? (
                notifications.map((notification) => (
                  <div key={notification.id} className={styles.item}>
                    <div className={styles.itemHeader}>
                      <span className={styles.institution}>
                        {notification.institution_name}
                      </span>
                      {getNotificationTypeBadge(notification.notification_type)}
                    </div>
                    <div className={styles.itemDetails}>
                      <span className={styles.account}>
                        Account: {notification.account_number}
                      </span>
                      <span className={styles.maturityDate}>
                        Matures: {formatDate(notification.maturity_date)}
                      </span>
                    </div>
                    <button
                      className={styles.dismissButton}
                      onClick={() => handleDismiss(notification.id)}
                      disabled={dismissMutation.isPending}
                      aria-label="Dismiss notification"
                    >
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <path
                          d="M2 2L10 10M2 10L10 2"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          strokeLinecap="round"
                        />
                      </svg>
                    </button>
                  </div>
                ))
              ) : (
                <div className={styles.empty}>No notifications</div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
