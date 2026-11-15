// Doop: k0kB5dc-Vo / componentes Button, Chip; folha sem frame (guia "Telas sem frame"). RF06, RN04, RN21, RN32
// (ADR 0007, CA22): a 409 conta_restrita_orfa opens the sheet listing the bills that would be left with nobody
// who sees them; each one gets "Escolher quem vê" or "Cancelar conta", then "Sair" resends with resolucoes.
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Folha } from "@/components/ui/folha";
import { ApiError, type ContaRestritaOrfa, type Resolucao } from "@/lib/grupos/client";
import { useAcoesGrupo } from "@/lib/grupos/hooks";
import styles from "./grupo.module.css";

type Escolha = { acao: "acesso"; usuarios: string[] } | { acao: "cancelar" };

function orfas(error: unknown): ContaRestritaOrfa | null {
  if (!(error instanceof ApiError) || error.status !== 409) return null;
  const d = error.data as Partial<ContaRestritaOrfa> | undefined;
  return d?.code === "conta_restrita_orfa" && Array.isArray(d.contas) ? (d as ContaRestritaOrfa) : null;
}

export function SairDoGrupo({ grupoId, grupoNome }: { grupoId: string; grupoNome: string }) {
  const router = useRouter();
  const { sair } = useAcoesGrupo(grupoId);
  const [barrada, setBarrada] = useState<ContaRestritaOrfa | null>(null);
  const [escolhas, setEscolhas] = useState<Record<string, Escolha>>({});

  function enviar(resolucoes?: Resolucao[]) {
    sair.mutate(resolucoes, {
      onSuccess() {
        setBarrada(null);
        router.replace("/grupos");
        router.refresh(); // the space selector reads the groups from /api/me/
      },
      onError(error) {
        const o = orfas(error);
        if (!o) return;
        // Keep what was already chosen for bills that still block.
        setEscolhas((atual) => Object.fromEntries(o.contas.flatMap((c) => (atual[c.id] ? [[c.id, atual[c.id]]] : []))));
        setBarrada(o);
      },
    });
  }

  function confirmar() {
    if (!window.confirm(`Sair de ${grupoNome}? Você perde o acesso ao grupo na hora.`)) return;
    setEscolhas({});
    enviar();
  }

  const resolvidas = barrada?.contas.every((c) => {
    const e = escolhas[c.id];
    return e && (e.acao === "cancelar" || e.usuarios.length > 0);
  });

  function sairResolvendo() {
    if (!barrada || !resolvidas) return;
    enviar(barrada.contas.map((c) => ({ lancamento: c.id, ...escolhas[c.id] })));
  }

  const alternar = (contaId: string, pessoa: string) =>
    setEscolhas((atual) => {
      const e = atual[contaId];
      const usuarios = e?.acao === "acesso" ? e.usuarios : [];
      const novos = usuarios.includes(pessoa) ? usuarios.filter((u) => u !== pessoa) : [...usuarios, pessoa];
      return { ...atual, [contaId]: { acao: "acesso", usuarios: novos } };
    });

  const erroFolha = barrada && sair.error && !orfas(sair.error) ? sair.error.message : null;

  return (
    <div className={styles.leave}>
      <Button tone="ghost" label={sair.isPending && !barrada ? "Saindo…" : "Sair do grupo"} onClick={confirmar} disabled={sair.isPending} />
      {sair.error && !barrada && !orfas(sair.error) && <p className={styles.erro} role="alert">{sair.error.message}</p>}

      <Folha
        open={!!barrada}
        onClose={() => setBarrada(null)}
        title={`Antes de sair de ${grupoNome}`}
        actions={<Button tone="danger" label={sair.isPending ? "Saindo…" : "Sair"} onClick={sairResolvendo} disabled={!resolvidas || sair.isPending} />}
      >
        {barrada && (
          <div className={styles.form}>
            <p>{barrada.detail}</p>
            <ul className={styles.orfas}>
              {barrada.contas.map((c) => {
                const e = escolhas[c.id];
                return (
                  <li key={c.id}>
                    <Link href={`/contas/${c.id}`} className={styles.orfaNome}>
                      {c.descricao}
                    </Link>
                    <div className={styles.orfaAcoes} role="group" aria-label={`O que fazer com ${c.descricao}`}>
                      <Chip label="Escolher quem vê" state={e?.acao === "acesso" ? "on" : "off"} onClick={() => setEscolhas({ ...escolhas, [c.id]: { acao: "acesso", usuarios: e?.acao === "acesso" ? e.usuarios : [] } })} />
                      <Chip label="Cancelar conta" state={e?.acao === "cancelar" ? "on" : "off"} onClick={() => setEscolhas({ ...escolhas, [c.id]: { acao: "cancelar" } })} />
                    </div>
                    {e?.acao === "acesso" &&
                      (barrada.pessoas.length ? (
                        <div className={styles.orfaAcoes} role="group" aria-label={`Quem vê ${c.descricao}`}>
                          {barrada.pessoas.map((p) => (
                            <Chip key={p.id} label={p.nome} state={e.usuarios.includes(p.id) ? "on" : "off"} onClick={() => alternar(c.id, p.id)} />
                          ))}
                        </div>
                      ) : (
                        <p className={styles.aviso}>Não há mais ninguém no grupo que possa ver esta conta. Cancele a conta para sair.</p>
                      ))}
                  </li>
                );
              })}
            </ul>
            {erroFolha && <p className={styles.erro} role="alert">{erroFolha}</p>}
          </div>
        )}
      </Folha>
    </div>
  );
}
