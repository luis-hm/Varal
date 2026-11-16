// Doop: k0kB5dc-Vo / 05 · Nova conta (0PfC8pBVwF) + M01 (oOhe6pYOzx): header and "Onde fica esta conta?";
// 06 · Conferir conta (tKY4nFTZ3-) + M02 (Sre1zOcaE-): Valor, Vencimento, Descrição, Casa, Quem paga, "Salvar conta".
// No frame (guide varal-ui "Telas sem frame"): "Quem vê" people, the visibility notice and "Cancelar conta".
// CU05 (manual), CU07; RF10–RF12, RN05, RN06, RN11, RN22, Q3, Q16, Q19b, CA28. Not here until their stage:
// PDF area, "Colar código", "Se repete", code, issue date, payee (05/06/08) and "+ Nova" house.
"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent, type ReactNode } from "react";
import { useSessao } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Field } from "@/components/ui/field";
import { Folha } from "@/components/ui/folha";
import { Icon } from "@/components/ui/icon";
import type { ContaDetalhe, ContaEntrada } from "@/lib/contas/client";
import { lerValor, valorEditavel } from "@/lib/contas/formato";
import { useAcoesConta } from "@/lib/contas/hooks";
import { espacosParaCriar } from "@/lib/espaco";
import { ApiError, type Membro } from "@/lib/grupos/client";
import { useGrupo } from "@/lib/grupos/hooks";
import styles from "./conta-folha.module.css";

export const AVISO_VISIBILIDADE = "Quem paga também vê esta conta";

type Pessoa = { id: string; nome: string };

// `pagador` and `acesso` take user ids, not membership ids.
function usuarioDe(m: Membro, meuId: string): string {
  return m.sou_eu ? meuId : m.usuario;
}

function pessoas(membros: Membro[], papeis: Membro["papel"][], meuId: string): Pessoa[] {
  return membros
    .filter((m) => papeis.includes(m.papel))
    .flatMap((m) => {
      const id = usuarioDe(m, meuId);
      return id ? [{ id, nome: m.sou_eu ? "Eu" : m.nome || m.email || "" }] : [];
    })
    .sort((a, b) => Number(b.nome === "Eu") - Number(a.nome === "Eu"));
}

type Props = {
  open: boolean;
  onClose: () => void;
  /** Without a bill: create (Q3). With one: edit and cancel (CU07). */
  conta?: ContaDetalhe;
};

