// Doop: k0kB5dc-Vo / 10 · Grupo (SfhuKVOQIF) + D04 · Grupo (5UzCB5yNaI); CU02, CU03, CU04; RN04, RN05, RN07,
// RN13, RN21. COR-04/07/11: "Casas" became "Categorias" with an icon; a card opens the category's bills, the
// pencil edits it (admin), "Sem categoria" appears whenever it holds bills and "Ver todas as contas" lists the
// whole group. Observers get the same page with no admin action; the payer never gets here (403).
"use client";

import { useConfirmar } from "@/components/ui/confirmar";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Field } from "@/components/ui/field";
import { Folha } from "@/components/ui/folha";
import { Icon } from "@/components/ui/icon";
import { RadioCard } from "@/components/ui/radio-card";
import { RecorrenciasFolha } from "@/components/recurrences/recorrencias-folha";
import { RecurringRow } from "@/components/recurrences/recurring-row";
import { ICONES_CATEGORIA, iconeDe, SEM_CATEGORIA, type IconeCategoria } from "@/lib/categorias/icones";
import { nomeMes, plural, reais, totalConhecido } from "@/lib/contas/formato";
import { useRecorrencias, useResumo } from "@/lib/contas/hooks";
import { ApiError, type Casa, type GrupoDetalhe, type Membro, type Papel } from "@/lib/grupos/client";
import { useAcoesGrupo, useConvitesPendentes, useGrupo, usePreviewArquivamento } from "@/lib/grupos/hooks";
import { expiraEm, iniciais, ordemPapeis, papeis } from "@/lib/grupos/papeis";
import { ConviteFolha, useConvite } from "./convite-folha";
import { HouseCard } from "./house-card";
import { estadoRecorrencia } from "@/components/recurrences/estado";
import { MemberRow } from "./member-row";
import { SairDoGrupo } from "./sair-do-grupo";
import styles from "./grupo.module.css";

