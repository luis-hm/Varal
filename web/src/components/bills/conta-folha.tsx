// Doop: k0kB5dc-Vo / 05 · Nova conta (0PfC8pBVwF) + M01 (oOhe6pYOzx): header and "Onde fica esta conta?";
// 06 · Conferir conta (tKY4nFTZ3-) + M02 (Sre1zOcaE-): Valor, Vencimento, Descrição, Casa, Quem paga, "Salvar conta".
// No frame (guide varal-ui "Telas sem frame"): "Quem vê" people, the visibility notice and "Cancelar conta".
// CU05, CU07; RF08–RF12, RN05, RN06, RN08–RN11, RN22, Q3, Q16, Q19b, CA28.
// PDF, issue date, recurrence and "+ Nova" house stay in their stages (06/08).
"use client";

import { useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState, type FormEvent, type ReactNode } from "react";
import { useSessao } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Field } from "@/components/ui/field";
import { Folha } from "@/components/ui/folha";
import { Icon } from "@/components/ui/icon";
import type { ContaDetalhe, ContaEntrada, InstrumentoEntrada, Leitura } from "@/lib/contas/client";
import { lerValor, valorEditavel } from "@/lib/contas/formato";
import { useAcoesConta, useLerInstrumento } from "@/lib/contas/hooks";
import { espacosParaCriar } from "@/lib/espaco";
import { ApiError, type Membro } from "@/lib/grupos/client";
import { useGrupo } from "@/lib/grupos/hooks";
import styles from "./conta-folha.module.css";
import instrumentoStyles from "./instrumento.module.css";

export const AVISO_VISIBILIDADE = "Quem paga também vê esta conta";

