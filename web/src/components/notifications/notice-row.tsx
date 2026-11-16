// Doop: k0kB5dc-Vo / NoticeRow; 04 · Avisos + D06 · Avisos, 02/D02 · Início.
import type { ReactNode } from "react";
import styles from "./notice-row.module.css";

type Props = {
  tone?: "info" | "vence" | "vencida" | "aguardando" | "pago";
  unread?: "no" | "yes";
  title: string;
  text: string;
  time: string;
  icon: ReactNode;
  onClick: () => void;
  disabled?: boolean;
};

export function NoticeRow({ tone = "info", unread = "no", title, text, time, icon, onClick, disabled }: Props) {
  return (
    <button type="button" className={styles.row} data-tone={tone} data-unread={unread} onClick={onClick} disabled={disabled}>
      <span className={styles.icon} aria-hidden="true">{icon}</span>
      <span className={styles.body}>
        <span className={styles.title}>{title}</span>
        <span className={styles.text}>{text}</span>
        {unread === "yes" && <span className={styles.srOnly}>Não lido</span>}
      </span>
      <span className={styles.time}>{time}</span>
      {unread === "yes" && <span className={styles.dot} aria-hidden="true" />}
    </button>
  );
}