export function ContaFolha({ open, onClose, conta }: Props) {
  const router = useRouter();
  const { user, espaco: atual } = useSessao();
  const { criar, editar, cancelar } = useAcoesConta();
  const espacos = espacosParaCriar(user, atual.id); // ajuste 30: current space first and selected
  const [espacoId, setEspacoId] = useState(conta?.espaco.id ?? espacos[0].id);
  const espaco = conta?.espaco ?? espacos.find((e) => e.id === espacoId)!;
  const emGrupo = espaco.tipo === "grupo";
  const grupo = useGrupo(espaco.id, emGrupo);

  const [valor, setValor] = useState(conta ? valorEditavel(conta.valor_centavos) : "");
  const [vencimento, setVencimento] = useState(conta?.vencimento ?? "");
  const [descricao, setDescricao] = useState(conta?.descricao ?? "");
  const [casa, setCasa] = useState<string | null>(conta?.subgrupo?.id ?? null);
  // Q16: "Eu" pre-selected; whoever creates in a group is admin or member, so can pay.
  const [pagador, setPagador] = useState<string | null>(conta ? (conta.pagador?.id ?? null) : user.id);
  const [visibilidade, setVisibilidade] = useState(conta?.visibilidade ?? "grupo");
  const [acesso, setAcesso] = useState<string[]>(conta?.acesso.map((p) => p.id) ?? []);
  const [local, setLocal] = useState<Record<string, string>>({});

  const membros = grupo.data?.membros ?? [];
  const pagadores = pessoas(membros, ["admin", "membro", "pagador"], user.id);
  if (conta?.pagador && !pagadores.some((p) => p.id === conta.pagador!.id)) pagadores.push(conta.pagador);
  // Decision 7: new people only admin, member or observer; whoever is already in "Quem vê" stays (ADR 0008).
  // Creating: whoever creates always sees it, so "Eu" is not an option; editing keeps it (Q19b).
  const quemVe = pessoas(membros, ["admin", "membro", "observador"], user.id).filter((p) => conta || p.id !== user.id);
  for (const p of conta?.acesso ?? []) if (!quemVe.some((q) => q.id === p.id)) quemVe.push(p);
  // Q20: a bill of an archived house keeps and shows it.
  const casas = [...(grupo.data?.casas ?? [])];
  if (conta?.subgrupo && !casas.some((c) => c.id === conta.subgrupo!.id)) casas.push(conta.subgrupo);

  const erro = criar.error ?? editar.error ?? cancelar.error;
  const api = erro instanceof ApiError ? erro.campos : {};
  const erros = {
    valor: local.valor ?? api.valor_centavos,
    vencimento: local.vencimento ?? api.vencimento,
    descricao: local.descricao ?? api.descricao,
    casa: api.subgrupo,
    pagador: api.pagador,
    // Q19b: "Você é a única pessoa que vê esta conta…" comes back on `acesso`.
    acesso: api.acesso ?? api.visibilidade,
  };
  const geral = erro && !Object.values(erros).some(Boolean) ? erro.message : undefined;
  const ocupado = criar.isPending || editar.isPending || cancelar.isPending;
  const aviso = emGrupo && visibilidade === "restrita" && !!pagador && pagador !== user.id;

  function trocarEspaco(id: string) {
    setEspacoId(id);
    setCasa(null);
    setPagador(user.id);
    setVisibilidade("grupo");
    setAcesso([]);
  }

  function salvar(event: FormEvent) {
    event.preventDefault();
    const centavos = lerValor(valor);
    const faltas: Record<string, string> = {};
    if (centavos === null) faltas.valor = "Informe um valor maior que zero, como 287,43.";
    if (!vencimento) faltas.vencimento = "Informe o vencimento.";
    if (!descricao.trim()) faltas.descricao = "Dê um nome para a conta.";
    setLocal(faltas);
    if (Object.keys(faltas).length) return;
    const body: ContaEntrada = {
      descricao: descricao.trim(),
      valor_centavos: centavos!,
      vencimento,
      ...(emGrupo && { subgrupo: casa, pagador, visibilidade, acesso: visibilidade === "restrita" ? acesso : [] }),
    };
    if (conta) return editar.mutate({ id: conta.id, body }, { onSuccess: onClose });
    criar.mutate(
      { espaco: espaco.id, body },
      {
        onSuccess(nova) {
          onClose();
          // The new bill, in its month's list (desktop: list + panel; mobile: its detail).
          router.push(`/contas/${nova.id}?mes=${nova.vencimento.slice(0, 7)}`);
        },
      },
    );
  }

  const podeCancelar = conta && (conta.status === "pendente" || conta.status === "aguardando");
  return (
    <Folha
      open={open}
      onClose={onClose}
      title={conta ? "Editar conta" : "Nova conta"}
      actions={<Button type="submit" form="conta-form" label={ocupado ? "Salvando…" : conta ? "Salvar" : "Salvar conta"} disabled={ocupado} />}
    >
      <form id="conta-form" className={styles.form} onSubmit={salvar} noValidate>
        {!conta && (
          <div className={styles.onde} role="group" aria-labelledby="onde-t">
            <span id="onde-t" className={styles.lb}>
              <span className={styles.mob}>Onde fica esta conta?</span>
              <span className={styles.desk}>Onde fica:</span>
            </span>
            <div className={styles.row}>
              {espacos.map((e) => (
                <Chip key={e.id} label={e.nome} wrap state={e.id === espaco.id ? "on" : "off"} onClick={() => trocarEspaco(e.id)} />
              ))}
            </div>
          </div>
        )}

        <div className={styles.g2}>
          <Field label="Valor" inputMode="decimal" placeholder="R$ 0,00" value={valor} onChange={(e) => setValor(e.target.value)} error={erros.valor} required autoFocus={!!conta} />
          <Field label="Vencimento" type="date" value={vencimento} onChange={(e) => setVencimento(e.target.value)} error={erros.vencimento} required />
        </div>
        <Field label="Descrição" placeholder="Energia · Casa 3" maxLength={150} value={descricao} onChange={(e) => setDescricao(e.target.value)} error={erros.descricao} required />

        {emGrupo && grupo.isPending && <p className={styles.nota} role="status">Carregando casas e pessoas…</p>}
        {emGrupo && grupo.data && (
          <>
            <div className={styles.g2}>
              {!!casas.length && (
                <Escolha titulo="Casa" erro={erros.casa}>
                  <Chip label="Sem casa" state={casa === null ? "on" : "off"} onClick={() => setCasa(null)} />
                  {casas.map((c) => (
                    <Chip key={c.id} label={c.nome} wrap state={casa === c.id ? "on" : "off"} onClick={() => setCasa(c.id)} />
                  ))}
                </Escolha>
              )}
              <Escolha titulo="Quem paga" erro={erros.pagador}>
                {pagadores.map((p) => (
                  <Chip key={p.id} label={p.nome} state={pagador === p.id ? "on" : "off"} onClick={() => setPagador(p.id)} />
                ))}
                <Chip label="Ninguém" state={pagador === null ? "on" : "off"} onClick={() => setPagador(null)} />
              </Escolha>
            </div>
            {/* CA28: said at once, before saving, and read out by screen readers. */}
            <p className={styles.aviso} aria-live="polite" data-vazio={!aviso || undefined}>
              {aviso && (
                <>
                  <Icon name="cadeado" size="sm" />
                  {AVISO_VISIBILIDADE}
                </>
              )}
            </p>
            <Escolha titulo="Quem vê" erro={erros.acesso}>
              <Chip label="Todo o grupo" state={visibilidade === "grupo" ? "on" : "off"} onClick={() => setVisibilidade("grupo")} />
              <Chip label="Só algumas pessoas" state={visibilidade === "restrita" ? "on" : "off"} onClick={() => setVisibilidade("restrita")} />
            </Escolha>
            {visibilidade === "restrita" && (
              <Escolha titulo="Quem mais vê" nota="Quem criou e quem paga sempre veem a conta.">
                {quemVe.map((p) => (
                  <Chip
                    key={p.id}
                    label={p.nome}
                    state={acesso.includes(p.id) ? "on" : "off"}
                    onClick={() => setAcesso(acesso.includes(p.id) ? acesso.filter((id) => id !== p.id) : [...acesso, p.id])}
                  />
                ))}
                {!quemVe.length && <span className={styles.nota}>Ninguém mais no grupo para escolher.</span>}
              </Escolha>
            )}
          </>
        )}

        {geral && <p className={styles.erro} role="alert">{geral}</p>}
        {podeCancelar && (
          <Button
            tone="danger"
            label={cancelar.isPending ? "Cancelando…" : "Cancelar conta"}
            disabled={ocupado}
            onClick={() => {
              if (window.confirm(`Cancelar ${conta.descricao}? Ela sai das listas e dos totais e fica no histórico.`))
                cancelar.mutate(conta.id, { onSuccess: onClose });
            }}
          />
        )}
      </form>
    </Folha>
  );
}

function Escolha({ titulo, nota, erro, children }: { titulo: string; nota?: string; erro?: string; children: ReactNode }) {
  return (
    <div role="group" aria-label={titulo}>
      <span className={styles.lb}>{titulo}</span>
      <div className={styles.row}>{children}</div>
      {nota && <p className={styles.nota}>{nota}</p>}
      {erro && (
        <p className={styles.erro} role="alert">
          {erro}
        </p>
      )}
    </div>
  );
}
