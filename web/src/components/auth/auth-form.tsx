// Doop: k0kB5dc-Vo / GJDSPaQbio + 7JTmWMAJup; CU01. Additional form states approved in chat.
"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Field } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { AuthError, csrfToken, getSession, validateResetKey } from "@/lib/auth/client";
import { useAuthConfig, useLogin, useRequestPassword, useResetPassword, useSignup } from "@/lib/auth/hooks";
import { useHydrated } from "@/lib/auth/hydration";
import { comProximo, proximoDaUrl, useProximo } from "@/lib/auth/proximo";
import styles from "./auth.module.css";

type Mode = "login" | "signup" | "request" | "reset";
const titles: Record<Mode, string> = { login: "Entrar", signup: "Criar conta", request: "Recuperar senha", reset: "Nova senha" };

function completedSession(data: Awaited<ReturnType<typeof getSession>>) {
  return data.meta.is_authenticated;
}

export function AuthForm({ mode, resetKey }: { mode: Mode; resetKey?: string }) {
  const hydrated = useHydrated();
  const proximo = useProximo();
  const config = useAuthConfig();
  const login = useLogin();
  const signup = useSignup();
  const requestPassword = useRequestPassword();
  const resetPassword = useResetPassword();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [notice, setNotice] = useState("");
  const [done, setDone] = useState(false);
  const messageRef = useRef<HTMLParagraphElement>(null);
  const providerForm = useRef<HTMLFormElement>(null);
  const mutation = mode === "login" ? login : mode === "signup" ? signup : mode === "request" ? requestPassword : resetPassword;
  const keyStatus = useQuery({
    queryKey: ["reset-key", resetKey],
    queryFn: () => validateResetKey(resetKey!),
    enabled: mode === "reset" && !!resetKey && !done,
    retry: false,
    gcTime: 0,
  });
  const authError = mutation.error instanceof AuthError ? mutation.error : undefined;
  const fieldError = (name: string) => authError?.issues.filter((issue) => issue.param === name).map((issue) => issue.message).join(" ") || undefined;
  const formError = mutation.error
    ? authError?.issues.filter((issue) => !issue.param).map((issue) => issue.message).join(" ") || (authError?.issues.length ? "Confira os campos indicados." : "Não foi possível concluir. Tente novamente.")
    : "";

  useEffect(() => {
    if (mode !== "login") return;
    const timer = window.setTimeout(() => { try {
      if (sessionStorage.getItem("varal.push.logout-aviso")) {
        sessionStorage.removeItem("varal.push.logout-aviso");
        setNotice("Não foi possível confirmar a desativação das notificações neste dispositivo.");
      }
    } catch { /* storage unavailable */ } }, 0);
    return () => window.clearTimeout(timer);
  }, [mode]);

  useEffect(() => {
    if (formError || notice || done) messageRef.current?.focus();
  }, [formError, notice, done]);

  function enterApp() {
    queryClient.clear();
    // A fresh request discards prefetched pages from the previous authentication state.
    window.location.replace(proximoDaUrl() ?? "/");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNotice("");
    try {
      if (mode === "login" || mode === "signup") {
        const result = mode === "login" ? await login.mutateAsync({ email, password }) : await signup.mutateAsync({ email, password });
        setPassword("");
        if (completedSession(result)) enterApp();
        else setNotice("Não foi possível entrar. Tente novamente.");
      } else if (mode === "request") {
        await requestPassword.mutateAsync({ email });
        setDone(true);
      } else if (resetKey) {
        await resetPassword.mutateAsync({ key: resetKey, password });
        setPassword("");
        queryClient.removeQueries({ queryKey: ["reset-key"] });
        setDone(true);
      }
    } catch {
      // The mutation holds the field errors; never echo credentials in an error message.
    }
  }

  async function google() {
    setNotice("");
    try {
      const result = config.data ?? (await config.refetch()).data;
      if (!result?.data.socialaccount?.providers.some((provider) => provider.id === "google")) {
        setNotice("O login com Google está indisponível no momento. Use seu e-mail para entrar ou criar uma conta.");
        return;
      }
      const form = providerForm.current;
      if (!form || !csrfToken()) {
        setNotice("Atualize a página e tente novamente.");
        return;
      }
      (form.elements.namedItem("csrfmiddlewaretoken") as HTMLInputElement).value = csrfToken();
      (form.elements.namedItem("callback_url") as HTMLInputElement).value = `${window.location.origin}${comProximo("/entrar/retorno", proximoDaUrl())}`;
      form.submit();
    } catch {
      setNotice("Não foi possível iniciar o login com Google. Tente novamente.");
    }
  }

  // A consumed reset key becomes invalid; that must not replace a completed reset's success state.
  const invalidKey = mode === "reset" && !done && (!resetKey || keyStatus.isError);
  const hasGoogle = mode === "login" || mode === "signup";

  return (
    <>
      <h1 className={styles.title}>{titles[mode]}</h1>
      {mode === "login" && <p className={styles.welcome}>Que bom te ver de novo.</p>}
      {mode === "request" && !done && <p className={styles.description}>Informe seu e-mail para receber um link e criar uma nova senha.</p>}
      {mode === "reset" && !done && !invalidKey && <p className={styles.description}>Escolha uma nova senha para sua conta.</p>}
      {hasGoogle && (
        <>
          <button className={styles.google} type="button" onClick={google} disabled={!hydrated || config.isFetching || mutation.isPending}>
            {/* The original Google mark from the approved Doop frame. */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/google.png" alt="" width="20" height="20" />
            Continuar com Google
          </button>
          <form ref={providerForm} hidden method="post" action="/api/auth/browser/v1/auth/provider/redirect">
            <input type="hidden" name="provider" value="google" />
            <input type="hidden" name="process" value="login" />
            <input type="hidden" name="callback_url" />
            <input type="hidden" name="csrfmiddlewaretoken" />
          </form>
          <div className={styles.divider}>ou com e-mail</div>
        </>
      )}
      {notice && <p className={styles.notice} role="status" tabIndex={-1} ref={messageRef}>{notice}</p>}
      {formError && <p className={styles.error} role="alert" tabIndex={-1} ref={messageRef}>{formError}</p>}
      {invalidKey ? (
        <>
          <p className={styles.error} role="alert">Este link é inválido ou expirou. Solicite um novo link para recuperar sua senha.</p>
          <Link className={styles.link} href="/recuperar-senha">Solicitar novo link</Link>
        </>
      ) : done ? (
        <>
          <p className={mode === "reset" ? styles.success : styles.notice} role="status" tabIndex={-1} ref={messageRef}>
            {mode === "request" ? "Se houver uma conta com esse e-mail, você receberá um link para criar uma nova senha." : "Senha alterada. Entre com sua nova senha."}
          </p>
          <Link className={styles.link} href="/entrar">Voltar para Entrar</Link>
        </>
      ) : (
        <form className={styles.fields} onSubmit={submit} aria-label={titles[mode]} aria-busy={!hydrated || mutation.isPending}>
          {mode !== "reset" && <Field label="E-mail" name="email" type="email" autoComplete="email" placeholder="voce@email.com" value={email} onChange={(event) => { setEmail(event.target.value); mutation.reset(); }} error={fieldError("email")} disabled={!hydrated || mutation.isPending} required />}
          {mode !== "request" && <Field label={mode === "reset" ? "Nova senha" : "Senha"} name="password" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} placeholder="••••••••" value={password} onChange={(event) => { setPassword(event.target.value); mutation.reset(); }} error={fieldError("password")} hint={mode === "signup" || mode === "reset" ? "Use pelo menos 8 caracteres. Evite senhas comuns e senhas feitas só de números." : undefined} trailing={mode === "login" ? <Link className={`${styles.link} ${styles.forgot}`} href="/recuperar-senha">Esqueci</Link> : undefined} disabled={!hydrated || mutation.isPending} required minLength={mode === "login" ? undefined : 8} />}
          <Button type="submit" width="full" label={mutation.isPending ? "Aguarde…" : mode === "request" ? "Enviar link" : mode === "reset" ? "Salvar nova senha" : titles[mode]} disabled={!hydrated || mutation.isPending || (mode === "reset" && keyStatus.isPending)} />
        </form>
      )}
      {mode === "login" ? <p className={styles.footer}>Ainda não tem conta? <Link className={styles.link} href={comProximo("/criar-conta", proximo)}>Criar conta</Link></p> : mode === "signup" ? <p className={styles.footer}>Já tem conta? <Link className={styles.link} href={comProximo("/entrar", proximo)}>Entrar</Link></p> : !done && <p className={styles.footer}><Link className={styles.link} href="/entrar">Voltar para Entrar</Link></p>}
    </>
  );
}

export function GoogleReturn() {
  const queryClient = useQueryClient();
  const session = useQuery({ queryKey: ["oauth-return"], queryFn: getSession, retry: false, gcTime: 0 });
  useEffect(() => {
    if (session.data?.meta.is_authenticated) {
      queryClient.clear();
      window.location.replace(proximoDaUrl() ?? "/");
    }
  }, [session.data, queryClient]);
  const failed = session.isError || (session.data && !session.data.meta.is_authenticated);
  return <><h1 className={styles.title}>Entrar</h1><p className={styles.notice} role="status">{failed ? "Não foi possível entrar com Google. Você pode tentar novamente ou usar seu e-mail." : "Concluindo sua entrada…"}</p>{failed && <Link className={styles.link} href="/entrar">Voltar para Entrar</Link>}</>;
}
