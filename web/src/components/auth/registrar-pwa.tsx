"use client";
import { useEffect } from "react";
export function RegistrarPwa() {
  useEffect(() => {
    if (!("serviceWorker" in navigator) || !window.isSecureContext) return;
    void navigator.serviceWorker.register("/sw-notificacoes.js").catch(() => {});
  }, []);
  return null;
}
