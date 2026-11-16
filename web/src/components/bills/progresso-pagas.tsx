// Doop: k0kB5dc-Vo / 02 · Início (JJvrRugL0_) + D02 (SMDsrD8FGT); Q07-7.
import type { CSSProperties } from "react";
import styles from "./progresso-pagas.module.css";

type Props = { pagas: number; total: number; mes: string };

export function ProgressoPagas({ pagas, total, mes }: Props) {
  if (total <= 0) return <p className={styles.legenda}>Nenhuma conta em {mes}.</p>;
  const porcentagem = Math.max(0, Math.min(100, (pagas / total) * 100));
  return <div className={styles.progresso}>
    <div className={styles.barra} role="progressbar" aria-label={`Contas pagas em ${mes}`} aria-valuemin={0} aria-valuemax={total} aria-valuenow={pagas} aria-valuetext={`${pagas} de ${total} contas pagas`}>
      <span style={{ "--progresso": `${porcentagem}%` } as CSSProperties} />
    </div>
    <p className={styles.legenda}>{pagas} de {total} {total === 1 ? "conta paga" : "contas pagas"}</p>
  </div>;
}
