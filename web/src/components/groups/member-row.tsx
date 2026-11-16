// Doop: k0kB5dc-Vo / componente MemberRow (10 · Grupo, D04 · Grupo)
import { Nome } from "@/components/ui/nome";
import type { Papel } from "@/lib/grupos/client";
import { papeis } from "@/lib/grupos/papeis";
import styles from "./member-row.module.css";

type Props = {
  role?: Papel;
  initials: string;
  name: string;
  detail?: string;
  /** Admin only: the row opens the member's management sheet. */
  onClick?: () => void;
};

export function MemberRow({ role = "membro", initials, name, detail, onClick }: Props) {
  const content = (
    <>
      <span className={styles.av} aria-hidden="true">{initials}</span>
      <span className={styles.bd}>
        {/* Ajuste 29: a long name or e-mail is cut on one line, whole in title. */}
        <Nome className={styles.nm}>{name}</Nome>
        {detail && <Nome className={styles.dt}>{detail}</Nome>}
      </span>
      {/* RNF09: the role is text, never colour alone. */}
      <span className={styles.rl}>{papeis[role].title}</span>
    </>
  );
  return onClick ? (
    <button type="button" className={styles.mr} data-role={role} onClick={onClick} aria-haspopup="dialog">
      {content}
    </button>
  ) : (
    <div className={styles.mr} data-role={role}>{content}</div>
  );
}
