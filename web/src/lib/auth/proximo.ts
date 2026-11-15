"use client";

import { useSyncExternalStore } from "react";

/** Where to go after login/signup: only a local path (starts with "/", not "//", no scheme). */
export function proximoSeguro(valor: string | null | undefined): string | null {
  if (!valor || !valor.startsWith("/") || valor.startsWith("//") || valor.includes("\\")) return null;
  // Control characters could be stripped by the URL parser and turn the path into "//host".
  if ([...valor].some((c) => c.charCodeAt(0) < 32 || c.charCodeAt(0) === 127)) return null;
  const url = new URL(valor, "http://local.invalid");
  return url.origin === "http://local.invalid" ? valor : null;
}

export function proximoDaUrl(): string | null {
  return typeof window === "undefined" ? null : proximoSeguro(new URLSearchParams(window.location.search).get("proximo"));
}

const subscribe = () => () => {};

/** `proximo` of the current URL, read after hydration (null on the server). */
export function useProximo() {
  const search = useSyncExternalStore(subscribe, () => window.location.search, () => "");
  return proximoSeguro(new URLSearchParams(search).get("proximo"));
}

/** Appends a validated `proximo` to an auth link, so login ⇄ signup keeps the way back. */
export const comProximo = (href: string, proximo: string | null) => (proximo ? `${href}?proximo=${encodeURIComponent(proximo)}` : href);
