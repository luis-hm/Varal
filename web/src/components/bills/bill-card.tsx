// Doop: k0kB5dc-Vo / componente BillCard (Mwqabjlc2s), used in 02, 03, D02, D03.
import Link from "next/link";
import type { ReactNode } from "react";
import { Icon } from "@/components/ui/icon";
import type { Conta } from "@/lib/contas/client";
import { metaConta, reais } from "@/lib/contas/formato";
import { StatusBadge } from "./status-badge";
import styles from "./bill-card.module.css";

type Props = {
  title: string;
  meta: string;
  value: string;
  /** Slot icon: house or bill type. */
  icon: ReactNode;
  /** Slot status: StatusBadge. */
  status: ReactNode;
  href: string;
  /** D03: the open bill gets the ink border. */
  selected?: boolean;
  /** D2: struck-through value and reduced opacity. */
  cancelled?: boolean;
};

export function BillCard({ title, meta, value, icon, status, href, selected, cancelled }: Props) {
  return (
    <Link
      className={styles.bill}
      href={href}
      data-selected={selected || undefined}
      data-cancelled={cancelled || undefined}
      aria-current={selected ? "true" : undefined}
    >
      <span className={styles.lead}>{icon}</span>
      <span className={styles.main}>
        <span className={styles.t}>{title}</span>
        <span className={styles.m}>{meta}</span>
        <span className={styles.s}>{status}</span>
      </span>
      <span className={styles.v}>{value}</span>
    </Link>
  );
}

/** A Conta from the API as a BillCard: house icon when it has one, otherwise the manual icon (no instrument yet). */
export function ContaCard({ conta, href, selected }: { conta: Conta; href: string; selected?: boolean }) {
  return (
    <BillCard
      title={conta.descricao}
      meta={metaConta(conta)}
      value={reais(conta.valor_centavos)}
      icon={<Icon name={conta.subgrupo ? "casa" : "manual"} size="md" />}
      status={<StatusBadge status={conta.status_exibido} />}
      href={href}
      selected={selected}
      cancelled={conta.status === "cancelada"}
    />
  );
}
