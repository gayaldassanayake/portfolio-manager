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
};

const navItems = [
  { label: 'Dashboard', path: '/', icon: icons.dashboard },
  { label: 'Holdings', path: '/holdings', icon: icons.holdings },
  { label: 'Transactions', path: '/transactions', icon: icons.transactions },
  { label: 'Performance', path: '/performance', icon: icons.performance },
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
