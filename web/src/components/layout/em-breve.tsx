// Placeholder for a section whose screen arrives in a later stage. Doop: k0kB5dc-Vo / componente TopBar.
import type { ReactNode } from "react";
import { TopBar } from "./top-bar";
import styles from "./em-breve.module.css";

export function EmBreve({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <>
      <TopBar title={title} />
      <div className={styles.body}>
        <p>Em breve</p>
        {children}
      </div>
    </>
  );
}
