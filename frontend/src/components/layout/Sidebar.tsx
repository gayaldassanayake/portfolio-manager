import { NavLink } from 'react-router-dom';
import { cn } from '../../lib/utils';
import styles from './Sidebar.module.css';

// Icons as inline SVGs for the Swiss Finance aesthetic
const icons = {
  dashboard: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="2" y="2" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
      <rect x="11" y="2" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
      <rect x="2" y="11" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
      <rect x="11" y="11" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  ),
  holdings: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M2 5C2 3.89543 2.89543 3 4 3H16C17.1046 3 18 3.89543 18 5V15C18 16.1046 17.1046 17 16 17H4C2.89543 17 2 16.1046 2 15V5Z" stroke="currentColor" strokeWidth="1.5" />
      <path d="M2 8H18" stroke="currentColor" strokeWidth="1.5" />
      <path d="M6 12H8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M11 12H14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  transactions: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M4 7H16M4 7L7 4M4 7L7 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M16 13H4M16 13L13 10M16 13L13 16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  performance: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M3 17L7 12L11 14L17 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M14 6H17V9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  fixedDeposits: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="2" y="5" width="16" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="M2 8H18" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="10" cy="11.5" r="1.5" fill="currentColor" />
    </svg>
  ),
  settings: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="3" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M17 10C17 10.5 16.9 11 16.7 11.4L18 12.4L16.5 15L14.9 14.3C14.3 14.8 13.7 15.2 13 15.4V17H11V15.4C10.3 15.2 9.7 14.8 9.1 14.3L7.5 15L6 12.4L7.3 11.4C7.1 11 7 10.5 7 10C7 9.5 7.1 9 7.3 8.6L6 7.6L7.5 5L9.1 5.7C9.7 5.2 10.3 4.8 11 4.6V3H13V4.6C13.7 4.8 14.3 5.2 14.9 5.7L16.5 5L18 7.6L16.7 8.6C16.9 9 17 9.5 17 10Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  ),
};

const navItems = [
  { label: 'Dashboard', path: '/', icon: icons.dashboard },
  { label: 'Holdings', path: '/holdings', icon: icons.holdings },
  { label: 'Transactions', path: '/transactions', icon: icons.transactions },
  { label: 'Performance', path: '/performance', icon: icons.performance },
  { label: 'Fixed Deposits', path: '/fixed-deposits', icon: icons.fixedDeposits },
  { label: 'Settings', path: '/settings', icon: icons.settings },
];

export function Sidebar() {
  return (
    <aside className={styles.sidebar}>
      {/* Logo / Brand */}
      <div className={styles.brand}>
        <div className={styles.logo}>
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect x="2" y="2" width="24" height="24" rx="6" stroke="currentColor" strokeWidth="2" />
            <path d="M8 18L12 12L16 15L20 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="20" cy="9" r="2" fill="currentColor" />
          </svg>
        </div>
        <div className={styles.brandText}>
          <span className={styles.brandName}>Portfolio</span>
          <span className={styles.brandTagline}>Manager</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className={styles.nav}>
        <ul className={styles.navList}>
          {navItems.map((item, index) => (
            <li key={item.path} style={{ animationDelay: `${index * 50}ms` }}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  cn(styles.navLink, isActive && styles.active)
                }
              >
                <span className={styles.navIcon}>{item.icon}</span>
                <span className={styles.navLabel}>{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className={styles.footer}>
        <div className={styles.footerContent}>
          <span className={styles.footerLabel}>Swiss Finance</span>
          <span className={styles.footerVersion}>v1.0.0</span>
        </div>
      </div>
    </aside>
  );
}
