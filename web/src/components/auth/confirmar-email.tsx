"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { confirmarEmail, verificarChaveEmail } from "@/lib/auth/client";
import styles from "./auth.module.css";

export function ConfirmarEmail() {
  const chave = useRef("");
  const trava = useRef(false);
  const [estado, setEstado] = useState<"verificando" | "pronto" | "erro" | "concluido">("verificando");
  useEffect(() => {
    let ativo = true;
    if (!chave.current) {
      const partes = window.location.pathname.split("/");
      try { chave.current = decodeURIComponent(partes[partes.length - 1] ?? ""); } catch { chave.current = ""; }
      if (chave.current === "confirmar-email") chave.current = "";
    }
    window.history.replaceState(null, "", "/confirmar-email");
    if (!chave.current) { queueMicrotask(() => { if (ativo) setEstado("erro"); }); return () => { ativo = false; }; }
    void verificarChaveEmail(chave.current).then((info) => {
      if (!ativo) return;
      const hint = document.cookie.split("; ").find((item) => item.startsWith("varal_owner="))?.slice("varal_owner=".length);
      if (hint && hint !== "bloqueada" && hint !== info.data.user.id) { chave.current = ""; setEstado("erro"); return; }
      setEstado("pronto");
    }).catch(() => { if (ativo) { chave.current = ""; setEstado("erro"); } });
    return () => { ativo = false; };
  }, []);
  async function confirmar() {
    if (trava.current || !chave.current) return;
    trava.current = true;
    try { await confirmarEmail(chave.current); chave.current = ""; setEstado("concluido"); }
    catch { chave.current = ""; setEstado("erro"); }
    finally { trava.current = false; }
  }
  return <><h1 className={styles.title}>Confirmar e-mail</h1>
    {estado === "verificando" && <p role="status">Verificando link…</p>}
    {estado === "pronto" && <><p>Confirme este endereço para continuar.</p><Button label="Confirmar e-mail" onClick={confirmar} /></>}
    {estado === "erro" && <p role="alert">Este link é inválido, expirou ou pertence a outra conta.</p>}
    {estado === "concluido" && <p role="status">E-mail confirmado. Para ações protegidas, conclua também a reautenticação.</p>}
    <Link className={styles.link} href="/entrar">Voltar para Entrar</Link>
  </>;
}
