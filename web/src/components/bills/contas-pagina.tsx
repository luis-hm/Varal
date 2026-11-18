// Doop: k0kB5dc-Vo / 03 · Contas (bdiED7Q0I-) + D03 · Contas + Detalhe (cWdVUX2y8H), 07 · Detalhe (efJzW9e5vx);
// CU06, CU07; RF13, RN12, D2, Q9, Q13 (no search), Q14 (Categoria / Quem paga), CA15, CA30.
// COR-02/03/05/07/11: personal by default (?espaco= picks a group), every period unless ?mes=, filters that never
// hide while active, and a fixed mode for "Grupos → grupo → categoria → contas" (same list, other context).
// One route per size pair: < 1024px [id] is the 07 alone; from 1024px the list stays and the panel slides in.
"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";
import { useSessao } from "@/components/layout/app-shell";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Folha } from "@/components/ui/folha";
import { Icon, type IconName } from "@/components/ui/icon";
import { RecorrenciasFolha } from "@/components/recurrences/recorrencias-folha";
import { ApiError } from "@/lib/grupos/client";
import type { Conta, FiltroStatus, Lista } from "@/lib/contas/client";
import { mesAno, mesAtual, nomeMes, plural, somarMes, totalConhecido } from "@/lib/contas/formato";
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

/** Fixed context of a category screen (COR-11): the list is locked to one group and one category. */
export type ContextoFixo = {
  espacoId: string;
  /** Category id or "nenhum" (bills without category). */
  categoria: string;
  /** Path of this screen; bills open under `${base}/${id}`. */
  base: string;
  voltar: string;
  titulo: string;
  subtitulo: string;
  icone: IconName;
};

