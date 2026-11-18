// Doop: k0kB5dc-Vo / shell 02 · Início + D02 · Início; Field, Button, Folha; Q11-11 (no dedicated Perfil frame).
// COR-09: redesigned presentation; same flows (preferences, export, delete, re-auth, logout) and protections.
"use client";

import { useRef, useState, type FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { LogoutButton } from "@/components/auth/logout-button";
import { Preferencias } from "@/components/notifications/avisos";
import { useSessao } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Folha } from "@/components/ui/folha";
import { Icon } from "@/components/ui/icon";
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
  const nome = user.nome?.trim() || "";
  const iniciais = (nome || user.email).split(/[\s@.]+/).filter(Boolean).slice(0, 2).map((parte) => parte[0]).join("").toUpperCase();
  const fecharReauth = () => { if (busy) return; setReauth(null); setSenha(""); setCodigo(""); setErro(""); };
  const mensagens = <>{erro && <p className={styles.error} role="alert">{erro}</p>}{aviso && <p className={styles.aviso} role="status">{aviso}</p>}</>;
  // COR-09: identity card, then two columns on desktop (preferences | data and privacy); the destructive
  // area sits apart, last, in its own tinted card. Re-authentication is a sheet/modal like every other flow.
  return <div className={styles.page}>
    <header className={styles.identidade}>
      <span className={styles.avatar} aria-hidden="true">{iniciais}</span>
      <div className={styles.quem}>
        <h1 title={nome || user.email}>{nome || "Seu perfil"}</h1>
        <p title={user.email}>{user.email}</p>
        <p className={styles.grupos}>{user.grupos.length ? `${user.grupos.length} ${user.grupos.length === 1 ? "grupo" : "grupos"}` : "Só o espaço pessoal"}</p>
      </div>
      <div className={styles.sair}><LogoutButton /></div>
    </header>
    {!reauth && mensagens}
    <div className={styles.colunas}>
      <div className={styles.coluna}>
        <section className={styles.cartao} aria-labelledby="dados-t">
          <h2 id="dados-t"><Icon name="perfil" size="md" />Seus dados</h2>
          <dl className={styles.dados}>
            <div><dt>Nome</dt><dd title={nome}>{nome || "Não informado"}</dd></div>
            <div><dt>E-mail</dt><dd title={user.email}>{user.email}</dd></div>
          </dl>
        </section>
        <div className={styles.cartao}><Preferencias user={user.id} /></div>
      </div>
      <div className={styles.coluna}>
        <section className={styles.cartao} aria-labelledby="exportar-t">
          <h2 id="exportar-t"><Icon name="baixar" size="md" />Exportar meus dados</h2>
          <p>Prepare um arquivo com seus dados pessoais e participações atuais. A exportação fica disponível por até 24 horas.</p>
          <div className={styles.actions}><Button label="Preparar exportação" tone="secondary" onClick={() => protegido("exportar")} disabled={busy || !!reauth} />{exportacao?.estado === "pronto" && <Button label="Baixar exportação" onClick={() => protegido("baixar")} disabled={busy || !!reauth} />}</div>
          {exportacao && <p className={styles.estado} data-estado={exportacao.estado} role="status">{exportacao.estado === "pronto" ? "Exportação pronta." : exportacao.estado === "falhou" ? "Não foi possível preparar a exportação." : exportacao.estado === "expirado" ? "Exportação expirada." : "Preparando exportação…"} Disponível até {new Date(exportacao.expira_em).toLocaleString("pt-BR", { timeZone: "America/Fortaleza" })}.</p>}
          {estado.isError && <p role="alert">Não foi possível consultar a exportação. <button type="button" className={styles.link} onClick={() => estado.refetch()}>Tentar novamente</button></p>}
        </section>
        <section className={`${styles.cartao} ${styles.perigo}`} aria-labelledby="excluir-t">
          <h2 id="excluir-t"><Icon name="alerta" size="md" />Excluir minha conta</h2>
          <p>Seus dados pessoais e sua conta serão excluídos. Dados e comprovantes dos grupos podem ser preservados conforme as regras do grupo.</p>
          {!intencao && <div className={styles.actions}><Button tone="danger" label="Preparar exclusão" disabled={busy || !!reauth} onClick={() => protegido("excluir")} /></div>}
          {intencao && <div className={styles.confirmar}><p>Confirme a exclusão até {new Date(intencao.expira_em).toLocaleString("pt-BR", { timeZone: "America/Fortaleza" })}. Isso não pode ser desfeito.</p><label className={styles.checkbox}><input type="checkbox" checked={confirmado} onChange={(event) => setConfirmado(event.target.checked)} disabled={busy || !!reauth} /> Quero excluir minha conta</label><Button tone="danger" label="Confirmar exclusão" disabled={!confirmado || busy || !!reauth} onClick={() => protegido("confirmar")} /></div>}
        </section>
      </div>
    </div>
    <Folha open={!!reauth} onClose={fecharReauth} busy={busy} title="Confirme sua identidade" subtitle="Por segurança, confirme antes de continuar.">
      {auth.isLoading || emails.isLoading ? <p role="status">Carregando…</p> : auth.isError || emails.isError ? <p role="alert">Não foi possível carregar as opções de confirmação.</p> : <form className={styles.form} onSubmit={provar}>
        {auth.data?.data.user.has_usable_password ? <Field label="Senha" type="password" autoComplete="current-password" value={senha} onChange={(event) => setSenha(event.target.value)} required autoFocus /> : principal?.verified ? codigoEnviado ? <Field label="Código de confirmação" value={codigo} onChange={(event) => setCodigo(event.target.value)} required autoFocus /> : <p>Enviaremos um código para seu e-mail verificado.</p> : <><p>Confirme seu endereço de e-mail antes de solicitar um código.</p><Button label="Enviar link de confirmação" tone="secondary" onClick={verificarEmail} disabled={busy || !principal} /></>}
        {reauth && mensagens}
        <div className={styles.actions}>
          {(auth.data?.data.user.has_usable_password || principal?.verified) && <Button type="submit" label={busy ? "Aguarde…" : !auth.data?.data.user.has_usable_password && !codigoEnviado ? "Enviar código" : "Confirmar identidade"} disabled={busy} />}
          <Button label="Cancelar" tone="ghost" disabled={busy} onClick={fecharReauth} />
        </div>
      </form>}
    </Folha>
  </div>;
}
