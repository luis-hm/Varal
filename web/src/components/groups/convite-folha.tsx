// Doop: k0kB5dc-Vo / 11 · Convidar membro (bkv_O9ohNO) + M05 · Convidar membro (8XSFrkwy2d); CU03, RF05, RN24, RN31.
"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Folha } from "@/components/ui/folha";
import { Icon } from "@/components/ui/icon";
import { RadioCard } from "@/components/ui/radio-card";
import type { ConviteCriado, Papel } from "@/lib/grupos/client";
import { useAcoesGrupo } from "@/lib/grupos/hooks";
import { encurtarLink, ordemPapeis, papeis } from "@/lib/grupos/papeis";
import styles from "./grupo.module.css";

/** Owner of the invite sheet: call `abrir()` from the click that opens it (no effect, no double request). */
export function useConvite(grupoId: string) {
  const { criarConvite, revogarConvite } = useAcoesGrupo(grupoId);
  const [open, setOpen] = useState(false);
  const [papel, setPapel] = useState<Papel>("pagador");
  // The full URL (bearer token, RN31) lives only here, in memory.
  const [convite, setConvite] = useState<ConviteCriado | null>(null);
  const usado = useRef(false);

  function descartar() {
    // Closing or switching role without copying/sharing revokes the unused link (ADR 0004).
    if (convite && !usado.current) revogarConvite.mutate(convite.id);
  }

  function gerar(p: Papel) {
    usado.current = false;
    setConvite(null);
    criarConvite.mutate(p, { onSuccess: setConvite });
  }

  return {
    open,
    papel,
    convite,
    gerando: criarConvite.isPending,
    erro: criarConvite.error?.message,
    abrir() {
      setOpen(true);
      setPapel("pagador");
      gerar("pagador");
    },
    trocar(p: Papel) {
      if (p === papel) return;
      descartar();
      setPapel(p);
      gerar(p);
    },
    tentarDeNovo: () => gerar(papel),
    marcarUsado() {
      usado.current = true;
    },
    fechar() {
      descartar();
      setConvite(null);
      setOpen(false);
    },
  };
}

export function ConviteFolha({ grupoNome, estado }: { grupoNome: string; estado: ReturnType<typeof useConvite> }) {
  const { open, papel, convite, gerando, erro } = estado;
  const [aviso, setAviso] = useState("");

  async function copiar() {
    if (!convite) return;
    try {
      await navigator.clipboard.writeText(convite.url);
      estado.marcarUsado();
      setAviso("Link copiado.");
    } catch {
      setAviso("Não foi possível copiar. Tente compartilhar.");
    }
  }

  async function compartilhar() {
    if (!convite) return;
    if (typeof navigator.share !== "function") return copiar();
    try {
      await navigator.share({ title: `Convite para ${grupoNome}`, text: `Entre no grupo ${grupoNome} no Varal.`, url: convite.url });
      estado.marcarUsado();
      setAviso("");
    } catch (error) {
      // Cancelled by the person: the link stays unused. Any other failure falls back to copying.
      if (!(error instanceof DOMException && error.name === "AbortError")) await copiar();
    }
  }

  return (
    <Folha
      open={open}
      onClose={() => {
        setAviso("");
        estado.fechar();
      }}
      title="Convidar para o grupo"
      subtitle={`${grupoNome} · escolha o que a pessoa poderá fazer`}
      size="convite"
      actions={<Button label="Compartilhar convite" icon="pedir" onClick={compartilhar} disabled={!convite} />}
    >
      <div role="radiogroup" aria-label="Papel" className={styles.papeis}>
        {ordemPapeis.map((p) => (
          <RadioCard
            key={p}
            name="papel-convite"
            value={p}
            state={p === papel ? "on" : "off"}
            onChange={() => {
              setAviso("");
              estado.trocar(p);
            }}
            {...papeis[p]}
          />
        ))}
      </div>
      {/* key: a new link restarts the shine (2 passes, then it stops). */}
      <div key={convite?.id ?? "vazio"} className={styles.link} data-shine={convite ? "on" : "off"}>
        <span className={styles.linkText}>
          {convite ? (
            <>
              <span className={styles.srOnly}>Link do convite, encurtado: </span>
              <b>{encurtarLink(convite.url)}</b>
            </>
          ) : (
            <b aria-live="polite">{erro ? "Não foi possível gerar o link." : gerando ? "Gerando link…" : ""}</b>
          )}
          <span className={styles.linkMeta}>Expira em 7 dias · vale para 1 pessoa</span>
        </span>
        {erro && !gerando ? (
          <button type="button" className={styles.round} onClick={estado.tentarDeNovo} aria-label="Gerar o link de novo">
            <Icon name="repetir" size="md" />
          </button>
        ) : (
          <button type="button" className={styles.round} onClick={copiar} disabled={!convite} aria-label="Link do convite, copiar">
            <Icon name="copiar" size="md" />
          </button>
        )}
      </div>
      <p className={styles.aviso} role="status">{aviso}</p>
    </Folha>
  );
}
