"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import styles from './Sidebar.module.css';

export default function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    { label: 'Dashboard', href: '/', icon: '📊' },
    { label: 'Repositories', href: '/repos', icon: '📂' },
    { label: 'Jobs', href: '/jobs', icon: '⚡' },
    { label: 'Settings', href: '/settings', icon: '⚙️' },
  ];

  return (
    <aside className={`${styles.sidebar} glass-panel`}>
      <div className={styles.logo}>
        <span className={styles.logoIcon}>👻</span>
        <h2>Ghost-Editor</h2>
      </div>

      <nav className={styles.nav}>
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link 
              key={item.href} 
              href={item.href}
              className={`${styles.navItem} ${isActive ? styles.active : ''}`}
            >
              <span className={styles.icon}>{item.icon}</span>
              {item.label}
              {isActive && <div className={styles.activeIndicator} />}
            </Link>
          );
        })}
      </nav>

      <div className={styles.status}>
        <div className={styles.statusDot} />
        <span>Agent Ready</span>
      </div>
    </aside>
  );
}
