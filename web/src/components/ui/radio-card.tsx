// Doop: k0kB5dc-Vo / componente RadioCard (11 · Convidar membro, M05)
import type { InputHTMLAttributes } from "react";
import styles from "./radio-card.module.css";

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "checked" | "title"> & {
  /** Doop state: "on" is the checked option. */
  state?: "off" | "on";
  title: string;
  text: string;
};

// A native radio inside the label: arrow keys, focus and screen readers come from the platform.
export function RadioCard({ state = "off", title, text, className, ...input }: Props) {
  return (
    <label className={className ? `${styles.rc} ${className}` : styles.rc} data-state={state}>
      <input type="radio" className={styles.input} checked={state === "on"} {...input} />
      <span className={styles.dot} aria-hidden="true" />
      <span className={styles.body}>
        <span className={styles.tt}>{title}</span>
        <span className={styles.tx}>{text}</span>
      </span>
    </label>
  );
}

/** Same card without a choice (role shown on the invite acceptance screen). */
export function PapelCard({ title, text }: { title: string; text: string }) {
  return (
    <div className={styles.rc} data-state="off">
      <span className={styles.body}>
        <span className={styles.tt}>{title}</span>
        <span className={styles.tx}>{text}</span>
      </span>
    </div>
  );
}