export function ContasPagina({ contaId, fixo }: { contaId?: string; fixo?: ContextoFixo }) {
  const router = useRouter();
  const params = useSearchParams();
  const { user } = useSessao();
  const conta = useConta(contaId);
  const mes = params.get("mes") || undefined;
  const status = (params.get("status") as FiltroStatus | null) || "todas";
  const casa = fixo ? fixo.categoria : params.get("casa") || undefined;
  const pagador = params.get("pagador") || undefined;
  // COR-05: the main list is personal unless ?espaco= names a group you can browse (never the payer's).
  const contextos = [
    { id: user.espaco_pessoal.id, nome: "Pessoal" },
    ...user.grupos.filter((g) => g.papel !== "pagador").map((g) => ({ id: g.id, nome: g.nome })),
  ];
  const escolhido = contextos.find((c) => c.id === params.get("espaco")) ?? contextos[0];
  // Decision 2: an open bill shows the list of its own space.
  const espacoId = fixo ? fixo.espacoId : contaId ? (conta.data?.espaco.id ?? (conta.isError ? escolhido.id : undefined)) : escolhido.id;
  const espacoNome = fixo ? fixo.subtitulo : contaId && conta.data ? conta.data.espaco.nome : escolhido.nome;
  const pessoal = espacoId === user.espaco_pessoal.id;
  const lista = useContas(espacoId, { mes, status, subgrupo: casa, pagador });
  const [filtros, setFiltros] = useState(false);
  const [recorrencias, setRecorrencias] = useState(false);
  const base = fixo?.base ?? "/contas";

  const query = (mudar: Record<string, string | undefined>) => {
    const q = new URLSearchParams(params);
    for (const [k, v] of Object.entries(mudar)) {
      if (v && !(k === "status" && v === "todas") && !(k === "espaco" && v === user.espaco_pessoal.id)) q.set(k, v);
      else q.delete(k);
    }
    return q.size ? `?${q}` : "";
  };
  // CA15: filters live in the URL, so Back restores them.
  const ir = (mudar: Record<string, string | undefined>) => router.push(`${contaId ? `${base}/${contaId}` : base}${query(mudar)}`, { scroll: false });
  const limpar = () => ir({ casa: undefined, pagador: undefined, status: undefined, mes: undefined });
  const origemSimples = params.get("origem") === "simples";
  const grupoSimples = conta.data?.espaco.tipo === "grupo" && user.grupos.find((grupo) => grupo.id === conta.data?.espaco.id && grupo.papel === "pagador");
  const voltar = origemSimples ? (grupoSimples ? `/grupos/${encodeURIComponent(grupoSimples.id)}/simples${params.get("pagas") === "1" ? "?pagas=1" : ""}` : "/grupos") : `${base}${query({})}`;
  const naoAchou = conta.error instanceof ApiError && conta.error.status === 404;

  const opcoesCasa = lista.data ? opcoesCategoria(lista.data, casa) : [];
  const opcoesQuem = lista.data ? opcoesPagador(lista.data, pagador) : [];
  // COR-07: active filters stay visible and removable even when the answer is empty.
  const ativos = [
    ...(!fixo && casa ? [{ chave: "casa", rotulo: `Categoria: ${opcoesCasa.find(([id]) => id === casa)?.[1] ?? "indisponível"}` }] : []),
    ...(pagador ? [{ chave: "pagador", rotulo: `Quem paga: ${opcoesQuem.find(([id]) => id === pagador)?.[1] ?? "indisponível"}` }] : []),
  ];
  const podeFiltrar = !pessoal && (opcoesCasa.length > 0 || opcoesQuem.length > 0);
  const algumFiltro = ativos.length > 0 || status !== "todas" || !!mes;
  const totalRotulo = (d: Lista) => `${d.valores_indefinidos_qtd ? "Total conhecido" : "Total"} ${d.mes ? `de ${nomeMes(d.mes)}` : "de todos os meses"}: ${totalConhecido(d.total_centavos, d.valores_indefinidos_qtd)}`;

  return (
    <div className={styles.split} data-aberta={contaId ? "" : undefined}>
      <section className={styles.lista} aria-labelledby="contas-t">
        <header className={styles.cab}>
          {fixo && (
            <Link className={styles.redondo} href={fixo.voltar} aria-label="Voltar ao grupo">
              <Icon name="voltar" size="md" />
            </Link>
          )}
          <div className={styles.titulo1}>
            {fixo && <span className={styles.selo}><Icon name={fixo.icone} size="md" /></span>}
            <span>
              <h1 id="contas-t">{fixo ? fixo.titulo : "Contas"}</h1>
              {fixo && <small>{fixo.subtitulo}</small>}
            </span>
          </div>
          <div className={styles.acoes}>
            <button type="button" className={styles.redondo} aria-label="Recorrências" aria-haspopup="dialog" onClick={() => setRecorrencias(true)}>
              <Icon name="repetir" size="md" />
            </button>
            {(podeFiltrar || ativos.length > 0) && (
              <button type="button" className={`${styles.redondo} ${styles.mobOnly}`} aria-label="Filtros" aria-haspopup="dialog" data-ativo={ativos.length || undefined} onClick={() => setFiltros(true)}>
                <Icon name="filtro" size="md" />
              </button>
            )}
          </div>
        </header>

        <div className={styles.contexto}>
          {!fixo && contextos.length > 1 && (
            <ChipMenu titulo="Ver" valor={escolhido.id} opcoes={contextos.map((c) => [c.id, c.nome])} onEscolher={(v) => ir({ espaco: v, casa: undefined, pagador: undefined })} />
          )}
          <nav className={styles.periodo} aria-label="Período">
            {mes ? (
              <>
                <Link className={styles.seta} href={`${base}${query({ mes: somarMes(mes, -1) })}`} aria-label="Mês anterior" scroll={false}>
                  <Icon name="chevron" size="sm" className={styles.esq} />
                </Link>
                <b className={styles.mesNome}>{mesAno(mes)}</b>
                <Link className={styles.seta} href={`${base}${query({ mes: somarMes(mes, 1) })}`} aria-label="Próximo mês" scroll={false}>
                  <Icon name="chevron" size="sm" />
                </Link>
                <Link className={styles.limparMes} href={`${base}${query({ mes: undefined })}`} scroll={false}>Todos os meses</Link>
              </>
            ) : (
              <>
                <b className={styles.mesNome}>Todos os meses</b>
                <Link className={styles.limparMes} href={`${base}${query({ mes: mesAtual() })}`} scroll={false}>
                  <Icon name="calendario" size="sm" /> Escolher mês
                </Link>
              </>
            )}
          </nav>
        </div>

        {lista.data && (
          <p className={styles.resumoLista}>
            {totalRotulo(lista.data)} · {plural(lista.data.contagens.todas, "conta", "contas")}
            {!fixo && <> · {espacoNome}</>}
          </p>
        )}

        {lista.data && (
          <div className={styles.chips} role="group" aria-label="Filtrar por status">
            {chips.map(([valor, rotulo]) => (
              <Chip key={valor} label={rotulo} count={lista.data.contagens[valor]} state={status === valor ? "on" : "off"} onClick={() => ir({ status: valor })} />
            ))}
            {podeFiltrar && (
              <span className={styles.deskOnly}>
                {!fixo && opcoesCasa.length > 0 && <ChipMenu titulo="Categoria" valor={casa} opcoes={opcoesCasa} todos="todas" onEscolher={(v) => ir({ casa: v })} />}
                {opcoesQuem.length > 0 && <ChipMenu titulo="Quem paga" valor={pagador} opcoes={opcoesQuem} todos="todos" onEscolher={(v) => ir({ pagador: v })} />}
              </span>
            )}
          </div>
        )}

        {ativos.length > 0 && (
          <div className={styles.ativos} role="group" aria-label="Filtros ativos">
            {ativos.map((a) => (
              <button key={a.chave} type="button" className={styles.tag} onClick={() => ir({ [a.chave]: undefined })} aria-label={`Remover filtro ${a.rotulo}`}>
                {a.rotulo} <Icon name="fechar" size="sm" />
              </button>
            ))}
          </div>
        )}

        {lista.error ? (
          <div className={styles.vazio} role="alert">
            <p>{lista.error.message}</p>
            <Button tone="secondary" label="Tentar de novo" onClick={() => void lista.refetch()} />
          </div>
        ) : !lista.data ? (
          <p className={styles.vazio} role="status">Carregando contas…</p>
        ) : !lista.data.itens.length ? (
          <div className={styles.vazio}>
            <p>{algumFiltro ? "Nenhuma conta com esses filtros." : mes ? `Nenhuma conta em ${nomeMes(mes)}.` : "Nenhuma conta por aqui ainda."}</p>
            {algumFiltro && <Button tone="secondary" label="Limpar filtros" onClick={limpar} />}
          </div>
        ) : (
          agrupar(lista.data.itens).map(([nome, contas], g) => (
            <section key={nome} aria-label={nome}>
              <p className={`${styles.grupo} ${styles.in}`} style={{ animationDelay: `${g * 0.12}s` }}>
                <span>{nome}</span>
                <span>{contas.some((c) => c.valor_centavos === null) ? "Total conhecido: " : ""}{totalConhecido(contas.reduce((s, c) => s + (c.valor_centavos ?? 0), 0), contas.filter((c) => c.valor_centavos === null).length)}</span>
              </p>
              <ul className={styles.cards}>
                {contas.map((c, i) => (
                  <li key={c.id} className={styles.in} style={{ animationDelay: `${g * 0.12 + (i + 1) * 0.06}s` }}>
                    <ContaCard conta={c} href={`${base}/${c.id}${query({})}`} selected={c.id === contaId} />
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
          <ContaDetalhe conta={conta.data} voltar={voltar} retornoPagamento={origemSimples ? voltar : undefined} />
        ) : (
          <>
            {/* Ajuste 28: no TabBar on the stacked 07, so loading and errors keep the way back too. */}
            <div className={styles.mobTop}>
              <TopBar title="Conta" backHref={voltar} />
            </div>
            {naoAchou ? (
              // RN06: the same answer for a bill that does not exist and one you cannot see.
              <div className={styles.escolha} role="alert">
                <Icon name="alerta" size="xl" />
                <b>Conta não encontrada</b>
                <Link href={voltar}>Voltar para a lista</Link>
              </div>
            ) : (
              <p className={styles.escolha} role={conta.error ? "alert" : "status"}>
                {conta.error?.message ?? "Carregando conta…"}
              </p>
            )}
          </>
        )}
      </aside>

      <Folha open={filtros} onClose={() => setFiltros(false)} title="Filtros" actions={<Button label="Ver contas" onClick={() => setFiltros(false)} />}>
        <div className={styles.folhaFiltros}>
          {!fixo && opcoesCasa.length > 0 && <FiltroChips titulo="Categoria" valor={casa} opcoes={opcoesCasa} todos="Todas" onEscolher={(v) => ir({ casa: v })} />}
          {opcoesQuem.length > 0 && <FiltroChips titulo="Quem paga" valor={pagador} opcoes={opcoesQuem} todos="Todos" onEscolher={(v) => ir({ pagador: v })} />}
          {algumFiltro && <Button tone="ghost" label="Limpar filtros" onClick={limpar} />}
        </div>
      </Folha>
      {recorrencias && espacoId && <RecorrenciasFolha open espacoId={espacoId} pessoal={pessoal} onClose={() => setRecorrencias(false)} />}
    </div>
  );
}

// Filter options come from the API and only list what you see (RN06). An active value missing from the
// options (archived category, a payer who left) still shows, so it can be removed (COR-07).
function opcoesCategoria(l: Lista, ativo?: string): [string, string][] {
  const opcoes: [string, string][] = [
    ...l.opcoes.casas.map((c): [string, string] => [c.id, c.nome]),
    ...(l.opcoes.sem_categoria || ativo === "nenhum" ? [["nenhum", "Sem categoria"] as [string, string]] : []),
  ];
  return ativo && !opcoes.some(([id]) => id === ativo) ? [...opcoes, [ativo, "Indisponível"]] : opcoes;
}

function opcoesPagador(l: Lista, ativo?: string): [string, string][] {
  const opcoes: [string, string][] = [
    ...l.opcoes.pagadores.map((p): [string, string] => [p.id, p.sou_eu ? "Você" : p.nome]),
    ...(l.opcoes.ex_membro ? [["ex_membro", "Ex-membro"] as [string, string]] : []),
    ...(l.opcoes.sem_pagador ? [["nenhum", "Sem pagador"] as [string, string]] : []),
  ];
  return ativo && !opcoes.some(([id]) => id === ativo) ? [...opcoes, [ativo, "Indisponível"]] : opcoes;
}

type FiltroProps = { titulo: string; valor?: string; opcoes: [string, string][]; todos?: string; onEscolher: (v?: string) => void };

/** Mobile: the chips inside the "Filtros" sheet (Q14). */
function FiltroChips({ titulo, valor, opcoes, todos, onEscolher }: FiltroProps) {
  return (
    <div role="group" aria-label={titulo}>
      <span className={styles.lb}>{titulo}</span>
      <div className={styles.chipsWrap}>
        {todos && <Chip label={todos} state={!valor ? "on" : "off"} onClick={() => onEscolher(undefined)} />}
        {opcoes.map(([id, nome]) => (
          <Chip key={id} label={nome} wrap state={valor === id ? "on" : "off"} onClick={() => onEscolher(id)} />
        ))}
      </div>
    </div>
  );
}

/** A chip with a small menu (Q14, D03); also the context picker "Ver: Pessoal". */
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
      <Chip label={titulo} count={atual ?? todos} state={valor && todos ? "on" : "off"} onClick={() => setAberto(!aberto)} />
      {aberto && (
        <span id={id} className={styles.menu} role="group" aria-label={titulo}>
          {todos && (
            <button type="button" aria-current={!valor || undefined} onClick={() => escolher(undefined)}>
              {todos[0].toUpperCase() + todos.slice(1)}
            </button>
          )}
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
