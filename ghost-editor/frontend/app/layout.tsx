import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import styles from "./layout.module.css";

export const metadata: Metadata = {
  title: "Ghost-Editor | AI Documentation",
  description: "AI agent that automatically updates code documentation.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className={styles.appContainer}>
          <Sidebar />
          <main className={styles.mainContent}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
