"use client";

import styles from './DashboardStats.module.css';

export default function DashboardStats() {
  const stats = [
    {
      id: 1,
      label: 'Tracked Repositories',
      value: '12',
      icon: '📂',
      meta: '+2 this week',
      trend: 'up'
    },
    {
      id: 2,
      label: 'Active PRs Analysed',
      value: '34',
      icon: '🔍',
      meta: '+8 today',
      trend: 'up'
    },
    {
      id: 3,
      label: 'Docs Auto-Updated',
      value: '156',
      icon: '✨',
      meta: '98% success rate',
      trend: 'neutral'
    }
  ];

  return (
    <div className={styles.grid}>
      {stats.map((stat, i) => (
        <div 
          key={stat.id} 
          className={`${styles.card} glass-panel animate-fade-in animate-delay-${i + 1}`}
        >
          <div className={styles.header}>
            <span className={styles.icon}>{stat.icon}</span>
            <span>{stat.label}</span>
          </div>
          <div className={styles.value}>{stat.value}</div>
          <div className={`${styles.meta} ${stat.trend === 'neutral' ? styles.neutral : ''}`}>
            {stat.trend === 'up' && '↗'} {stat.meta}
          </div>
        </div>
      ))}
    </div>
  );
}
