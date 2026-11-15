// Doop: k0kB5dc-Vo / 03 · Contas (bdiED7Q0I-) + D03 · Contas + Detalhe (cWdVUX2y8H), 07 · Detalhe (efJzW9e5vx);
// CU06, CU07; RF13, RN12, D2, Q9, Q13 (no search), Q14 (Casa / Quem paga), CA15, CA30.
// One route for both sizes: < 1024px /contas/[id] is the 07 alone; from 1024px the list stays and the panel slides in.
"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";
import { useSessao } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Folha } from "@/components/ui/folha";
import { Icon } from "@/components/ui/icon";
import { ApiError } from "@/lib/grupos/client";
import type { Conta, FiltroStatus, Lista } from "@/lib/contas/client";
import { mesAno, mesAtual, nomeMes, plural, reais, somarMes } from "@/lib/contas/formato";
import { useConta, useContas } from "@/lib/contas/hooks";
import { ContaCard } from "./bill-card";
import { ContaDetalhe } from "./conta-detalhe";
import styles from "./contas.module.css";

const chips: [FiltroStatus, string][] = [
  ["todas", "Todas"],
  ["a_pagar", "A pagar"],
  ["vencidas", "Vencidas"],
  ["pagas", "Pagas"],
  ["canceladas", "Canceladas"],
];

/** Groups by due date (03): overdue, next 7 days, later, paid; cancelled ones only under their filter (D2). */
export function agrupar(itens: Conta[]): [string, Conta[]][] {
  const grupos = new Map<string, Conta[]>();
  for (const c of itens) {
    const s = c.status_exibido;
    const nome =
      s === "cancelada" ? "Canceladas" : s === "paga" || s === "confirmada" ? "Pagas" : s === "vencida" ? "Vencidas" : c.dias_para_vencer <= 7 ? "Esta semana" : "Mais adiante";
    grupos.set(nome, [...(grupos.get(nome) ?? []), c]);
  }
  return ["Vencidas", "Esta semana", "Mais adiante", "Pagas", "Canceladas"].flatMap((n) => (grupos.has(n) ? [[n, grupos.get(n)!] as [string, Conta[]]] : []));
}

