import styles from './page.module.css';
import DashboardStats from '@/components/DashboardStats';
import RepoList from '@/components/RepoList';

export default function Home() {
  return (
    <div className="animate-fade-in">
      <header className={styles.header}>
        <h1 className={styles.title}>Dashboard</h1>
        <p className={styles.subtitle}>Overview of your AI documentation agent activity.</p>
      </header>

      <section className={`${styles.hero} glass-panel`}>
        <div className={styles.heroContent}>
          <h2 className={styles.heroTitle}>Agent is Active and Listening</h2>
          <p className={styles.heroDesc}>
            Ghost-Editor is currently monitoring 12 repositories for Pull Requests. 
            When a PR is merged, the agent will automatically analyze the diff and 
            update the corresponding documentation.
          </p>
        </div>
        <button className={styles.heroAction}>
          + Connect Repository
        </button>
      </section>

      <DashboardStats />
      
      <RepoList />
    </div>
  );
}
