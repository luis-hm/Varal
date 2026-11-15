// Doop: k0kB5dc-Vo / componente HouseCard (10 · Grupo, D04 · Grupo, D02 · Início)
import type { CSSProperties } from "react";
import { Icon } from "@/components/ui/icon";
import styles from "./house-card.module.css";

type Props = {
  label: string;
  caption: string;
  "caption-2"?: string;
  /** Paid share 0–100. Without it there is no bar (a house with no bills yet, stage 03). */
  progress?: number;
  /** Admin only: opens the house's edit sheet. Stage 04 adds the Doop `house-link`. */
  onClick?: () => void;
};

export function HouseCard({ label, caption, "caption-2": caption2, progress, onClick }: Props) {
  const content = (
    <>
      <span className={styles.ib}>
        <Icon name="casa" size="md" />
      </span>
      <b className={styles.lb}>{label}</b>
      <small>{caption}</small>
      {progress != null && (
        <span className={styles.bar} aria-hidden="true">
          <i style={{ "--progress": `${progress}%` } as CSSProperties} />
        </span>
      )}
      {caption2 && <small>{caption2}</small>}
    </>
  );
  return onClick ? (
    <button type="button" className={styles.house} onClick={onClick} aria-haspopup="dialog">
      {content}
    </button>
  ) : (
    <div className={styles.house}>{content}</div>
  );
}
