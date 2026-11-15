// Doop: k0kB5dc-Vo / componente Button; RF06 (leave the group, any role), RN04.
"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAcoesGrupo } from "@/lib/grupos/hooks";
import styles from "./grupo.module.css";

export function SairDoGrupo({ grupoId, grupoNome }: { grupoId: string; grupoNome: string }) {
  const router = useRouter();
  const { sair } = useAcoesGrupo(grupoId);
  function confirmar() {
    if (!window.confirm(`Sair de ${grupoNome}? Você perde o acesso ao grupo na hora.`)) return;
    sair.mutate(undefined, {
      onSuccess() {
        router.replace("/grupos");
        router.refresh(); // the space selector reads the groups from /api/me/
      },
    });
  }
  return (
    <div className={styles.leave}>
      <Button tone="ghost" label={sair.isPending ? "Saindo…" : "Sair do grupo"} onClick={confirmar} disabled={sair.isPending} />
      {sair.error && <p className={styles.erro} role="alert">{sair.error.message}</p>}
    </div>
  );
}