// The API always sends the e-mail when there is no name (RNF04 minimisation).
export const nomeDoMembro = (m: Membro) => m.nome || m.email || "";

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
  const abrirConvite = useRef(convite.abrir);
  useEffect(() => {
    // CU02: a freshly created group arrives with ?convidar=1 and opens the invite once.
    if (!admin || new URLSearchParams(window.location.search).get("convidar") !== "1") return;
    window.history.replaceState(window.history.state, "", window.location.pathname);
    abrirConvite.current();
  }, [admin]);
  const pendentes = useConvitesPendentes(grupo.id, admin);
  const [membro, setMembro] = useState<Membro | null>(null);
  const [casa, setCasa] = useState<Casa | "nova" | null>(null);
  const [config, setConfig] = useState(false);
  const [recorrencias, setRecorrencias] = useState<string | true | false>(false); // id = open on that recurrence
  const modelos = useRecorrencias(grupo.id);
  const [configN, setConfigN] = useState(0); // fresh form on every opening, kept mounted to return focus
  const abrirConfig = () => {
    setConfigN((n) => n + 1);
    setConfig(true);
  };
  // Q11/Q12: real month totals per category, only from the bills you see (RN06). COR-07: the "Sem categoria"
  // line (id null) gets its own card so no part of the total disappears.
  const resumo = useResumo(grupo.id);
  const porCasa = new Map(resumo.data?.por_casa.map((c) => [c.id, c]));
  const semCategoria = porCasa.get(null);
  const mes = resumo.data ? nomeMes(resumo.data.mes) : "";
  const legenda = (total?: (typeof resumo.data & object)["por_casa"][number]) => ({
    caption: resumo.data ? `${total?.valores_indefinidos_qtd ? "Total conhecido: " : ""}${totalConhecido(total?.total_centavos ?? 0, total?.valores_indefinidos_qtd ?? 0)} em ${mes}` : "…",
    "caption-2": resumo.data ? (total?.abertas_qtd ? `${plural(total.abertas_qtd, "conta", "contas")} a pagar` : total?.qtd ? `${total.pagas_qtd} de ${total.qtd} pagas` : "Nada a pagar") : undefined,
    progress: total?.qtd ? total.pagas_qtd / total.qtd * 100 : undefined,
  });
  const urlCategoria = (id: string) => `/grupos/${encodeURIComponent(grupo.id)}/categorias/${encodeURIComponent(id)}`;

  return (
    <div className={styles.page}>
      <header className={`${styles.header} ${styles.in}`}>
        <span className={styles.mark}>
          <Icon name="varal" size="xl" />
        </span>
        <div className={styles.ident}>
          <h1>{grupo.nome}</h1>
          <p>
            {plural(grupo.membros.length, "membro", "membros")} · {plural(grupo.casas.length, "categoria", "categorias")} · você é{" "}
            {papeis[grupo.meu_papel].title.toLowerCase()}
          </p>
        </div>
        {admin && (
          <>
            <button type="button" className={`${styles.round} ${styles.mobileOnly}`} aria-label="Configurações" onClick={abrirConfig} aria-haspopup="dialog">
              <Icon name="manual" size="md" />
            </button>
            <Button className={styles.headerAction} tone="secondary" label="Configurações" icon="manual" onClick={abrirConfig} aria-haspopup="dialog" />
            <Button className={styles.headerAction} label="Convidar pessoa" icon="mais" onClick={convite.abrir} aria-haspopup="dialog" />
          </>
        )}
      </header>

      <div className={styles.body}>
        <div className={styles.colA}>
          <section className={`${styles.in} ${styles.d1}`} aria-labelledby="casas-t">
            <div className={styles.sec}>
              <h2 id="casas-t">Categorias</h2>
              {admin && (
                <button type="button" className={styles.secAction} onClick={() => setCasa("nova")} aria-haspopup="dialog">
                  + Nova categoria
                </button>
              )}
            </div>
            {grupo.casas.length || semCategoria ? (
              <div className={styles.houses}>
                {grupo.casas.map((c) => (
                  <HouseCard key={c.id} label={c.nome} icon={iconeDe(c.icone)} href={urlCategoria(c.id)} onEditar={admin ? () => setCasa(c) : undefined} {...legenda(porCasa.get(c.id))} />
                ))}
                {semCategoria && <HouseCard label="Sem categoria" icon="contas" href={urlCategoria(SEM_CATEGORIA)} {...legenda(semCategoria)} />}
              </div>
            ) : (
              <p className={`${styles.card} ${styles.empty}`}>
                {admin ? "Organize as contas em categorias, como Luz, Internet ou Aluguel." : "Nenhuma categoria ainda."}
              </p>
            )}
            <Link className={styles.todas} href={`/contas?espaco=${encodeURIComponent(grupo.id)}`}>
              <Icon name="contas" size="md" />
              <span>Ver todas as contas do grupo</span>
              <Icon name="chevron" size="sm" />
            </Link>
          </section>
          <section className={`${styles.in} ${styles.d2}`} aria-labelledby="recorrencias-t">
            <div className={styles.sec}><h2 id="recorrencias-t">Contas que se repetem</h2><button type="button" className={styles.secAction} onClick={() => setRecorrencias(true)}>Ver todas</button></div>
            <div className={styles.card}>{modelos.data?.length ? modelos.data.slice(0, 5).map((r) => <RecurringRow key={r.id} text={r.descricao} caption={`Dia ${r.dia_vencimento} · ${r.valor_tipo === "fixo" ? "valor fixo" : "valor muda"} · ${estadoRecorrencia(r.estado)}`} vl={r.valor_centavos == null ? "Valor a definir" : reais(r.valor_centavos)} onClick={() => setRecorrencias(r.id)} />) : <p className={styles.empty}>{modelos.isPending ? "Carregando recorrências…" : modelos.error ? "Não foi possível carregar as recorrências." : "Nenhuma conta que se repete."}</p>}</div>
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
                  detail={`Paga ${plural(m.contas_atribuidas_qtd, "conta", "contas")} em ${mes || "este mês"}`}
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
      {recorrencias && <RecorrenciasFolha open espacoId={grupo.id} pessoal={false} inicial={recorrencias === true ? undefined : recorrencias} onClose={() => setRecorrencias(false)} />}

      {admin && (
        <>
          <ConviteFolha grupoNome={grupo.nome} estado={convite} />
          <MembroFolha grupoId={grupo.id} membro={membro} onClose={() => setMembro(null)} />
          <CasaFolha grupoId={grupo.id} casa={casa} casas={grupo.casas} onClose={() => setCasa(null)} />
          {configN > 0 && <ConfiguracoesFolha key={configN} open={config} grupo={grupo} onClose={() => setConfig(false)} />}
        </>
      )}
    </div>
  );
}

