// No frame in the Doop (guide varal-ui, "Telas sem frame"): invite acceptance inside the login layout
// GJDSPaQbio (01 · Entrar) + 7JTmWMAJup (D01 · Entrar). CU03, RF05; RN24, RN31.
"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import styles from "@/components/auth/auth.module.css";
import button from "@/components/ui/button.module.css";
import { Button } from "@/components/ui/button";
import { PapelCard } from "@/components/ui/radio-card";
import { getSession } from "@/lib/auth/client";
import { useHydrated } from "@/lib/auth/hydration";
import { ApiError } from "@/lib/grupos/client";
import { useAceitarConvite, useConvitePublico } from "@/lib/grupos/hooks";
import { expiraEm, papeis } from "@/lib/grupos/papeis";
import { hrefDoGrupo } from "./grupos-lista";

export function AceiteConvite({ token }: { token: string }) {
  const hydrated = useHydrated();
  const queryClient = useQueryClient();
  const convite = useConvitePublico(token);
  const sessao = useQuery({ queryKey: ["sessao"], queryFn: getSession, retry: false, gcTime: 0 });
  const aceitar = useAceitarConvite(token);
  const volta = encodeURIComponent(`/c/${token}`);

  function aceito() {
    aceitar.mutate(undefined, {
      onSuccess(r) {
        queryClient.clear();
        // A full load refreshes /api/me/ (space selector) on the server.
        window.location.replace(hrefDoGrupo({ id: r.grupo_id, papel: r.papel }));
      },
    });
  }

  if (convite.isPending) return <p className={styles.notice} role="status">Abrindo o convite…</p>;
  if (convite.error)
    return (
      <>
        <h1 className={styles.title}>Convite</h1>
        <p className={styles.error} role="alert">
          {convite.error instanceof ApiError && convite.error.status === 410 ? convite.error.message : "Não foi possível abrir o convite. Tente novamente."}
        </p>
        <Link className={styles.link} href="/">Ir para o Varal</Link>
      </>
    );

  const { grupo_nome, papel, expira_em } = convite.data;
  const logado = sessao.data?.meta.is_authenticated;
  return (
    <>
      <p className={styles.description}>Convite para</p>
      <h1 className={styles.title}>{grupo_nome}</h1>
      <PapelCard {...papeis[papel]} />
      <p className={styles.description}>{expiraEm(expira_em)} · vale para 1 pessoa</p>
      {aceitar.error && <p className={styles.error} role="alert">{aceitar.error.message}</p>}
      {sessao.isPending ? (
        <p className={styles.notice} role="status">Verificando sua conta…</p>
      ) : logado ? (
        <Button width="full" label={aceitar.isPending ? "Aceitando…" : "Aceitar convite"} onClick={aceito} disabled={!hydrated || aceitar.isPending || aceitar.isSuccess} />
      ) : (
        <>
          <p className={styles.description}>Entre ou crie sua conta para aceitar. Depois você volta para este convite.</p>
          {/* Links with the Button look (same CSS module), since they navigate. */}
          <Link className={button.btn} data-tone="primary" data-width="full" href={`/entrar?proximo=${volta}`}>Entrar</Link>
          <Link className={button.btn} data-tone="ghost" data-width="full" href={`/criar-conta?proximo=${volta}`}>Criar conta</Link>
        </>
      )}
    </>
  );
}
