// Doop: k0kB5dc-Vo / 10 · Grupo + D04, 05 + M01; CU09, Q08-8.
"use client";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useSessao } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Field } from "@/components/ui/field";
import { Folha } from "@/components/ui/folha";
import { RadioCard } from "@/components/ui/radio-card";
import type { CriarRecorrencia, EditarRecorrencia, Recorrencia } from "@/lib/contas/client";
import { lerValor, reais, valorEditavel } from "@/lib/contas/formato";
import { useAcoesRecorrencia, useRecorrencia, useRecorrencias } from "@/lib/contas/hooks";
import { useGrupo } from "@/lib/grupos/hooks";
import { RecurringRow } from "./recurring-row";
import styles from "./recorrencias.module.css";

type Props = { open: boolean; espacoId: string; pessoal: boolean; inicial?: string; onClose: () => void };
export function RecorrenciasFolha({ open, espacoId, pessoal, inicial, onClose }: Props) {
  const { user } = useSessao();
  const lista = useRecorrencias(open ? espacoId : undefined);
  const grupo = useGrupo(espacoId, open && !pessoal);
  const [selecionado, setSelecionado] = useState<string | "nova" | null>(inicial ?? null);
  const detalhe = useRecorrencia(open && selecionado && selecionado !== "nova" ? selecionado : undefined);
  const acoes = useAcoesRecorrencia();
  const [descricao, setDescricao] = useState("");
  const [dia, setDia] = useState("1");
  const [tipo, setTipo] = useState<"fixo" | "variavel">("fixo");
  const [valor, setValor] = useState("");
  const [casa, setCasa] = useState<string | null>(null);
  const [pagador, setPagador] = useState<string | null>(pessoal ? null : user.id);
  const [visibilidade, setVisibilidade] = useState<"grupo" | "restrita">("grupo");
  const [acesso, setAcesso] = useState<string[]>([]);
  const [erro, setErro] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const trava = useRef(false);
  const geracao = useRef(0);
  const tentativa = useRef<{ assinatura: string; chave: string } | null>(null);
  const carregado = useRef<string | null>(null);
  const base = useRef<Recorrencia | null>(null);
  useEffect(() => () => { geracao.current++; }, []);
  useEffect(() => {
    const r = detalhe.data;
    if (!r || carregado.current === r.id) return;
    let ativo = true;
    queueMicrotask(() => { if (!ativo) return; carregado.current = r.id; base.current = { ...r, acesso: [...r.acesso] }; setDescricao(r.descricao); setDia(String(r.dia_vencimento)); setTipo(r.valor_tipo); setValor(r.valor_centavos == null ? "" : valorEditavel(r.valor_centavos)); setCasa(r.subgrupo); setPagador(r.pagador); setVisibilidade(r.visibilidade); setAcesso([...r.acesso]); });
    return () => { ativo = false; };
  }, [detalhe.data]);
  const item = selecionado && selecionado !== "nova" ? detalhe.data : undefined;
  function voltar() { if (trava.current) return; geracao.current++; setSelecionado(null); carregado.current = null; base.current = null; tentativa.current = null; setErro(""); }
  function fechar() { if (trava.current) return; geracao.current++; onClose(); }
  function nova() { if (trava.current) return; carregado.current = null; base.current = null; tentativa.current = null; setDescricao(""); setDia("1"); setTipo("fixo"); setValor(""); setCasa(null); setPagador(pessoal ? null : user.id); setVisibilidade("grupo"); setAcesso([]); setErro(""); setSelecionado("nova"); }
  async function executar(fn: () => Promise<unknown>, depois: () => void) {
    if (trava.current) return;
    trava.current = true; setOcupado(true); setErro(""); const versao = ++geracao.current;
    try { await fn(); if (versao === geracao.current) { trava.current = false; setOcupado(false); depois(); } }
    catch (e) { if (versao === geracao.current) setErro(e instanceof Error ? e.message : "Não foi possível concluir."); }
    finally { if (versao === geracao.current) { trava.current = false; setOcupado(false); } }
  }
  function salvar(e: FormEvent) {
    e.preventDefault();
    const n = Number(dia); const cents = tipo === "fixo" ? lerValor(valor) : null;
    if (!descricao.trim() || !Number.isInteger(n) || n < 1 || n > 31 || (tipo === "fixo" && cents === null)) { setErro("Informe descrição, dia de 1 a 31 e valor fixo maior que zero."); return; }
    const campos = { descricao: descricao.trim(), dia_vencimento: n, valor_tipo: tipo, valor_centavos: cents, subgrupo: casa, pagador, visibilidade, acesso: visibilidade === "restrita" ? acesso : [] };
    if (selecionado === "nova") {
      const assinatura = JSON.stringify([espacoId, campos]);
      if (tentativa.current?.assinatura !== assinatura) tentativa.current = { assinatura, chave: crypto.randomUUID() };
      const body: CriarRecorrencia = { ...campos, chave_idempotencia: tentativa.current.chave };
      void executar(() => acoes.criar.mutateAsync({ espaco: espacoId, body }), () => { setSelecionado(null); tentativa.current = null; });
    } else if (item?.pode_editar && base.current?.id === item.id) {
      const original = base.current;
      const body: EditarRecorrencia = {};
      if (campos.descricao !== original.descricao) body.descricao = campos.descricao;
      if (campos.dia_vencimento !== original.dia_vencimento) body.dia_vencimento = campos.dia_vencimento;
      if (campos.valor_tipo !== original.valor_tipo) body.valor_tipo = campos.valor_tipo;
      if (campos.valor_centavos !== original.valor_centavos) body.valor_centavos = campos.valor_centavos;
      if (campos.subgrupo !== original.subgrupo) body.subgrupo = campos.subgrupo;
      if (campos.pagador !== original.pagador) body.pagador = campos.pagador;
      if (campos.visibilidade !== original.visibilidade) body.visibilidade = campos.visibilidade;
      const acessoBase = original.visibilidade === "restrita" ? original.acesso : [];
      if (JSON.stringify(campos.acesso.slice().sort()) !== JSON.stringify(acessoBase.slice().sort())) body.acesso = campos.acesso;
      void executar(() => acoes.editar.mutateAsync({ id: item.id, body }), voltar);
    }
  }
  const membros = grupo.data?.membros ?? [];
  const podeCriar = pessoal || grupo.data?.meu_papel === "admin" || grupo.data?.meu_papel === "membro";
  const editavel = selecionado === "nova" || !!item?.pode_editar;
  return <Folha open={open} onClose={fechar} busy={ocupado} title={selecionado === "nova" ? "Nova recorrência" : selecionado ? "Conta que se repete" : "Recorrências"}>
    {!selecionado ? <>
      {podeCriar && <Button label="Nova recorrência" icon="mais" onClick={nova} />}
      {lista.isPending ? <p role="status">Carregando recorrências…</p> : lista.error ? <p role="alert">{lista.error.message}</p> : lista.data?.length ? <div className={styles.lista}>{lista.data.map((r) => <RecurringRow key={r.id} text={r.descricao} caption={`Dia ${r.dia_vencimento} · ${r.valor_tipo === "fixo" ? "valor fixo" : "valor muda"} · ${r.estado}`} vl={r.valor_centavos == null ? "Valor a definir" : reais(r.valor_centavos)} onClick={() => { setErro(""); setSelecionado(r.id); }} />)}</div> : <p>Nenhuma conta que se repete neste espaço.</p>}
    </> : selecionado !== "nova" && !item ? <p role={detalhe.error ? "alert" : "status"}>{detalhe.error?.message ?? "Carregando recorrência…"}</p> : <>
      {item && <p className={styles.nota}>Estado: {item.estado}{item.motivo_pausa ? ` · ${item.motivo_pausa}` : ""}. Pausar ou encerrar mantém as contas já criadas.</p>}
      <form className={styles.form} onSubmit={salvar}>
        <fieldset className={styles.form} disabled={ocupado || !editavel}>
          <Field label="Descrição" value={descricao} onChange={(e) => setDescricao(e.target.value)} maxLength={150} required />
          <Field label="Dia do vencimento" type="number" min={1} max={31} value={dia} onChange={(e) => setDia(e.target.value)} required hint="Em meses mais curtos, vence no último dia." />
          <fieldset className={styles.opcoes}><legend>Valor</legend><RadioCard name="valor-recorrencia" title="Valor fixo" text="Mesmo valor a cada mês." state={tipo === "fixo" ? "on" : "off"} onChange={() => setTipo("fixo")} /><RadioCard name="valor-recorrencia" title="Valor muda" text="Cada conta começa com valor a definir." state={tipo === "variavel" ? "on" : "off"} onChange={() => setTipo("variavel")} /></fieldset>
          {tipo === "fixo" && <Field label="Valor fixo" inputMode="decimal" value={valor} onChange={(e) => setValor(e.target.value)} required />}
          {!pessoal && grupo.data && <>
            <div role="group" aria-label="Casa"><b>Casa</b><div className={styles.chips}><Chip label="Sem casa" state={casa === null ? "on" : "off"} onClick={() => setCasa(null)} />{grupo.data.casas.filter((c) => !c.arquivado).map((c) => <Chip key={c.id} label={c.nome} wrap state={casa === c.id ? "on" : "off"} onClick={() => setCasa(c.id)} />)}</div></div>
            <div role="group" aria-label="Quem paga"><b>Quem paga</b><div className={styles.chips}><Chip label="Ninguém" state={pagador === null ? "on" : "off"} onClick={() => setPagador(null)} />{membros.filter((m) => m.papel !== "observador").map((m) => <Chip key={m.id} label={m.sou_eu ? "Eu" : m.nome || m.email || ""} state={pagador === m.usuario ? "on" : "off"} onClick={() => setPagador(m.usuario)} />)}</div></div>
            <div role="group" aria-label="Quem vê"><b>Quem vê</b><div className={styles.chips}><Chip label="Todo o grupo" state={visibilidade === "grupo" ? "on" : "off"} onClick={() => setVisibilidade("grupo")} /><Chip label="Só algumas pessoas" state={visibilidade === "restrita" ? "on" : "off"} onClick={() => setVisibilidade("restrita")} /></div></div>
            {visibilidade === "restrita" && <div role="group" aria-label="Quem mais vê"><b>Quem mais vê</b><div className={styles.chips}>{membros.filter((m) => m.papel !== "pagador" && !m.sou_eu).map((m) => <Chip key={m.id} label={m.nome || m.email || ""} state={acesso.includes(m.usuario) ? "on" : "off"} onClick={() => setAcesso(acesso.includes(m.usuario) ? acesso.filter((id) => id !== m.usuario) : [...acesso, m.usuario])} />)}</div></div>}
          </>}
          {selecionado === "nova" && <p className={styles.nota}>A conta deste mês será criada agora. Nenhum código ou PDF será copiado para os próximos meses.</p>}
          {editavel && <Button type="submit" label={ocupado ? "Salvando…" : selecionado === "nova" ? "Criar recorrência" : "Salvar"} />}
        </fieldset>
      </form>
      {item && <div className={styles.acoes}>{([ ["pausar", item.pode_pausar, "Pausar"], ["retomar", item.pode_retomar, "Retomar"], ["encerrar", item.pode_encerrar, "Encerrar"] ] as const).map(([acao, permitido, label]) => permitido && <Button key={acao} tone="secondary" label={label} disabled={ocupado} onClick={() => { if (acao === "encerrar" && !window.confirm("Encerrar esta recorrência? As contas já criadas serão mantidas.")) return; void executar(() => acoes.acao.mutateAsync({ id: item.id, acao }), voltar); }} />)}</div>}
      <Button tone="ghost" label="Voltar à lista" disabled={ocupado} onClick={voltar} />
    </>}
    {erro && <p role="alert" className={styles.erro}>{erro}</p>}
  </Folha>;
}
