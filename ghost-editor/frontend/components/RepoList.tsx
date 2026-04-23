"use client";

import styles from './RepoList.module.css';

export default function RepoList() {
  const repos = [
    {
      id: 1,
      name: 'ghost-editor-core',
      url: 'github.com/org/ghost-editor-core',
      status: 'active',
      lastSync: '2 mins ago'
    },
    {
      id: 2,
      name: 'legal-auditor-frontend',
      url: 'github.com/org/legal-auditor',
      status: 'syncing',
      lastSync: 'Syncing now...'
    },
    {
      id: 3,
      name: 'data-generator-api',
      url: 'github.com/org/data-generator',
      status: 'active',
      lastSync: '5 hours ago'
    }
  ];

  return (
    <div className={`${styles.container} animate-fade-in animate-delay-3`}>
      <h3 className={styles.title}>
        <span>Tracked Repositories</span>
      </h3>
      
      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Repository</th>
              <th>Status</th>
              <th>Last Auto-Sync</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {repos.map((repo) => (
              <tr key={repo.id}>
                <td>
                  <div className={styles.repoName}>
                    <span className={styles.repoIcon}>📦</span>
                    <div>
                      <div>{repo.name}</div>
                      <div className={styles.url}>{repo.url}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <span className={`${styles.status} ${styles[repo.status]}`}>
                    {repo.status === 'active' ? 'Active' : 'Syncing'}
                  </span>
                </td>
                <td className={styles.url}>{repo.lastSync}</td>
                <td>
                  <button className={styles.actionBtn}>Force Sync</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
