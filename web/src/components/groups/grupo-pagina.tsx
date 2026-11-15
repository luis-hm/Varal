// Doop: k0kB5dc-Vo / 10 · Grupo (SfhuKVOQIF) + D04 · Grupo (5UzCB5yNaI); CU02, CU03, CU04; RN04, RN05, RN07, RN21.
// Stage 03 hides what later stages fill (spec CA18): bill totals and bars, "Paga N contas", recurring bills,
// settings and "Gerenciar papéis". Observers get the same page with no action; the payer never gets here (403).
"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Folha } from "@/components/ui/folha";
import { Icon } from "@/components/ui/icon";
import { RadioCard } from "@/components/ui/radio-card";
import { ApiError, type Casa, type GrupoDetalhe, type Membro, type Papel } from "@/lib/grupos/client";
import { useAcoesGrupo, useConvitesPendentes, useGrupo } from "@/lib/grupos/hooks";
import { expiraEm, iniciais, ordemPapeis, papeis } from "@/lib/grupos/papeis";
import { ConviteFolha, useConvite } from "./convite-folha";
import { HouseCard } from "./house-card";
import { MemberRow } from "./member-row";
import { SairDoGrupo } from "./sair-do-grupo";
import styles from "./grupo.module.css";

const plural = (n: number, um: string, varios: string) => `${n} ${n === 1 ? um : varios}`;
export const nomeDoMembro = (m: Membro) => m.nome || m.email;

export function GrupoPagina({ id }: { id: string }) {
  const router = useRouter();
  const grupo = useGrupo(id);
  const status = grupo.error instanceof ApiError ? grupo.error.status : undefined;

  useEffect(() => {
    // RN07 / decision 6: the payer has no group page, only the simple mode.
    if (status === 403) router.replace(`/grupos/${id}/simples`);
  }, [status, id, router]);

  if (grupo.data) return <Conteudo grupo={grupo.data} />;
  if (status === 403) return <p className={styles.empty} role="status">Abrindo o modo simples…</p>;
  if (grupo.error)
    return (
      <div className={styles.leave}>
        <p className={styles.erro} role="alert">{grupo.error.message}</p>
        <Button tone="secondary" label="Ver meus grupos" onClick={() => router.push("/grupos")} />
      </div>
    );
  return <p className={styles.empty} role="status">Carregando grupo…</p>;
}

function Conteudo({ grupo }: { grupo: GrupoDetalhe }) {
  const admin = grupo.meu_papel === "admin";
  const acoes = useAcoesGrupo(grupo.id);
  const convite = useConvite(grupo.id);
  const pendentes = useConvitesPendentes(grupo.id, admin);
  const [membro, setMembro] = useState<Membro | null>(null);
  const [casa, setCasa] = useState<Casa | "nova" | null>(null);

  return (
    <div className={styles.page}>
      <header className={`${styles.header} ${styles.in}`}>
        <span className={styles.mark}>
          <Icon name="varal" size="xl" />
        </span>
        <div className={styles.ident}>
          <h1>{grupo.nome}</h1>
          <p>
            {plural(grupo.membros.length, "membro", "membros")} · {plural(grupo.casas.length, "casa", "casas")} · você é{" "}
            {papeis[grupo.meu_papel].title.toLowerCase()}
          </p>
        </div>
        {admin && <Button className={styles.headerAction} label="Convidar pessoa" icon="mais" onClick={convite.abrir} aria-haspopup="dialog" />}
      </header>

      <div className={styles.body}>
        <div className={styles.colA}>
          <section className={`${styles.in} ${styles.d1}`} aria-labelledby="casas-t">
            <div className={styles.sec}>
              <h2 id="casas-t">Casas</h2>
              {admin && (
                <button type="button" className={styles.secAction} onClick={() => setCasa("nova")} aria-haspopup="dialog">
                  + Nova casa
                </button>
              )}
            </div>
            {grupo.casas.length ? (
              <div className={styles.houses}>
                {grupo.casas.map((c) => (
                  <HouseCard key={c.id} label={c.nome} caption="Sem contas ainda" onClick={admin ? () => setCasa(c) : undefined} />
                ))}
              </div>
            ) : (
              <p className={`${styles.card} ${styles.empty}`}>Nenhuma casa ainda.</p>
            )}
          </section>
        </div>

        <div className={styles.colB}>
          <section className={`${styles.in} ${styles.d2}`} aria-labelledby="membros-t">
            <div className={styles.sec}>
              <h2 id="membros-t">Membros</h2>
              {admin && (
                <button type="button" className={`${styles.secAction} ${styles.mobileOnly}`} onClick={convite.abrir} aria-haspopup="dialog">
                  + Convidar
                </button>
              )}
            </div>
            <div className={styles.card}>
              {grupo.membros.map((m) => (
                <MemberRow
                  key={m.id}
                  role={m.papel}
                  initials={iniciais(nomeDoMembro(m))}
                  name={m.sou_eu ? `${nomeDoMembro(m)} (você)` : nomeDoMembro(m)}
                  onClick={admin ? () => setMembro(m) : undefined}
                />
              ))}
            </div>
          </section>

          {admin && !!pendentes.data?.length && (
            <section className={`${styles.in} ${styles.d3}`} aria-labelledby="pendentes-t">
              <div className={styles.sec}>
                <h2 id="pendentes-t">Convites pendentes</h2>
              </div>
              <div className={styles.card}>
                {pendentes.data.map((c) => (
                  <div key={c.id} className={styles.pending}>
                    <span>
                      <b>{papeis[c.papel].title}</b>
                      <small>{expiraEm(c.expira_em)}{c.criado_por_nome ? ` · por ${c.criado_por_nome}` : ""}</small>
                    </span>
                    <Button
                      tone="ghost"
                      label="Revogar"
                      aria-label={`Revogar convite de ${papeis[c.papel].title.toLowerCase()}`}
                      disabled={acoes.revogarConvite.isPending}
                      onClick={() => acoes.revogarConvite.mutate(c.id)}
                    />
                  </div>
                ))}
              </div>
            </section>
          )}

          <p className={`${styles.privacy} ${styles.in} ${styles.d3}`}>
            <Icon name="cadeado" size="md" />
            <span>Suas contas pessoais nunca aparecem aqui. Só o que está no grupo é visto pelos membros.</span>
          </p>
        </div>
      </div>

      <SairDoGrupo grupoId={grupo.id} grupoNome={grupo.nome} />

      {admin && (
        <>
          <ConviteFolha grupoNome={grupo.nome} estado={convite} />
          <MembroFolha grupoId={grupo.id} membro={membro} onClose={() => setMembro(null)} />
          <CasaFolha grupoId={grupo.id} casa={casa} onClose={() => setCasa(null)} />
        </>
      )}
    </div>
  );
}