export function ContasPagina({ contaId }: { contaId?: string }) {
  const router = useRouter();
  const params = useSearchParams();
  const { espaco } = useSessao();
  const conta = useConta(contaId);
  const mes = params.get("mes") || mesAtual();
  const status = (params.get("status") as FiltroStatus | null) || "todas";
  const casa = params.get("casa") || undefined;
  const pagador = params.get("pagador") || undefined;
  // Decision 2: an open bill shows the list of its own space.
  const espacoId = contaId ? (conta.data?.espaco.id ?? (conta.isError ? espaco.id : undefined)) : espaco.id;
  const espacoNome = contaId && conta.data ? conta.data.espaco.nome : espaco.nome;
  const lista = useContas(espacoId, { mes, status, subgrupo: casa, pagador });
  const [filtros, setFiltros] = useState(false);

  const query = (mudar: Record<string, string | undefined>) => {
    const q = new URLSearchParams(params);
    for (const [k, v] of Object.entries(mudar)) {
      if (v && !(k === "status" && v === "todas")) q.set(k, v);
      else q.delete(k);
    }
    return q.size ? `?${q}` : "";
  };
  // CA15: filters live in the URL, so Back restores them.
  const ir = (mudar: Record<string, string | undefined>) => router.push(`${contaId ? `/contas/${contaId}` : "/contas"}${query(mudar)}`, { scroll: false });
  const voltar = `/contas${query({})}`;
  const naoAchou = conta.error instanceof ApiError && conta.error.status === 404;

  return (
    <div className={styles.split} data-aberta={contaId ? "" : undefined}>
      <section className={styles.lista} aria-labelledby="contas-t">
        <header className={styles.cab}>
          <h1 id="contas-t">Contas</h1>
          {lista.data && temFiltros(lista.data) && (
            <button type="button" className={`${styles.redondo} ${styles.mobOnly}`} aria-label="Filtros" aria-haspopup="dialog" onClick={() => setFiltros(true)}>
              <Icon name="filtro" size="md" />
            </button>
          )}
          <nav className={styles.meses} aria-label="Mês">
            <Link className={styles.seta} href={`/contas${query({ mes: somarMes(mes, -1) })}`} aria-label="Mês anterior" scroll={false}>
              <Icon name="chevron" size="sm" className={styles.esq} />
            </Link>
            <span className={styles.mesTx}>
              <b>{mesAno(mes)}</b>
              {/* Q9: every month number names its month. */}
              {lista.data && (
                <small className={styles.mobOnly}>
                  Total de {nomeMes(lista.data.mes)}: {reais(lista.data.total_centavos)} · {espacoNome}
                </small>
              )}
            </span>
            <Link className={styles.seta} href={`/contas${query({ mes: somarMes(mes, 1) })}`} aria-label="Próximo mês" scroll={false}>
              <Icon name="chevron" size="sm" />
            </Link>
          </nav>
        </header>
        {lista.data && (
          <p className={styles.sub}>
            Total de {nomeMes(lista.data.mes)}: {reais(lista.data.total_centavos)} · {plural(lista.data.contagens.todas, "conta", "contas")}
          </p>
        )}

        {lista.data && (
          <div className={styles.chips} role="group" aria-label="Filtrar por status">
            {chips.map(([valor, rotulo]) => (
              <Chip key={valor} label={rotulo} count={lista.data.contagens[valor]} state={status === valor ? "on" : "off"} onClick={() => ir({ status: valor })} />
            ))}
            {temFiltros(lista.data) && (
              <span className={styles.deskOnly}>
                <ChipMenu titulo="Casa" valor={casa} opcoes={lista.data.opcoes.casas.map((c) => [c.id, c.nome])} todos="todas" onEscolher={(v) => ir({ casa: v })} />
                <ChipMenu titulo="Quem paga" valor={pagador} opcoes={opcoesPagador(lista.data)} todos="todos" onEscolher={(v) => ir({ pagador: v })} />
              </span>
            )}
          </div>
        )}

        {lista.error ? (
          <p className={styles.vazio} role="alert">{lista.error.message}</p>
        ) : !lista.data ? (
          <p className={styles.vazio} role="status">Carregando contas…</p>
        ) : !lista.data.itens.length ? (
          <p className={styles.vazio}>{casa || pagador || status !== "todas" ? "Nenhuma conta com esses filtros." : `Nenhuma conta em ${nomeMes(mes)}.`}</p>
        ) : (
          agrupar(lista.data.itens).map(([nome, contas], g) => (
            <section key={nome} aria-label={nome}>
              <p className={`${styles.grupo} ${styles.in}`} style={{ animationDelay: `${g * 0.12}s` }}>
                <span>{nome}</span>
                <span>{reais(contas.reduce((s, c) => s + c.valor_centavos, 0))}</span>
              </p>
              <ul className={styles.cards}>
                {contas.map((c, i) => (
                  <li key={c.id} className={styles.in} style={{ animationDelay: `${g * 0.12 + (i + 1) * 0.06}s` }}>
                    <ContaCard conta={c} href={`/contas/${c.id}${query({})}`} selected={c.id === contaId} />
                  </li>
                ))}
              </ul>
            </section>
          ))
        )}
      </section>

      <aside className={styles.painel} key={contaId} aria-label="Conta aberta">
        {!contaId ? (
          <p className={styles.escolha}>
            <Icon name="contas" size="xl" />
            Escolha uma conta para ver os detalhes.
          </p>
        ) : conta.data ? (
          <ContaDetalhe conta={conta.data} voltar={voltar} />
        ) : naoAchou ? (
          // RN06: the same answer for a bill that does not exist and one you cannot see.
          <div className={styles.escolha} role="alert">
            <Icon name="alerta" size="xl" />
            <b>Conta não encontrada</b>
            <Link href={voltar}>Voltar para Contas</Link>
          </div>
        ) : (
          <p className={styles.escolha} role={conta.error ? "alert" : "status"}>
            {conta.error?.message ?? "Carregando conta…"}
          </p>
        )}
      </aside>

      {lista.data && temFiltros(lista.data) && (
        <Folha open={filtros} onClose={() => setFiltros(false)} title="Filtros" actions={<Button label="Ver contas" onClick={() => setFiltros(false)} />}>
          <FiltroChips titulo="Casa" valor={casa} opcoes={lista.data.opcoes.casas.map((c) => [c.id, c.nome])} todos="Todas" onEscolher={(v) => ir({ casa: v })} />
          <FiltroChips titulo="Quem paga" valor={pagador} opcoes={opcoesPagador(lista.data)} todos="Todos" onEscolher={(v) => ir({ pagador: v })} />
        </Folha>
      )}
    </div>
  );
}

