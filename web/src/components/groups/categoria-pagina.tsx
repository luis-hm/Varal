// Doop: k0kB5dc-Vo / 03 · Contas (bdiED7Q0I-) + D03 · Contas + Detalhe (cWdVUX2y8H), reached from 10 · Grupo
// (SfhuKVOQIF) + D04 (5UzCB5yNaI). No dedicated frame: COR-11 "Grupos → grupo → categoria → contas → detalhe".
// Same list, filters and detail as Contas, locked to one group and one category (or "Sem categoria").
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { ContasPagina } from "@/components/bills/contas-pagina";
import { Icon } from "@/components/ui/icon";
import { iconeDe, SEM_CATEGORIA } from "@/lib/categorias/icones";
import { ApiError } from "@/lib/grupos/client";
import { useGrupo } from "@/lib/grupos/hooks";
import styles from "./grupo.module.css";

export function CategoriaPagina({ grupoId, categoriaId, contaId }: { grupoId: string; categoriaId: string; contaId?: string }) {
  const router = useRouter();
  const grupo = useGrupo(grupoId);
  const status = grupo.error instanceof ApiError ? grupo.error.status : undefined;
  useEffect(() => {
    // RN07: the payer has no group pages, only the simple mode.
    if (status === 403) router.replace(`/grupos/${grupoId}/simples`);
  }, [status, grupoId, router]);

  const voltar = `/grupos/${encodeURIComponent(grupoId)}`;
  if (!grupo.data) {
    return (
      <div className={styles.leave}>
        <p className={grupo.error ? styles.erro : styles.empty} role={grupo.error ? "alert" : "status"}>
          {grupo.error ? grupo.error.message : "Carregando categoria…"}
        </p>
        {grupo.error && <Link href="/grupos">Ver meus grupos</Link>}
      </div>
    );
  }
  const sem = categoriaId === SEM_CATEGORIA;
  const categoria = grupo.data.casas.find((c) => c.id === categoriaId);
  if (!sem && !categoria) {
    // Archived or unknown: never reveal more than "not here".
    return (
      <div className={styles.leave} role="alert">
        <Icon name="alerta" size="xl" />
        <p className={styles.erro}>Categoria não encontrada.</p>
        <Link href={voltar}>Voltar para {grupo.data.nome}</Link>
      </div>
    );
  }
  return (
    <ContasPagina
      contaId={contaId}
      fixo={{
        espacoId: grupoId,
        categoria: sem ? "nenhum" : categoriaId,
        base: `${voltar}/categorias/${encodeURIComponent(categoriaId)}`,
        voltar,
        titulo: sem ? "Sem categoria" : categoria!.nome,
        subtitulo: grupo.data.nome,
        icone: sem ? "contas" : iconeDe(categoria!.icone),
      }}
    />
  );
}
