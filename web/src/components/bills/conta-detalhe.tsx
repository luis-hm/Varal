// Doop: k0kB5dc-Vo / 07 · Detalhe da conta (efJzW9e5vx) + painel de D03 · Contas + Detalhe (cWdVUX2y8H);
// CU06, CU07, CU08; RF14, RN06, RN22, RN30, D2. PDF, Emissão, "Repete", "Já paguei" and reminders
// stay in their stages (06–09).
"use client";

import Link from "next/link";
import { useState, type ReactNode } from "react";
import { TopBar } from "@/components/layout/top-bar";
import { Icon, type IconName } from "@/components/ui/icon";
import { Nome } from "@/components/ui/nome";
import type { ContaDetalhe as Detalhe } from "@/lib/contas/client";
import { dataCivil, dia, diaSemana, partesReais, prazo, quando } from "@/lib/contas/formato";
import { useLinkPdfConta } from "@/lib/contas/hooks";
import { Button } from "@/components/ui/button";
import { linhaHistorico, type Trecho } from "@/lib/contas/historico";
import { ContaFolha } from "./conta-folha";
import { CopiarCodigo } from "./copiar-codigo";
import { PagamentoAcoes } from "./pagamento-acoes";
import { StatusBadge } from "./status-badge";
import styles from "./contas.module.css";
import instrumentoStyles from "./instrumento.module.css";

/** History text with each person's name on one line (ajuste 29); the rest of the line still wraps. */
const trechos = (t: Trecho[]) => t.map((x, i) => (typeof x === "string" ? x : x.nome && <Nome key={i}>{x.nome}</Nome>));

type Props = {
  conta: Detalhe;
  /** Back (07) and close (D03 panel) both go to the list with the same filters. */
  voltar: string;
};

export function ContaDetalhe({ conta, voltar }: Props) {
  const [editando, setEditando] = useState(false);
  const [edicao, setEdicao] = useState(0); // fresh form state on every opening, kept mounted to return focus
  const pdf = useLinkPdfConta();
  const [inteiro, centavos] = partesReais(conta.valor_centavos);
  const st = conta.status_exibido;
  const aberta = conta.status !== "cancelada" && conta.status !== "paga" && conta.status !== "confirmada";
  const podeEditar = conta.pode_editar && conta.status !== "cancelada";
  const instrumento = conta.instrumento;
  const codigo = instrumento?.codigo ?? instrumento?.chave_pix;
  const rotuloCodigo = instrumento?.tipo === "pix" ? instrumento.chave_pix ? "Chave Pix" : "Pix copia e cola" : "Linha digitável";
  const editar = podeEditar ? (
    <button type="button" aria-label="Editar conta" onClick={() => {
        setEdicao((n) => n + 1);
        setEditando(true);
      }} aria-haspopup="dialog">
      <Icon name="manual" size="md" />
    </button>
  ) : undefined;
  // Ajuste 29: people's names and e-mails stay on one line (ellipsis + title); house names keep wrapping (decision 11).
  const linhas: [IconName, string, ReactNode][] = [
    ...(conta.subgrupo ? [["casa", "Casa", conta.subgrupo.nome] as [IconName, string, ReactNode]] : []),
    ...(conta.espaco.tipo === "grupo"
      ? ([
          ["perfil", "Quem paga", <Nome key="p">{!conta.pagador ? "Ninguém" : conta.pagador.sou_eu ? "Você" : conta.pagador.nome}</Nome>],
          conta.visibilidade === "grupo"
            ? ["grupo", "Quem vê", "Todo o grupo"]
            : ["cadeado", "Quem vê", conta.quem_ve.length ? (
                <span key="v" className={styles.pessoas}>
                  <span>Só </span>
                  {conta.quem_ve.map((p, i) => (
                    <span key={p.id} className={styles.pessoa}>
                      <Nome>{p.nome}</Nome>{i < conta.quem_ve.length - 1 ? ", " : ""}
                    </span>
                  ))}
                </span>
              ) : "Ninguém"],
        ] as [IconName, string, ReactNode][])
      : []),
    [
      "manual",
      "Criada por",
      <span key="c" className={styles.nomeData}>
        <Nome>{conta.criador.sou_eu ? "Você" : conta.criador.nome}</Nome>, {dia(conta.criado_em)}
      </span>,
    ],
    ...(instrumento?.data_emissao ? [["calendario", "Emissão", dataCivil(instrumento.data_emissao)] as [IconName, string, ReactNode]] : []),
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
                <Icon name={conta.subgrupo ? "casa" : instrumento?.tipo === "pix" ? "pix" : codigo ? "boleto" : "manual"} />
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

        {instrumento && codigo && (
          <section className={`${instrumentoStyles.codigo} ${styles.in} ${styles.d1}`} aria-label={rotuloCodigo}>
            <h2 className={instrumentoStyles.titulo}><Icon name={instrumento.tipo === "pix" ? "pix" : "boleto"} size="sm" />{rotuloCodigo}</h2>
            <p className={instrumentoStyles.texto}>{codigo}</p>
            {instrumento.beneficiario && <p className={instrumentoStyles.nota}>Beneficiário informado: <Nome>{instrumento.beneficiario}</Nome></p>}
            <CopiarCodigo key={codigo} codigo={codigo} chave={!!instrumento.chave_pix} />
          </section>
        )}

        {conta.documento_pdf && (
          <section className={instrumentoStyles.codigo} aria-label="PDF do boleto">
            <h2 className={instrumentoStyles.titulo}><Icon name="pdf" size="md" /> PDF do boleto</h2>
            <p className={instrumentoStyles.texto}>{conta.documento_pdf.nome}</p>
            <Button tone="secondary" icon="baixar" label={pdf.isPending ? "Preparando…" : "Baixar PDF"} disabled={pdf.isPending} onClick={() => {
              pdf.mutate(conta.id, { onSuccess: ({ url }) => {
                const link = document.createElement("a");
                link.href = url;
                link.target = "_blank";
                link.rel = "noopener noreferrer";
                link.click();
              } });
            }} />
            {pdf.error && <p role="alert">Não foi possível abrir o PDF. Tente novamente.</p>}
          </section>
        )}

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
                  <b>{trechos(forte)}</b>
                  {resto.length > 0 && <> · {trechos(resto)}</>} · {quando(h.criado_em)}
                </li>
              );
            })}
          </ol>
        </section>
        <PagamentoAcoes key={conta.id} conta={conta} />
      </div>
      {edicao > 0 && <ContaFolha key={edicao} open={editando} onClose={() => setEditando(false)} conta={conta} />}
    </article>
  );
}
