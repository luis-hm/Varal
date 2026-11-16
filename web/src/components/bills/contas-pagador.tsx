// Doop: k0kB5dc-Vo / 13 · Modo simples (mIvLheR2TS) + D05 (YTtAtGSyCI) as reference; componente BillCard.
// Q5: the payer's bills, read only, until stage 10 brings the full simple mode (Copiar, "Já paguei").
"use client";

import { mesAtual, nomeMes } from "@/lib/contas/formato";
import { useContas } from "@/lib/contas/hooks";
import { ContaCard } from "./bill-card";
import styles from "./contas.module.css";

export function ContasPagador({ grupoId }: { grupoId: string }) {
  const mes = mesAtual();
  const lista = useContas(grupoId, { mes });
  if (lista.error) return <p className={styles.vazio} role="alert">{lista.error.message}</p>;
  if (!lista.data) return <p className={styles.vazio} role="status">Carregando contas…</p>;
  if (!lista.data.itens.length) return <p className={styles.vazio}>Nenhuma conta para você pagar em {nomeMes(mes)}.</p>;
  return (
    <ul className={styles.cards} aria-label={`Suas contas de ${nomeMes(mes)}`}>
      {lista.data.itens.map((c) => (
        <li key={c.id}>
          <ContaCard conta={c} href={`/contas/${c.id}`} />
        </li>
      ))}
    </ul>
  );
}
