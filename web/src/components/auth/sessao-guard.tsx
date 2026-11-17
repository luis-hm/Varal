"use client";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { bloquearSessao, iniciarIdentidade } from "@/lib/auth/isolamento";

const abaOculta = () => document.visibilityState === "hidden";

export function SessaoGuard({ usuario, children }: { usuario: string; children: ReactNode }) {
  const cache = useQueryClient();
  useState(() => { if (typeof window !== "undefined") iniciarIdentidade(usuario); return null; });
  useEffect(() => {
    let vigente = true;
    let sequencia = 0;
    let restaurando = false;
    let novaRestauracao = false;
    let controlador: AbortController | null = null;
    function ocultar() {
      sequencia++;
      controlador?.abort();
      bloquearSessao();
      void cache.cancelQueries();
      cache.clear();
      document.querySelector<HTMLElement>("[data-sessao-privada]")?.setAttribute("hidden", "");
      document.documentElement.setAttribute("data-sessao-oculta", "");
    }
    async function restaurar() {
      if (restaurando) { novaRestauracao = true; return; }
      novaRestauracao = false;
      ocultar();
      restaurando = true;
      const atual = sequencia;
      controlador = new AbortController();
      try {
        const response = await fetch("/api/me/", { credentials: "same-origin", cache: "no-store", signal: controlador.signal, headers: { "X-Varal-Identidade-Esperada": usuario } });
        if (!vigente || atual !== sequencia || abaOculta()) return;
        if (!response.ok || response.headers.get("X-Varal-Identidade") !== usuario) return;
        const data: unknown = await response.json();
        if (!vigente || atual !== sequencia || abaOculta() || !data || typeof data !== "object" || !("id" in data) || data.id !== usuario) return;
        const hint = document.cookie.split("; ").find((v) => v.startsWith("varal_owner="))?.slice("varal_owner=".length);
        if (hint !== usuario || document.cookie.split("; ").some((v) => v.startsWith("varal_local_locked="))) return;
        // A fresh server render replaces stale state; no private snapshot is revealed in between.
        window.location.reload();
      } catch { /* offline remains masked; no financial replay */ }
      finally {
        restaurando = false; controlador = null;
        if (novaRestauracao && vigente && document.visibilityState !== "hidden") { novaRestauracao = false; void restaurar(); }
      }
    }
    const pagehide = () => ocultar();
    const pageshow = (event: PageTransitionEvent) => { if (event.persisted) void restaurar(); };
    const storage = (event: StorageEvent) => { if (event.key === "varal.sessao.evento" || event.key === "varal.auth.geracao.v1") ocultar(); };
    const visibilidade = () => { if (document.visibilityState === "hidden") ocultar(); else void restaurar(); };
    const channel = typeof BroadcastChannel === "undefined" ? null : new BroadcastChannel("varal-sessao-v1");
    if (channel) channel.onmessage = () => ocultar();
    window.addEventListener("pagehide", pagehide);
    window.addEventListener("pageshow", pageshow);
    window.addEventListener("storage", storage);
    window.addEventListener("varal-sessao-bloqueada", ocultar);
    document.addEventListener("visibilitychange", visibilidade);
    if (!abaOculta() && document.documentElement.hasAttribute("data-sessao-oculta")) void restaurar();
    return () => { vigente = false; controlador?.abort(); channel?.close(); window.removeEventListener("pagehide", pagehide); window.removeEventListener("pageshow", pageshow); window.removeEventListener("storage", storage); window.removeEventListener("varal-sessao-bloqueada", ocultar); document.removeEventListener("visibilitychange", visibilidade); };
  }, [cache, usuario]);
  return children;
}
