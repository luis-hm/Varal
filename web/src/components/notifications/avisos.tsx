// Doop: k0kB5dc-Vo / 04 · Avisos (fcR9RDu79a) + D06 · Avisos (aYT5zpG8_w); RF20, CU12, Q09-9.
"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Inicio } from "@/components/bills/inicio";
import { useSessao } from "@/components/layout/app-shell";
import { TopBar } from "@/components/layout/top-bar";
import { Icon } from "@/components/ui/icon";
import type { Notificacao } from "@/lib/notificacoes/client";
import { useAvisos, usePreferencias, usePushConfig } from "@/lib/notificacoes/hooks";
import { ativarPush, desativarPush, estadoPush, pendenciaPush, suportePush } from "@/lib/notificacoes/push";
import { AvisoLinha, useAbrirAviso } from "./aviso-acoes";
import styles from "./avisos.module.css";

function dataGrupo(data: string) {
  const formato = new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Fortaleza", day: "2-digit", month: "2-digit", year: "numeric" });
  const dia = formato.format(new Date(data));
  const agora = Date.now();
  if (dia === formato.format(new Date(agora))) return "Hoje";
  if (dia === formato.format(new Date(agora - 86400000))) return "Ontem";
  return dia;
}
export function Preferencias({ user }: { user: string }) {
  const { query, salvar } = usePreferencias(user);
  const config = usePushConfig(user);
  const [ativo, setAtivo] = useState(false);
  const [pendencia, setPendencia] = useState<ReturnType<typeof pendenciaPush>>(null);
  const [supported, setSupported] = useState(false);
  const [busy, setBusy] = useState(false);
  const [erro, setErro] = useState("");
  const latch = useRef(false);
  useEffect(() => { const timer = window.setTimeout(() => { setSupported(suportePush()); setAtivo(estadoPush(user)); setPendencia(pendenciaPush(user)); }, 0); return () => window.clearTimeout(timer); }, [user]);
  async function dispositivo() {
    if (latch.current) return;
    latch.current = true; setBusy(true); setErro("");
    try { if (ativo || pendencia === "propria") await desativarPush(user); else if (config.data) await ativarPush(user, config.data); }
    catch (error) { setErro(error instanceof Error ? error.message : "Não foi possível atualizar este dispositivo."); }
    finally { setAtivo(estadoPush(user)); setPendencia(pendenciaPush(user)); setBusy(false); latch.current = false; }
  }
  return <details className={styles.preferences}>
    <summary>Preferências de notificações</summary>
    {query.isLoading ? <p role="status">Carregando preferências…</p> : query.isError ? <p role="alert">Não foi possível carregar as preferências. <button type="button" onClick={() => query.refetch()}>Tentar novamente</button></p> : query.data && <>
      <label><input type="checkbox" checked={query.data.email ?? true} disabled={salvar.isPending} onChange={(e) => salvar.mutate({ email: e.target.checked })} /> E-mail</label>
      <label><input type="checkbox" checked={query.data.push ?? true} disabled={salvar.isPending} onChange={(e) => salvar.mutate({ push: e.target.checked })} /> Push</label>
      {salvar.isError && <p role="alert">Não foi possível salvar as preferências.</p>}
    </>}
    <p>{ativo ? "Inscrição registrada neste dispositivo." : "Notificações não ativadas neste dispositivo."}</p>
    {pendencia === "outra" && <p>Para ativar notificações aqui, entre na conta anterior e conclua a desativação pendente.</p>}
    {pendencia === "propria" && <p>Há uma desativação pendente neste dispositivo.</p>}
    {supported && Notification.permission === "denied" && <p>A permissão para notificações está bloqueada nas configurações do navegador.</p>}
    {!supported ? <p>Este navegador não permite ativar notificações neste dispositivo.</p> : config.isLoading ? <p role="status">Verificando disponibilidade…</p> : !config.data?.habilitado && !ativo && !pendencia ? <p>Notificações indisponíveis no momento.</p> : <button className={styles.action} type="button" onClick={dispositivo} disabled={busy || pendencia === "outra"}>{busy ? "Aguarde…" : pendencia === "propria" ? "Concluir desativação" : ativo ? "Desativar notificações neste dispositivo" : "Ativar notificações neste dispositivo"}</button>}
    {erro && <p role="alert">{erro}</p>}
  </details>;
}
function Conteudo({ onClose, onNavigate }: { onClose?: () => void; onNavigate?: () => void }) {
  const { user } = useSessao();
  const lista = useAvisos(user.id);
  const { abrir, erro, leitura } = useAbrirAviso(user.id, onNavigate ?? onClose);
  const todosLatch = useRef(false);
  async function marcarTodos() {
    if (todosLatch.current) return;
    todosLatch.current = true;
    try { await leitura.todos.mutateAsync(); } catch { /* displayed below */ } finally { todosLatch.current = false; }
  }
  const avisos = lista.data?.pages.flatMap((p) => p.resultados) ?? [];
  const grupos = avisos.reduce<{ dia: string; itens: Notificacao[] }[]>((all, aviso) => {
    const dia = dataGrupo(aviso.criado_em);
    const ultimo = all[all.length - 1];
    if (ultimo?.dia === dia) ultimo.itens.push(aviso); else all.push({ dia, itens: [aviso] });
    return all;
  }, []);
  return <>
    <div className={styles.mobileTop}><TopBar title="Avisos" backHref="/" action={<button className={styles.iconButton} type="button" onClick={marcarTodos} disabled={leitura.todos.isPending} aria-label="Marcar todos como lidos"><Icon name="pago" size="md" /></button>} /></div>
    <header className={styles.desktopTop}><h1 id="avisos-titulo">Avisos</h1><button className={styles.action} type="button" onClick={marcarTodos} disabled={leitura.todos.isPending}>Marcar todos como lidos</button>{onClose ? <button type="button" aria-label="Fechar" className={styles.iconButton} onClick={onClose}><Icon name="fechar" size="md" /></button> : <Link href="/" aria-label="Fechar" className={styles.iconButton}><Icon name="fechar" size="md" /></Link>}</header>
    <div className={styles.content}>
      {leitura.todos.isError && <p role="alert">Não foi possível marcar todos como lidos.</p>}
      {erro && <p role="alert">{erro}</p>}
      {lista.isLoading && <p role="status">Carregando avisos…</p>}
      {lista.isError && <p role="alert">Não foi possível carregar os avisos. <button type="button" onClick={() => lista.refetch()}>Tentar novamente</button></p>}
      {lista.isSuccess && !avisos.length && <p>Você ainda não tem avisos.</p>}
      {grupos.map(({ dia, itens }) => <section key={dia}><h2 className={styles.date}>{dia}</h2><ul className={styles.list}>{itens.map((aviso) => <li key={aviso.id}><AvisoLinha aviso={aviso} onClick={() => abrir(aviso)} disabled={leitura.um.isPending} /></li>)}</ul></section>)}
      {lista.hasNextPage && <button type="button" className={styles.action} disabled={lista.isFetchingNextPage} onClick={() => lista.fetchNextPage()}>{lista.isFetchingNextPage ? "Carregando…" : "Carregar mais"}</button>}
      <Preferencias user={user.id} />
    </div>
  </>;
}
export function AvisosGaveta({ onClose, onNavigate, returnFocusTo }: { onClose: () => void; onNavigate?: () => void; returnFocusTo?: HTMLElement | null }) {
  const ref = useRef<HTMLDialogElement>(null);
  const opener = useRef<HTMLElement | null>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    opener.current = returnFocusTo ?? (document.activeElement instanceof HTMLElement ? document.activeElement : null);
    dialog.showModal();
    return () => { if (dialog.open) dialog.close(); opener.current?.focus(); };
  }, [returnFocusTo]);
  return <dialog ref={ref} className={styles.drawer} aria-labelledby="avisos-titulo" onCancel={(event) => { event.preventDefault(); onClose(); }} onClick={(event) => { if (event.target === event.currentTarget) onClose(); }}><Conteudo onClose={onClose} onNavigate={onNavigate} /></dialog>;
}
export function AvisosPagina() {
  const router = useRouter();
  const [desktop, setDesktop] = useState(false);
  useEffect(() => {
    const media = window.matchMedia("(min-width: 1024px)");
    const change = () => setDesktop(media.matches);
    change(); media.addEventListener("change", change);
    return () => media.removeEventListener("change", change);
  }, []);
  return <><div className={styles.under}><Inicio /></div>{desktop ? <AvisosGaveta onClose={() => router.push("/")} onNavigate={() => {}} /> : <div className={styles.mobile}><Conteudo /></div>}</>;
}
