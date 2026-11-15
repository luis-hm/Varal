// Doop: k0kB5dc-Vo / 07 · Detalhe da conta (efJzW9e5vx) + painel de D03 · Contas + Detalhe (cWdVUX2y8H);
// CU06, CU07; RN06, RN22, RN30, D2. Not here until their stage: barcode, Copiar, PDF, Emissão, "Repete",
// "Já paguei" and the reminder footer (05–09).
"use client";

import Link from "next/link";
import { useState } from "react";
import { TopBar } from "@/components/layout/top-bar";
import { Icon, type IconName } from "@/components/ui/icon";
import type { ContaDetalhe as Detalhe } from "@/lib/contas/client";
import { dia, diaSemana, partesReais, prazo, quando } from "@/lib/contas/formato";
import { linhaHistorico } from "@/lib/contas/historico";
import { ContaFolha } from "./conta-folha";
import { StatusBadge } from "./status-badge";
import styles from "./contas.module.css";

type Props = {
  conta: Detalhe;
  /** Back (07) and close (D03 panel) both go to the list with the same filters. */
  voltar: string;
};

export function ContaDetalhe({ conta, voltar }: Props) {
  const [editando, setEditando] = useState(false);
  const [edicao, setEdicao] = useState(0); // fresh form state on every opening, kept mounted to return focus
  const [inteiro, centavos] = partesReais(conta.valor_centavos);
  const st = conta.status_exibido;
  const aberta = conta.status !== "cancelada" && conta.status !== "paga" && conta.status !== "confirmada";
  const podeEditar = conta.pode_editar && conta.status !== "cancelada";
  const editar = podeEditar ? (
    <button type="button" aria-label="Editar conta" onClick={() => {
        setEdicao((n) => n + 1);
        setEditando(true);
      }} aria-haspopup="dialog">
      <Icon name="manual" size="md" />
    </button>
  ) : undefined;
  const linhas: [IconName, string, string][] = [
    ...(conta.subgrupo ? [["casa", "Casa", conta.subgrupo.nome] as [IconName, string, string]] : []),
    ...(conta.espaco.tipo === "grupo"
      ? ([
          ["perfil", "Quem paga", !conta.pagador ? "Ninguém" : conta.pagador.sou_eu ? "Você" : conta.pagador.nome],
          conta.visibilidade === "grupo"
            ? ["grupo", "Quem vê", "Todo o grupo"]
            : ["cadeado", "Quem vê", conta.acesso.length ? `Só ${conta.acesso.map((p) => p.nome).join(", ")}` : "Só quem criou e quem paga"],
        ] as [IconName, string, string][])
      : []),
    ["manual", "Criada por", `${conta.criador.sou_eu ? "Você" : conta.criador.nome}, ${dia(conta.criado_em)}`],
  ];

  return (
    <article className={styles.detalhe} aria-label="Detalhe da conta">
      <div className={styles.mobTop}>
        <TopBar title="Conta" backHref={voltar} action={editar} />
      </div>
      <div className={styles.painelBarra}>
        {editar && <span className={styles.redondo}>{editar}</span>}
        <Link className={styles.redondo} href={voltar} aria-label="Fechar detalhe" scroll={false}>
          <Icon name="fechar" size="md" />
        </Link>
      </div>

      <div className={styles.corpo}>
        <section className={`${styles.resumo} ${styles.in}`}>
          <div className={styles.fio} aria-hidden="true">
            <svg viewBox="0 0 366 40" preserveAspectRatio="none">
              <path d="M-4 6 Q183 40 370 6" />
            </svg>
            <span className={styles.placa} data-status={st}>
              <i />
              <b>
                <Icon name={conta.subgrupo ? "casa" : "manual"} />
              </b>
            </span>
          </div>
          <StatusBadge status={st} />
          <h1 className={styles.titulo}>{conta.descricao}</h1>
          <p className={styles.valor} data-cancelada={conta.status === "cancelada" || undefined}>
            {inteiro}
            <span>{centavos}</span>
          </p>
          <p className={styles.vence}>
            {st === "vencida" ? "Venceu " : aberta ? "Vence " : "Vencimento "}
            <b data-status={st}>{diaSemana(conta.vencimento)}</b>
            {aberta && ` · ${prazo(conta.dias_para_vencer)}`}
          </p>
        </section>

        <section className={`${styles.info} ${styles.in} ${styles.d1}`} aria-label="Informações">
          {linhas.map(([icon, rotulo, texto]) => (
            <div key={rotulo} className={styles.ir}>
              <Icon name={icon} size="md" />
              <span>{rotulo}</span>
              <b>{texto}</b>
            </div>
          ))}
        </section>

        <section className={`${styles.historico} ${styles.in} ${styles.d2}`} aria-labelledby="historico-t">
          <h2 id="historico-t">Histórico</h2>
          <ol>
            {[...conta.historico].reverse().map((h, i) => {
              const [forte, resto] = linhaHistorico(h);
              return (
                <li key={i}>
                  <b>{forte}</b>
                  {resto && ` · ${resto}`} · {quando(h.criado_em)}
                </li>
              );
            })}
          </ol>
        </section>
      </div>
      {edicao > 0 && <ContaFolha key={edicao} open={editando} onClose={() => setEditando(false)} conta={conta} />}
    </article>
  );
}