type Pessoa = { id: string; nome: string };
type Modo = "manual" | "codigo" | "chave";
const tipos = { boleto_bancario: "Boleto bancário", boleto_arrecadacao: "Boleto de arrecadação", pix: "Pix" };

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
  // A form session owns its initial instrument. Remote refetches do not replace local entry/preview.
  const [inicial] = useState(() => conta?.instrumento && { ...conta.instrumento });
  const [modo, setModo] = useState<Modo>(inicial?.chave_pix ? "chave" : inicial?.codigo ? "codigo" : "manual");
  const [conteudo, setConteudo] = useState(inicial?.codigo ?? inicial?.chave_pix ?? "");
  const [conferencia, setConferencia] = useState<Leitura | null>(null);
  const [instrumentoAlterado, setInstrumentoAlterado] = useState(false);
  const leitura = useLerInstrumento();
  const { mutate: ler } = leitura;
  const versaoLeitura = useRef(0);
  const gravacao = useRef(false);
  const codigoId = useId();
  const dataId = useId();
  const podeTrocarInstrumento = !conta || conta.status === "pendente" || conta.status === "aguardando";

  // Existing instruments are checked again to expose the actual encoded fields and date choices.
  // Keep the persisted values (including a legacy date); this read is not an edit.
  useEffect(() => {
    if (!open || instrumentoAlterado || (!inicial?.codigo && !inicial?.chave_pix)) return;
    let ativo = true;
    const versao = ++versaoLeitura.current;
    const entrada = inicial.codigo ? { codigo: inicial.codigo } : { chave_pix: inicial.chave_pix! };
    ler(entrada, { onSuccess: (dados) => { if (ativo && versao === versaoLeitura.current) setConferencia(dados); } });
    return () => { ativo = false; };
  }, [open, inicial?.codigo, inicial?.chave_pix, instrumentoAlterado, ler]);

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
    instrumento: local.instrumento ?? api.instrumento ?? api.codigo ?? api.chave_pix,
  };
  const geral = erro && !Object.values(erros).some(Boolean) ? erro.message : undefined;
  const gravando = criar.isPending || editar.isPending || cancelar.isPending;
  const ocupado = gravando || leitura.isPending;
  const aviso = emGrupo && visibilidade === "restrita" && !!pagador && pagador !== user.id;

  function trocarEspaco(id: string) {
    if (gravacao.current) return;
    setEspacoId(id);
    setCasa(null);
    setPagador(user.id);
    setVisibilidade("grupo");
    setAcesso([]);
  }

  function mudarEntrada(novoModo: Modo, texto: string) {
    if (gravacao.current) return;
    versaoLeitura.current++;
    leitura.reset();
    criar.reset();
    editar.reset();
    setModo(novoModo);
    setConteudo(texto);
    setConferencia(null);
    setInstrumentoAlterado(true);
    setLocal((erros) => { const restantes = { ...erros }; delete restantes.instrumento; return restantes; });
  }

  function conferir() {
    if (gravacao.current) return;
    const entrada: InstrumentoEntrada = modo === "chave" ? { chave_pix: conteudo } : { codigo: conteudo };
    const versao = ++versaoLeitura.current;
    ler(entrada, {
      onSuccess(dados) {
        if (versao !== versaoLeitura.current) return;
        setConferencia(dados);
        setValor(dados.valor_centavos !== null ? valorEditavel(dados.valor_centavos) : "");
        setVencimento(dados.vencimento ?? "");
        setLocal({});
      },
    });
  }

  function salvar(event: FormEvent) {
    event.preventDefault();
    if (gravacao.current || leitura.isPending) return;
    const centavos = lerValor(valor);
    const faltas: Record<string, string> = {};
    if (centavos === null) faltas.valor = "Informe um valor maior que zero, como 287,43.";
    if (!vencimento) faltas.vencimento = "Informe o vencimento.";
    if (!descricao.trim()) faltas.descricao = "Dê um nome para a conta.";
    if (modo !== "manual" && !conferencia) faltas.instrumento = "Confira o código ou a chave antes de salvar.";
    setLocal(faltas);
    if (Object.keys(faltas).length) return;
    const body: ContaEntrada = {
      descricao: descricao.trim(),
      valor_centavos: centavos!,
      vencimento,
      ...(emGrupo && { subgrupo: casa, pagador, visibilidade, acesso: visibilidade === "restrita" ? acesso : [] }),
      ...((!conta || instrumentoAlterado) && modo !== "manual" ? { instrumento: modo === "chave" ? { chave_pix: conteudo } : { codigo: conteudo } } : instrumentoAlterado ? { instrumento: null } : {}),
    };
    // The synchronous latch also covers repeated submits before React paints the pending state.
    gravacao.current = true;
    const terminou = () => { gravacao.current = false; };
    if (conta) return editar.mutate({ id: conta.id, body }, { onSuccess: onClose, onSettled: terminou });
    criar.mutate(
      { espaco: espaco.id, body },
      {
        onSuccess(nova) {
          onClose();
          // The new bill, in its month's list (desktop: list + panel; mobile: its detail).
          router.push(`/contas/${nova.id}?mes=${nova.vencimento.slice(0, 7)}`);
        },
        onSettled: terminou,
      },
    );
  }

  const podeCancelar = conta && (conta.status === "pendente" || conta.status === "aguardando");
  return (
    <Folha
      open={open}
      onClose={() => { if (!gravacao.current) onClose(); }}
      busy={gravando}
      title={conta ? "Editar conta" : "Nova conta"}
      actions={<Button type="submit" form="conta-form" label={ocupado ? "Salvando…" : conta ? "Salvar" : "Salvar conta"} disabled={ocupado} />}
    >
      <form id="conta-form" className={styles.form} onSubmit={salvar} noValidate>
        <fieldset className={styles.campos} disabled={gravando}>
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

        {podeTrocarInstrumento && (
          <Escolha titulo="Como cadastrar">
            <Chip label="Digitar conta" state={modo === "manual" ? "on" : "off"} onClick={() => mudarEntrada("manual", "")} />
            <Chip label="Colar código" state={modo === "codigo" ? "on" : "off"} onClick={() => mudarEntrada("codigo", "")} />
            <Chip label="Chave Pix" state={modo === "chave" ? "on" : "off"} onClick={() => mudarEntrada("chave", "")} />
          </Escolha>
        )}
        {modo !== "manual" && (
          <div className={instrumentoStyles.conferencia}>
            {modo === "codigo" ? (
              <div className={instrumentoStyles.campo}>
                <label htmlFor={codigoId} className={instrumentoStyles.rotulo}>Linha digitável ou Pix copia e cola</label>
                <textarea id={codigoId} className={instrumentoStyles.entrada} value={conteudo} onChange={(e) => mudarEntrada(modo, e.target.value)} maxLength={4096} rows={3} readOnly={!podeTrocarInstrumento} spellCheck={false} autoCapitalize="none" aria-invalid={!!(erros.instrumento || leitura.error) || undefined} aria-describedby={`${codigoId}-mensagem`} />
              </div>
            ) : (
              <Field label="Chave Pix" value={conteudo} onChange={(e) => mudarEntrada(modo, e.target.value)} maxLength={77} readOnly={!podeTrocarInstrumento} autoCapitalize="none" autoComplete="off" spellCheck={false} error={erros.instrumento || leitura.error?.message} />
            )}
            {podeTrocarInstrumento && <Button tone="secondary" label={leitura.isPending ? "Conferindo…" : modo === "chave" ? "Conferir chave" : "Ler código"} onClick={conferir} disabled={leitura.isPending || !conteudo.trim()} />}
            {modo === "codigo" && <p id={`${codigoId}-mensagem`} className={instrumentoStyles.erro} role="alert">{erros.instrumento || leitura.error?.message}</p>}
            {conferencia && (
              <>
                <p className={instrumentoStyles.dados} role="status">{tipos[conferencia.instrumento.tipo]} conferido. Confira os dados antes de salvar.</p>
                {conferencia.avisos.map((aviso, i) => <p key={i} className={instrumentoStyles.nota}>{aviso}</p>)}
                {conferencia.instrumento.beneficiario && <Field label="Beneficiário" value={conferencia.instrumento.beneficiario} readOnly filled hint="Informado no código" />}
              </>
            )}
          </div>
        )}

        <div className={styles.g2}>
          <Field label="Valor" inputMode="decimal" placeholder="R$ 0,00" value={valor} onChange={(e) => setValor(e.target.value)} error={erros.valor} required autoFocus={!!conta} readOnly={conferencia?.valor_centavos != null} filled={conferencia?.valor_centavos != null} hint={conferencia?.valor_centavos != null ? "Do código" : undefined} />
          {conferencia && conferencia.vencimentos_possiveis.length > 1 ? (
            <div className={instrumentoStyles.campo}>
              <label htmlFor={dataId} className={instrumentoStyles.rotulo}>Vencimento</label>
              <select id={dataId} className={instrumentoStyles.data} value={vencimento} onChange={(e) => setVencimento(e.target.value)} aria-invalid={!!erros.vencimento || undefined} aria-describedby={`${dataId}-nota${erros.vencimento ? ` ${dataId}-erro` : ""}`}>
                {conferencia.vencimentos_possiveis.map((data) => <option key={data} value={data}>{data.split("-").reverse().join("/")}</option>)}
              </select>
              <p id={`${dataId}-nota`} className={instrumentoStyles.nota}>O fator permite duas datas. Escolha a que está no boleto.</p>
              {erros.vencimento && <p id={`${dataId}-erro`} className={instrumentoStyles.erro} role="alert">{erros.vencimento}</p>}
            </div>
          ) : <Field label="Vencimento" type="date" value={vencimento} onChange={(e) => setVencimento(e.target.value)} error={erros.vencimento} required readOnly={!!conferencia?.vencimento} filled={!!conferencia?.vencimento} hint={conferencia?.vencimento ? "Do código" : undefined} />}
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
              if (gravacao.current) return;
              if (window.confirm(`Cancelar ${conta.descricao}? Ela sai das listas e dos totais e fica no histórico.`)) {
                gravacao.current = true;
                cancelar.mutate(conta.id, { onSuccess: onClose, onSettled: () => { gravacao.current = false; } });
              }
            }}
          />
        )}
        </fieldset>
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
