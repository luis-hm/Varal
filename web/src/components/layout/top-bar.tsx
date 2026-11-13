// Doop: k0kB5dc-Vo / componente TopBar
import Link from "next/link";
import type { ReactNode } from "react";
import { Icon } from "@/components/ui/icon";
import styles from "./top-bar.module.css";

type Props = {
  title: string;
  /** Back link. Top-level sections have none; an empty slot keeps the title centred. */
  backHref?: string;
  action?: ReactNode;
};

export function TopBar({ title, backHref, action }: Props) {
  return (
    <header className={styles.top}>
      {backHref ? (
        <Link className={styles.bk} href={backHref} aria-label="Voltar">
          <Icon name="voltar" size="md" />
        </Link>
      ) : (
        <span className={styles.side} />
      )}
      <h1 className={styles.tt}>{title}</h1>
      <span className={styles.side}>{action}</span>
    </header>
  );
}
