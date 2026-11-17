// Doop: k0kB5dc-Vo / Button; CU01. Logout is the only addition to the Perfil placeholder.
"use client";

import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { useLogout } from "@/lib/auth/hooks";
import { useHydrated } from "@/lib/auth/hydration";
import { identidadeAtual, marcarSaidaLocal } from "@/lib/auth/isolamento";
import styles from "./auth.module.css";

export function LogoutButton() {
  const hydrated = useHydrated();
  const logout = useLogout();
  const queryClient = useQueryClient();
  async function leave() {
    const usuario = identidadeAtual();
    marcarSaidaLocal();
    void queryClient.cancelQueries();
    queryClient.clear();
    try {
      if (usuario) await logout.mutateAsync(usuario);
      else throw new Error("Sessão indisponível.");
    } catch {
      try { sessionStorage.setItem("varal.logout.pendente", "1"); } catch { /* offline state stays locally locked */ }
    }
    window.location.replace("/entrar");
  }
  return <div className={styles.logout}><Button label={logout.isPending ? "Saindo…" : "Sair da conta"} tone="secondary" onClick={leave} disabled={!hydrated || logout.isPending} />{logout.error && <p className={styles.error} role="alert">Não foi possível sair. Tente novamente.</p>}</div>;
}
