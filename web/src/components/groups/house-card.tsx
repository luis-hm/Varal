// Doop: k0kB5dc-Vo / componente HouseCard (10 · Grupo, D04 · Grupo, D02 · Início), now a category card (COR-04/11):
// the card opens the category's bills; editing is a separate small button, never the main click.
import Link from "next/link";
import type { CSSProperties } from "react";
import { Icon, type IconName } from "@/components/ui/icon";
import styles from "./house-card.module.css";

type Props = {
  label: string;
  caption: string;
  "caption-2"?: string;
  icon?: IconName;
  /** Paid share 0–100. Without it there is no bar. */
  progress?: number;
  /** Where the card goes: the category's bills. */
  href?: string;
  /** Admin only: opens the category's edit sheet. */
  onEditar?: () => void;
};

export function HouseCard({ label, caption, "caption-2": caption2, icon = "casa", progress, href, onEditar }: Props) {
  const content = (
    <>
      <span className={styles.ib}>
        <Icon name={icon} size="md" />
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
  return (
    <div className={styles.wrap}>
      {href ? (
        <Link href={href} className={styles.house}>
          {content}
        </Link>
      ) : (
        <div className={styles.house}>{content}</div>
      )}
      {onEditar && (
        <button type="button" className={styles.editar} onClick={onEditar} aria-label={`Editar ${label}`} aria-haspopup="dialog">
          <Icon name="manual" size="sm" />
        </button>
      )}
    </div>
  );
}
