"use client";
// COR-01: switching tabs never asks for a new login. The private tree is masked only when the identity
// actually changed (local logout, another account in another tab, server says the session ended) and on
// pagehide, so a BFCache snapshot never shows data before a fresh check. A same-user return just revalidates.
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { bloquearSessao, cookie, desbloquearSessao, iniciarIdentidade, marcaValida } from "@/lib/auth/isolamento";

type Motivo = "verificando" | "encerrada";
const TEXTOS: Record<Motivo, string> = {
  verificando: "Verificando sua sessão…",
  encerrada: "Sua sessão terminou. Entre de novo para continuar.",
};

function mascarar(motivo: Motivo) {
  document.querySelector<HTMLElement>("[data-sessao-privada]")?.setAttribute("hidden", "");
  document.documentElement.setAttribute("data-sessao-oculta", "");
  const status = document.querySelector<HTMLElement>("[data-sessao-status]");
  if (status) {
    status.dataset.motivo = motivo;
    const texto = status.querySelector("[data-sessao-texto]");
    if (texto) texto.textContent = TEXTOS[motivo];
  }
}

function revelar() {
  document.querySelector<HTMLElement>("[data-sessao-privada]")?.removeAttribute("hidden");
  document.documentElement.removeAttribute("data-sessao-oculta");
}

export function SessaoGuard({ usuario, children }: { usuario: string; children: ReactNode }) {
  const cache = useQueryClient();
  useState(() => { if (typeof window !== "undefined") iniciarIdentidade(usuario); return null; });
  useEffect(() => {
    let vigente = true;
    let controlador: AbortController | null = null;

    function encerrar() {
      controlador?.abort();
      bloquearSessao();
      void cache.cancelQueries();
      cache.clear();
      mascarar("encerrada");
    }

    async function revalidar() {
      if (!marcaValida(usuario)) return encerrar();
      revelar();
      controlador?.abort();
      controlador = new AbortController();
      let response: Response;
      try {
        response = await fetch("/api/me/", { credentials: "same-origin", cache: "no-store", signal: controlador.signal, headers: { "X-Varal-Identidade-Esperada": usuario } });
      } catch {
        return; // Offline or aborted: same identity, keep working; queries show their own errors.
      }
      if (!vigente) return;
      if (response.status === 401 || response.status === 403) return encerrar();
      if (!response.ok) return; // 5xx: transient, keep the screen.
      const data: unknown = await response.json().catch(() => null);
      if (!vigente) return;
      const id = data && typeof data === "object" && "id" in data ? data.id : null;
      if (id !== usuario) {
        // Another account owns this browser now: a fresh server render replaces every private byte.
        encerrar();
        window.location.reload();
        return;
      }
      desbloquearSessao();
      void cache.invalidateQueries();
    }

    // First paint: the server rendered for `usuario`; remember it as this browser's owner hint.
    if (marcaValida(usuario)) {
      if (!cookie("varal_owner")) document.cookie = `varal_owner=${encodeURIComponent(usuario)}; Path=/; SameSite=Lax; Max-Age=1209600`;
      revelar();
    } else encerrar();

    const pagehide = () => mascarar("verificando");
    const pageshow = (event: PageTransitionEvent) => { if (event.persisted) { mascarar("verificando"); void revalidar(); } };
    const visibilidade = () => { if (document.visibilityState === "visible") void revalidar(); };
    const outraAba = () => { if (!marcaValida(usuario)) encerrar(); else void revalidar(); };
    const storage = (event: StorageEvent) => { if (event.key === "varal.sessao.evento" || event.key === "varal.auth.geracao.v1") outraAba(); };
    const channel = typeof BroadcastChannel === "undefined" ? null : new BroadcastChannel("varal-sessao-v1");
    if (channel) channel.onmessage = outraAba;
    window.addEventListener("pagehide", pagehide);
    window.addEventListener("pageshow", pageshow);
    window.addEventListener("storage", storage);
    window.addEventListener("varal-sessao-bloqueada", encerrar);
    document.addEventListener("visibilitychange", visibilidade);
    return () => {
      vigente = false;
      controlador?.abort();
      channel?.close();
      window.removeEventListener("pagehide", pagehide);
      window.removeEventListener("pageshow", pageshow);
      window.removeEventListener("storage", storage);
      window.removeEventListener("varal-sessao-bloqueada", encerrar);
      document.removeEventListener("visibilitychange", visibilidade);
    };
  }, [cache, usuario]);
  return children;
}