function MembroFolha({ grupoId, membro, onClose }: { grupoId: string; membro: Membro | null; onClose: () => void }) {
  const [pedir, confirmacao] = useConfirmar();
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
      subtitle={(membro?.nome && membro.email) || "Papel no grupo"}
      actions={
        <>
          <Button
            tone="danger"
            label="Remover do grupo"
            disabled={ocupado}
            onClick={async () => {
              if (membro && await pedir(`Remover ${nome} do grupo? A pessoa perde o acesso na hora.`, "Remover do grupo")) remover.mutate(membro.id, { onSuccess: () => depois(true) });
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
      {confirmacao}
    </Folha>
  );
}

function CasaFolha({ grupoId, casa, casas, onClose }: { grupoId: string; casa: Casa | "nova" | null; casas: Casa[]; onClose: () => void }) {
  const { criarCasa, alterarCasa } = useAcoesGrupo(grupoId);
  const [nome, setNome] = useState<string | null>(null);
  const [icone, setIcone] = useState<IconeCategoria | null>(null);
  const [arquivando, setArquivando] = useState(false);
  const trava = useRef(false);
  const [destino, setDestino] = useState<string | null>(null);
  const preview = usePreviewArquivamento(grupoId, arquivando && casa && casa !== "nova" ? casa.id : undefined);
  const nova = casa === "nova";
  const valor = nome ?? (casa && !nova ? casa.nome : "");
  const iconeEscolhido: IconeCategoria = icone ?? (casa && !nova ? (iconeDe(casa.icone) as IconeCategoria) : "casa");
  const erro = criarCasa.error?.message ?? alterarCasa.error?.message;
  const ocupado = criarCasa.isPending || alterarCasa.isPending;

  function fechar() {
    if (trava.current) return;
    setNome(null);
    setIcone(null);
    setArquivando(false); setDestino(null);
    criarCasa.reset();
    alterarCasa.reset();
    onClose();
  }

  function salvar(event: FormEvent) {
    event.preventDefault();
    if (trava.current) return;
    const limpo = valor.trim();
    if (!limpo) return;
    trava.current = true;
    const sucesso = () => { trava.current = false; fechar(); };
    const terminou = () => { trava.current = false; };
    if (nova) criarCasa.mutate({ nome: limpo, icone: iconeEscolhido }, { onSuccess: sucesso, onSettled: terminou });
    else if (casa) alterarCasa.mutate({ casa: casa.id, nome: limpo, icone: iconeEscolhido }, { onSuccess: sucesso, onSettled: terminou });
    else trava.current = false;
  }

  return (
    <Folha
      open={!!casa}
      onClose={fechar}
      busy={ocupado}
      title={arquivando ? "Arquivar categoria" : nova ? "Nova categoria" : "Editar categoria"}
      actions={
        <>
          {arquivando && casa && !nova ? <Button tone="danger" label={ocupado ? "Arquivando…" : "Confirmar arquivamento"} disabled={ocupado || preview.isPending || !!preview.error} onClick={() => { if (trava.current) return; trava.current = true; alterarCasa.mutate({ casa: casa.id, arquivado: true, destino_subgrupo: destino }, { onSuccess: () => { trava.current = false; fechar(); }, onSettled: () => { trava.current = false; } }); }} /> : <>{!nova && casa && (
            <Button
              tone="ghost"
              label="Arquivar categoria"
              disabled={ocupado}
              onClick={() => {
                setArquivando(true);
              }}
            />
          )}
          <Button type="submit" form="casa-form" label={ocupado ? "Salvando…" : nova ? "Criar" : "Salvar"} disabled={ocupado || !valor.trim()} /></>}
        </>
      }
    >
      {arquivando ? <div className={styles.form}>
        <p>Escolha onde deixar as contas abertas e recorrências que você pode alterar.</p>
        {preview.isPending ? <p role="status">Carregando…</p> : preview.error ? <p role="alert">Não foi possível consultar a categoria.</p> : preview.data && <p>{plural(preview.data.contas_qtd, "conta", "contas")} · {plural(preview.data.recorrencias_qtd, "recorrência", "recorrências")}</p>}
        <div role="group" aria-label="Destino"><Chip label="Sem categoria" state={destino === null ? "on" : "off"} onClick={() => setDestino(null)} />{casas.filter((c) => c.id !== (casa && casa !== "nova" ? casa.id : "") && !c.arquivado).map((c) => <Chip key={c.id} label={c.nome} wrap state={destino === c.id ? "on" : "off"} onClick={() => setDestino(c.id)} />)}</div>
        {erro && <p role="alert" className={styles.erro}>{erro}</p>}
      </div> : <form id="casa-form" className={styles.form} onSubmit={salvar}>
        <Field label="Nome da categoria" value={valor} onChange={(e) => setNome(e.target.value)} maxLength={150} required autoFocus placeholder="Luz, Internet, Casa da praia…" error={erro} />
        <fieldset className={styles.icones}>
          <legend>Ícone</legend>
          <div className={styles.iconesGrade}>
            {ICONES_CATEGORIA.map(([nomeIcone, rotulo]) => (
              <label key={nomeIcone} className={styles.icone} data-on={iconeEscolhido === nomeIcone || undefined} title={rotulo}>
                <input type="radio" name="icone-categoria" value={nomeIcone} checked={iconeEscolhido === nomeIcone} onChange={() => setIcone(nomeIcone)} />
                <Icon name={nomeIcone} size="md" label={rotulo} />
              </label>
            ))}
          </div>
        </fieldset>
      </form>}
    </Folha>
  );
}

/** Q10 / RN13: "Avisar N dias antes", 1 to 7, admin only. No frame (guide "Telas sem frame"). */
function ConfiguracoesFolha({ open, grupo, onClose }: { open: boolean; grupo: GrupoDetalhe; onClose: () => void }) {
  const { configurar } = useAcoesGrupo(grupo.id);
  const [dias, setDias] = useState(String(grupo.janela_alerta_dias));
  const n = Number(dias);
  const valido = Number.isInteger(n) && n >= 1 && n <= 7;

  function salvar(event: FormEvent) {
    event.preventDefault();
    if (valido) configurar.mutate(n, { onSuccess: onClose });
  }

  return (
    <Folha
      open={open}
      onClose={onClose}
      title="Configurações"
      subtitle={grupo.nome}
      actions={<Button type="submit" form="config-form" label={configurar.isPending ? "Salvando…" : "Salvar"} disabled={configurar.isPending || !valido} />}
    >
      <form id="config-form" className={styles.form} onSubmit={salvar}>
        <Field
          label="Avisar quantos dias antes do vencimento"
          type="number"
          inputMode="numeric"
          min={1}
          max={7}
          value={dias}
          onChange={(e) => setDias(e.target.value)}
          hint="De 1 a 7 dias. Com esse prazo a conta aparece como “vence em breve” e entra em “Precisa de atenção”."
          error={!valido ? "Escolha de 1 a 7 dias." : configurar.error?.message}
          required
        />
      </form>
    </Folha>
  );
}