function MembroFolha({ grupoId, membro, onClose }: { grupoId: string; membro: Membro | null; onClose: () => void }) {
  const router = useRouter();
  const { alterarPapel, remover } = useAcoesGrupo(grupoId);
  const [papel, setPapel] = useState<Papel | null>(null);
  const escolhido = papel ?? membro?.papel ?? "membro";
  const erro = alterarPapel.error?.message ?? remover.error?.message;
  const ocupado = alterarPapel.isPending || remover.isPending;

  function fechar() {
    setPapel(null);
    alterarPapel.reset();
    remover.reset();
    onClose();
  }

  function depois(saiu = false) {
    // Changing or removing yourself changes what /api/me/ says (selector, payer redirect).
    if (membro?.sou_eu) {
      if (saiu) router.replace("/grupos");
      router.refresh();
    }
    fechar();
  }

  const nome = membro ? nomeDoMembro(membro) : "";
  return (
    <Folha
      open={!!membro}
      onClose={fechar}
      title={nome}
      subtitle={membro?.nome ? membro.email : "Papel no grupo"}
      actions={
        <>
          <Button
            tone="danger"
            label="Remover do grupo"
            disabled={ocupado}
            onClick={() => {
              if (membro && window.confirm(`Remover ${nome} do grupo? A pessoa perde o acesso na hora.`)) remover.mutate(membro.id, { onSuccess: () => depois(true) });
            }}
          />
          <Button
            label={alterarPapel.isPending ? "Salvando…" : "Salvar papel"}
            disabled={ocupado || escolhido === membro?.papel}
            onClick={() => membro && alterarPapel.mutate({ membro: membro.id, papel: escolhido }, { onSuccess: () => depois() })}
          />
        </>
      }
    >
      <div role="radiogroup" aria-label="Papel" className={styles.papeis}>
        {ordemPapeis.map((p) => (
          <RadioCard key={p} name="papel-membro" value={p} state={p === escolhido ? "on" : "off"} onChange={() => setPapel(p)} {...papeis[p]} />
        ))}
      </div>
      {erro && <p className={styles.erro} role="alert">{erro}</p>}
    </Folha>
  );
}

function CasaFolha({ grupoId, casa, onClose }: { grupoId: string; casa: Casa | "nova" | null; onClose: () => void }) {
  const { criarCasa, alterarCasa } = useAcoesGrupo(grupoId);
  const [nome, setNome] = useState<string | null>(null);
  const nova = casa === "nova";
  const valor = nome ?? (casa && !nova ? casa.nome : "");
  const erro = criarCasa.error?.message ?? alterarCasa.error?.message;
  const ocupado = criarCasa.isPending || alterarCasa.isPending;

  function fechar() {
    setNome(null);
    criarCasa.reset();
    alterarCasa.reset();
    onClose();
  }

  function salvar(event: FormEvent) {
    event.preventDefault();
    const limpo = valor.trim();
    if (!limpo) return;
    if (nova) criarCasa.mutate(limpo, { onSuccess: fechar });
    else if (casa) alterarCasa.mutate({ casa: casa.id, nome: limpo }, { onSuccess: fechar });
  }

  return (
    <Folha
      open={!!casa}
      onClose={fechar}
      title={nova ? "Nova casa" : "Editar casa"}
      actions={
        <>
          {!nova && casa && (
            <Button
              tone="ghost"
              label="Arquivar casa"
              disabled={ocupado}
              onClick={() => {
                if (window.confirm(`Arquivar ${casa.nome}? Ela sai da lista do grupo.`)) alterarCasa.mutate({ casa: casa.id, arquivado: true }, { onSuccess: fechar });
              }}
            />
          )}
          <Button type="submit" form="casa-form" label={ocupado ? "Salvando…" : nova ? "Criar" : "Salvar"} disabled={ocupado || !valor.trim()} />
        </>
      }
    >
      <form id="casa-form" className={styles.form} onSubmit={salvar}>
        <Field label="Nome da casa" value={valor} onChange={(e) => setNome(e.target.value)} maxLength={150} required autoFocus placeholder="Casa da praia" error={erro} />
      </form>
    </Folha>
  );
}