// Filter options come from the API and only list what you see (RN06): no option of a hidden bill.
const temFiltros = (l: Lista) => !!(l.opcoes.casas.length || l.opcoes.pagadores.length || l.opcoes.sem_pagador);

function opcoesPagador(l: Lista): [string, string][] {
  return [
    ...l.opcoes.pagadores.map((p): [string, string] => [p.id, p.sou_eu ? "Você" : p.nome]),
    ...(l.opcoes.sem_pagador ? [["nenhum", "Sem pagador"] as [string, string]] : []),
  ];
}

type FiltroProps = { titulo: string; valor?: string; opcoes: [string, string][]; todos: string; onEscolher: (v?: string) => void };

/** Mobile: the chips inside the "Filtros" sheet (Q14). */
function FiltroChips({ titulo, valor, opcoes, todos, onEscolher }: FiltroProps) {
  return (
    <div role="group" aria-label={titulo}>
      <span className={styles.lb}>{titulo}</span>
      <div className={styles.chipsWrap}>
        <Chip label={todos} state={!valor ? "on" : "off"} onClick={() => onEscolher(undefined)} />
        {opcoes.map(([id, nome]) => (
          <Chip key={id} label={nome} state={valor === id ? "on" : "off"} onClick={() => onEscolher(id)} />
        ))}
      </div>
    </div>
  );
}

/** Desktop: "Casa todas" chip with a small menu (Q14, D03). Menu has no frame (guide "Telas sem frame"). */
function ChipMenu({ titulo, valor, opcoes, todos, onEscolher }: FiltroProps) {
  const [aberto, setAberto] = useState(false);
  const raiz = useRef<HTMLSpanElement>(null);
  const id = useId();
  useEffect(() => {
    if (!aberto) return;
    const fora = (e: PointerEvent) => !raiz.current?.contains(e.target as Node) && setAberto(false);
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setAberto(false);
    document.addEventListener("pointerdown", fora);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("pointerdown", fora);
      document.removeEventListener("keydown", esc);
    };
  }, [aberto]);
  const escolher = (v?: string) => {
    setAberto(false);
    onEscolher(v);
  };
  const atual = opcoes.find(([o]) => o === valor)?.[1];
  return (
    <span className={styles.chipMenu} ref={raiz}>
      <Chip label={titulo} count={atual ?? todos} state={valor ? "on" : "off"} onClick={() => setAberto(!aberto)} />
      {aberto && (
        <span id={id} className={styles.menu} role="group" aria-label={titulo}>
          <button type="button" aria-current={!valor || undefined} onClick={() => escolher(undefined)}>
            {todos[0].toUpperCase() + todos.slice(1)}
          </button>
          {opcoes.map(([o, nome]) => (
            <button key={o} type="button" aria-current={o === valor || undefined} onClick={() => escolher(o)}>
              {nome}
            </button>
          ))}
        </span>
      )}
    </span>
  );
}
