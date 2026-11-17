// Doop: k0kB5dc-Vo / shell 02 · Início + D02 · Início; Field, Button; Q11-11 (no dedicated Perfil frame).
"use client";

import { useRef, useState, type FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { LogoutButton } from "@/components/auth/logout-button";
import { Preferencias } from "@/components/notifications/avisos";
import { useSessao } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { AuthError, confirmarCodigoReauth, emailsProprios, reautenticarSenha, sessaoAtual, solicitarCodigoReauth, solicitarVerificacaoEmail } from "@/lib/auth/client";
import { marcarSaidaLocal } from "@/lib/auth/isolamento";
import { ApiError } from "@/lib/grupos/client";
import { limparPushAposExclusao } from "@/lib/notificacoes/push";
import { baixarExportacao, consultarExportacao, criarIntencao, excluirConta, solicitarExportacao, type Exportacao } from "@/lib/perfil/client";
import type { components } from "@/types/api";
import styles from "./perfil.module.css";

type Acao = "exportar" | "baixar" | "excluir" | "confirmar";
type S = components["schemas"];
function precisaReauth(error: unknown) {
  if (!(error instanceof ApiError) || error.status !== 401 || !error.data || typeof error.data !== "object") return false;
  const data = error.data as Partial<S["ReauthResposta"]>;
  return data.code === "reauth_required" && data.meta?.is_authenticated === true;
}
function mensagem(error: unknown) {
  if (error instanceof ApiError || error instanceof AuthError) {
    if (error instanceof AuthError && error.status === 401 && error.autenticada === true) return "Não foi possível confirmar sua identidade. Confira os dados e tente novamente.";
    if (error.status === 401) return "Sua sessão expirou. Entre novamente para continuar.";
    if (error.status === 409) return "Não foi possível concluir agora. Verifique sua participação nos grupos e tente novamente.";
    if (error.status === 410) return "Esta solicitação expirou. Prepare uma nova.";
    if (error.status === 429) return "Muitas tentativas. Aguarde e tente novamente.";
    if (error.status === 403) return "Não foi possível autorizar esta ação. Atualize a página e tente novamente.";
  }
  return "Não foi possível concluir. Tente novamente.";
}

export function Perfil() {
  const { user } = useSessao();
  const cache = useQueryClient();
  const [job, setJob] = useState<Exportacao | null>(null);
  const [intencao, setIntencao] = useState<S["Intencao"] | null>(null);
  const [confirmado, setConfirmado] = useState(false);
  const [reauth, setReauth] = useState<Acao | null>(null);
  const [senha, setSenha] = useState("");
  const [codigo, setCodigo] = useState("");
  const [codigoEnviado, setCodigoEnviado] = useState(false);
  const [busy, setBusy] = useState(false);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const latch = useRef(false);
  const chave = useRef<string | null>(null);
  const auth = useQuery({ queryKey: ["perfil", user.id, "auth"], queryFn: sessaoAtual, enabled: !!reauth, retry: false });
  const emails = useQuery({ queryKey: ["perfil", user.id, "emails"], queryFn: emailsProprios, enabled: !!reauth && auth.data?.data.user.has_usable_password === false, retry: false });
  const principal = emails.data?.data.find((item) => item.primary && item.verified) ?? emails.data?.data.find((item) => item.verified) ?? emails.data?.data.find((item) => item.primary) ?? emails.data?.data[0];
  const estado = useQuery({ queryKey: ["perfil", user.id, "exportacao", job?.id], queryFn: () => consultarExportacao(job!.id), enabled: !!job && (job.estado === "pendente" || job.estado === "processando"), refetchInterval: (query) => { const atual = query.state.data ?? job; return query.state.status !== "error" && (atual?.estado === "pendente" || atual?.estado === "processando") ? 3000 : false; }, retry: false });
  const exportacao = estado.data ?? job;
  async function executar(acao: Acao) {
    if (acao === "exportar") {
      chave.current ??= crypto.randomUUID();
      const result = await solicitarExportacao({ chave: chave.current });
      setJob(result); chave.current = null;
    } else if (acao === "baixar" && exportacao) await baixarExportacao(exportacao.id);
    else if (acao === "excluir") {
      const result = await criarIntencao();
      setIntencao(result); setConfirmado(false);
    } else if (acao === "confirmar" && intencao && confirmado) {
      await excluirConta({ id: intencao.id, segredo: intencao.segredo, confirmar: true });
      marcarSaidaLocal();
      void cache.cancelQueries();
      cache.clear();
      void limparPushAposExclusao(user.id).catch(() => {});
      window.location.replace("/entrar");
    }
  }
  async function protegido(acao: Acao) {
    if (latch.current) return;
    latch.current = true; setBusy(true); setErro(""); setAviso("");
    try { await executar(acao); }
    catch (error) { if (precisaReauth(error)) { setReauth(acao); setCodigoEnviado(false); } else if (acao === "baixar" && error instanceof ApiError && error.status === 409) setErro("A exportação não está mais disponível. Prepare uma nova exportação."); else setErro(mensagem(error)); }
    finally { latch.current = false; setBusy(false); }
  }
  async function provar(event: FormEvent) {
    event.preventDefault();
    if (latch.current) return;
    latch.current = true; setBusy(true); setErro("");
    try {
      if (auth.data?.data.user.has_usable_password) await reautenticarSenha({ password: senha });
      else if (codigoEnviado) await confirmarCodigoReauth({ code: codigo });
      else if (principal?.verified) { await solicitarCodigoReauth({ email: principal.email }); setCodigoEnviado(true); setAviso("Código solicitado. Confira seu e-mail."); return; }
      else return;
      setSenha(""); setCodigo(""); setReauth(null);
      setAviso("Identidade confirmada. Continue a ação solicitada.");
    } catch (error) { setErro(mensagem(error)); }
    finally { latch.current = false; setBusy(false); }
  }
  async function verificarEmail() {
    if (!principal || latch.current) return;
    latch.current = true; setBusy(true); setErro("");
    try { await solicitarVerificacaoEmail(principal.email); setAviso("Solicitação enviada. Confirme o endereço pelo link e volte para continuar."); }
    catch (error) { setErro(mensagem(error)); }
    finally { latch.current = false; setBusy(false); }
  }
  return <div className={styles.page}>
    <h1>Perfil</h1>
    <section className={styles.section}><h2>Seus dados</h2><p>Nome</p><p className={styles.value} title={user.nome}>{user.nome}</p><p>E-mail</p><p className={styles.value} title={user.email}>{user.email}</p></section>
    <Preferencias user={user.id} />
    <section className={styles.section}><h2>Exportar meus dados</h2><p>Prepare um arquivo com seus dados pessoais e participações atuais. A exportação fica disponível por até 24 horas.</p>
      <div className={styles.actions}><Button label="Preparar exportação" onClick={() => protegido("exportar")} disabled={busy || !!reauth} />{exportacao?.estado === "pronto" && <Button label="Baixar exportação" tone="secondary" onClick={() => protegido("baixar")} disabled={busy || !!reauth} />}</div>
      {exportacao && <p role="status">{exportacao.estado === "pronto" ? "Exportação pronta" : exportacao.estado === "falhou" ? "Não foi possível preparar a exportação." : exportacao.estado === "expirado" ? "Exportação expirada." : "Preparando exportação…"} Disponível até {new Date(exportacao.expira_em).toLocaleString("pt-BR", { timeZone: "America/Fortaleza" })}.</p>}
      {estado.isError && <p role="alert">Não foi possível consultar a exportação. <button type="button" onClick={() => estado.refetch()}>Tentar novamente</button></p>}
    </section>
    <section className={styles.section}><h2>Excluir minha conta</h2><p>Seus dados pessoais e sua conta serão excluídos. Dados e comprovantes dos grupos podem ser preservados conforme as regras do grupo.</p><Button tone="danger" label="Preparar exclusão" disabled={busy || !!reauth} onClick={() => protegido("excluir")} />
      {intencao && <div><p>Confirme a exclusão até {new Date(intencao.expira_em).toLocaleString("pt-BR", { timeZone: "America/Fortaleza" })}.</p><label className={styles.checkbox}><input type="checkbox" checked={confirmado} onChange={(event) => setConfirmado(event.target.checked)} disabled={busy || !!reauth} /> Quero excluir minha conta</label><Button tone="danger" label="Confirmar exclusão" disabled={!confirmado || busy || !!reauth} onClick={() => protegido("confirmar")} /></div>}
    </section>
    {reauth && <section className={styles.section} aria-labelledby="confirmar-identidade"><h2 id="confirmar-identidade">Confirme sua identidade</h2>{auth.isLoading || emails.isLoading ? <p role="status">Carregando…</p> : auth.isError || emails.isError ? <p role="alert">Não foi possível carregar as opções de confirmação.</p> : <form className={styles.form} onSubmit={provar}>
      {auth.data?.data.user.has_usable_password ? <Field label="Senha" type="password" autoComplete="current-password" value={senha} onChange={(event) => setSenha(event.target.value)} required /> : principal?.verified ? codigoEnviado ? <Field label="Código de confirmação" value={codigo} onChange={(event) => setCodigo(event.target.value)} required /> : <p>Enviaremos um código para seu e-mail verificado.</p> : <><p>Confirme seu endereço de e-mail antes de solicitar um código.</p><Button label="Enviar link de confirmação" tone="secondary" onClick={verificarEmail} disabled={busy || !principal} /></>}
      {(auth.data?.data.user.has_usable_password || principal?.verified) && <Button type="submit" label={busy ? "Aguarde…" : !auth.data?.data.user.has_usable_password && !codigoEnviado ? "Enviar código" : "Confirmar identidade"} disabled={busy} />}
      <Button label="Cancelar" tone="ghost" disabled={busy} onClick={() => { setReauth(null); setSenha(""); setCodigo(""); }} />
    </form>}</section>}
    {erro && <p className={styles.error} role="alert">{erro}</p>}{aviso && <p role="status">{aviso}</p>}
    <LogoutButton />
  </div>;
}
