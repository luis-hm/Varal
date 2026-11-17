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
import { RepeticaoCampo } from "@/components/recurrences/repeticao-campo";
import { EscopoRecorrencia } from "@/components/recurrences/escopo-recorrencia";
import type { ContaAlteracao, ContaDetalhe, ContaEntrada, InstrumentoEntrada, Leitura } from "@/lib/contas/client";
import { lerValor, mesAtual, valorEditavel } from "@/lib/contas/formato";
import { useAcoesConta, useAcoesRecorrencia, useEnviarPdf, useLerInstrumento, usePdf, useRecorrencia } from "@/lib/contas/hooks";
import { espacosParaCriar } from "@/lib/espaco";
import { ApiError, type Membro } from "@/lib/grupos/client";
import { useGrupo } from "@/lib/grupos/hooks";
import styles from "./conta-folha.module.css";
import instrumentoStyles from "./instrumento.module.css";
import { PdfArquivo } from "./pdf-arquivo";

export const AVISO_VISIBILIDADE = "Quem paga também vê esta conta";

type Pessoa = { id: string; nome: string };
type Modo = "manual" | "codigo" | "chave";
const tipos = { boleto_bancario: "Boleto bancário", boleto_arrecadacao: "Boleto de arrecadação", pix: "Pix", manual: "Conta manual" };

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
  returnFocusTo?: HTMLElement | null;
};

export function ContaFolha({ open, onClose, conta, returnFocusTo }: Props) {
  const router = useRouter();
  const { user, espaco: atual } = useSessao();
  const { criar, editar, cancelar } = useAcoesConta();
  const recorrencias = useAcoesRecorrencia();
  const espacos = espacosParaCriar(user, atual.id); // ajuste 30: current space first and selected
  const [espacoId, setEspacoId] = useState(conta?.espaco.id ?? espacos[0].id);
  const espaco = conta?.espaco ?? espacos.find((e) => e.id === espacoId)!;
  const emGrupo = espaco.tipo === "grupo";
  const grupo = useGrupo(espaco.id, emGrupo);
  const modelo = useRecorrencia(open && conta?.pode_ver_recorrencia ? conta.recorrencia_id ?? undefined : undefined);
  // The editable values belong to this form session; refetches may change the live prop.
  const [base] = useState(() => conta ? {
    descricao: conta.descricao, valor_centavos: conta.valor_centavos, vencimento: conta.vencimento,
    subgrupo: conta.subgrupo?.id ?? null, pagador: conta.pagador?.id ?? null,
    visibilidade: conta.visibilidade, acesso: conta.acesso.map((p) => p.id),
  } : null);

  const [valor, setValor] = useState(conta?.valor_centavos != null ? valorEditavel(conta.valor_centavos) : "");
  const [vencimento, setVencimento] = useState(conta?.vencimento ?? "");
  const [descricao, setDescricao] = useState(conta?.descricao ?? "");
  const [casa, setCasa] = useState<string | null>(conta?.subgrupo?.id ?? null);
  // Q16: "Eu" pre-selected; whoever creates in a group is admin or member, so can pay.
  const [pagador, setPagador] = useState<string | null>(conta ? (conta.pagador?.id ?? null) : user.id);
  const [visibilidade, setVisibilidade] = useState(conta?.visibilidade ?? "grupo");
  const [acesso, setAcesso] = useState<string[]>(conta?.acesso.map((p) => p.id) ?? []);
  const [local, setLocal] = useState<Record<string, string>>({});
  const [repetir, setRepetir] = useState(false);
  const [tipoRecorrencia, setTipoRecorrencia] = useState<"fixo" | "variavel">("fixo");
  const [diaRecorrencia, setDiaRecorrencia] = useState("");
  const [escopo, setEscopo] = useState<"mes" | "proximos">("mes");
  const [confirmarChegada, setConfirmarChegada] = useState(false);
  const escopoEfetivo = modelo.data?.pode_editar ? escopo : "mes";
  const tentativa = useRef<{ assinatura: string; chave: string } | null>(null);
  // A form session owns its initial instrument. Remote refetches do not replace local entry/preview.
  const [inicial] = useState(() => conta?.instrumento && { ...conta.instrumento });
  const [modo, setModo] = useState<Modo>(inicial?.chave_pix ? "chave" : inicial?.codigo ? "codigo" : "manual");
  const [conteudo, setConteudo] = useState(inicial?.codigo ?? inicial?.chave_pix ?? "");
  const [conferencia, setConferencia] = useState<Leitura | null>(null);
  const [instrumentoAlterado, setInstrumentoAlterado] = useState(false);
  const [pdfInicial] = useState(() => conta?.documento_pdf ?? null);
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [pdfId, setPdfId] = useState<string | null | undefined>(undefined);
  const [emissao, setEmissao] = useState(inicial?.data_emissao ?? "");
  const [beneficiario, setBeneficiario] = useState(inicial?.beneficiario ?? "");
  const [metadadosAlterados, setMetadadosAlterados] = useState(false);
  const [pdfErro, setPdfErro] = useState("");
  const [candidato, setCandidato] = useState("");
  const envio = useEnviarPdf();
  const documento = usePdf(pdfId || undefined);
  const processado = useRef("");
  const enviando = useRef(false);
  const leitura = useLerInstrumento();
  const { mutate: ler } = leitura;
  const versaoLeitura = useRef(0);
  const gravacao = useRef(false);
  const sessao = useRef(0);
  useEffect(() => () => { sessao.current++; versaoLeitura.current++; }, []);
  const codigoId = useId();
  const dataId = useId();
  const podeTrocarInstrumento = !conta || conta.status === "pendente" || conta.status === "aguardando";

  useEffect(() => {
    const doc = documento.data;
    if (!doc || processado.current === doc.id || !["lido", "conferencia_manual"].includes(doc.estado)) return;
    processado.current = doc.id;
    let ativo = true;
    // Apply a settled query asynchronously; cleanup discards a superseded result.
    queueMicrotask(() => {
    if (!ativo) { processado.current = ""; return; }
    const resultado = doc.resultado;
    setEmissao(resultado?.data_emissao ?? "");
    setBeneficiario(resultado?.beneficiario ?? "");
    setMetadadosAlterados(true);
    if (resultado?.valor_centavos != null) setValor(valorEditavel(resultado.valor_centavos));
    if (resultado?.vencimento) setVencimento(resultado.vencimento);
    const candidatos = resultado?.candidatos ?? [];
    if (candidatos.length === 1) {
      const codigo = candidatos[0].codigo;
      setCandidato(codigo);
      setModo("codigo");
      setConteudo(codigo);
      setInstrumentoAlterado(true);
      const versao = ++versaoLeitura.current;
      ler({ codigo }, { onSuccess(dados) {
        if (versao !== versaoLeitura.current) return;
        setConferencia(dados);
        if (dados.valor_centavos != null) setValor(valorEditavel(dados.valor_centavos));
        if (dados.vencimento) setVencimento(dados.vencimento);
      } });
    } else {
      setCandidato("");
      setConferencia(null);
      setModo("manual");
      setConteudo("");
      setInstrumentoAlterado(true);
    }
    });
    return () => { ativo = false; };
  }, [documento.data, ler]);

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

  const erro = criar.error ?? editar.error ?? cancelar.error ?? recorrencias.criar.error;
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
  const gravando = criar.isPending || editar.isPending || cancelar.isPending || recorrencias.criar.isPending;
  const lendoPdf = envio.isPending || (!!pdfId && (!documento.data || ["pendente", "lendo"].includes(documento.data.estado)) && !documento.error);
  const ocupado = gravando || leitura.isPending || lendoPdf;
  const aviso = emGrupo && visibilidade === "restrita" && !!pagador && pagador !== user.id;

  function trocarEspaco(id: string) {
    if (gravacao.current || enviando.current || lendoPdf) return;
    setArquivo(null); setPdfId(undefined); setCandidato(""); setPdfErro("");
    setEspacoId(id);
    setCasa(null);
    setPagador(user.id);
    setVisibilidade("grupo");
    setAcesso([]);
  }

  function escolherPdf(novo: File) {
    if (gravacao.current || enviando.current || lendoPdf) return;
    if (novo.size > 5 * 1024 * 1024 || !novo.name.toLowerCase().endsWith(".pdf")) {
      setPdfErro("Escolha um PDF de até 5 MB.");
      return;
    }
    setPdfErro("");
    setArquivo(novo);
    setPdfId(undefined);
    setCandidato("");
    enviando.current = true;
    envio.mutate({ espaco: espaco.id, arquivo: novo, lancamentoId: conta?.id }, {
      onSuccess: (doc) => setPdfId(doc.id),
      onError: () => { setArquivo(null); setPdfErro("Não foi possível enviar o PDF. Tente novamente."); },
      onSettled: () => { enviando.current = false; },
    });
  }

  function escolherCandidato(codigo: string) {
    setCandidato(codigo);
    mudarEntrada("codigo", codigo);
    const versao = ++versaoLeitura.current;
    ler({ codigo }, { onSuccess(dados) {
      if (versao !== versaoLeitura.current) return;
      setConferencia(dados);
      if (dados.valor_centavos != null) setValor(valorEditavel(dados.valor_centavos));
      if (dados.vencimento) setVencimento(dados.vencimento);
    } });
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
    if (gravacao.current || enviando.current || leitura.isPending || lendoPdf) return;
    const centavos = lerValor(valor);
    const faltas: Record<string, string> = {};
    const aguardandoSemConfirmar = conta?.status === "aguardando" && !confirmarChegada;
    if (centavos === null && !(aguardandoSemConfirmar && base?.valor_centavos === null && !valor.trim())) faltas.valor = "Informe um valor maior que zero, como 287,43.";
    if (aguardandoSemConfirmar && centavos !== base?.valor_centavos) faltas.valor = "Confirme a chegada para alterar o valor.";
    if (aguardandoSemConfirmar && (instrumentoAlterado || pdfId)) faltas.instrumento = "Confirme a chegada para salvar os dados conferidos.";
    if (!vencimento) faltas.vencimento = "Informe o vencimento.";
    if (!descricao.trim()) faltas.descricao = "Dê um nome para a conta.";
    if (repetir && vencimento.slice(0, 7) !== mesAtual()) faltas.repeticao = "Para repetir, o vencimento da primeira conta precisa ser deste mês. Você pode salvar sem repetir.";
    if (repetir && (!Number.isInteger(Number(diaRecorrencia)) || Number(diaRecorrencia) < 1 || Number(diaRecorrencia) > 31)) faltas.repeticao = "Informe o dia das próximas contas, de 1 a 31.";
    if (modo !== "manual" && !conferencia) faltas.instrumento = "Confira o código ou a chave antes de salvar.";
    if (pdfId && !["lido", "conferencia_manual"].includes(documento.data?.estado ?? "")) faltas.instrumento = "Escolha um PDF válido antes de salvar.";
    if ((documento.data?.resultado?.candidatos?.length ?? 0) > 0 && (!candidato || modo !== "codigo" || conteudo !== candidato)) faltas.instrumento = "Escolha uma das linhas encontradas no PDF.";
    setLocal(faltas);
    if (Object.keys(faltas).length) return;
    const body: ContaAlteracao = {
      descricao: descricao.trim(),
      ...(centavos !== null ? { valor_centavos: centavos } : {}),
      vencimento,
      ...(emGrupo && { subgrupo: casa, pagador, visibilidade, acesso: visibilidade === "restrita" ? acesso : [] }),
      ...((!conta || instrumentoAlterado) && modo !== "manual" ? { instrumento: modo === "chave" ? { chave_pix: conteudo } : { codigo: conteudo } } : instrumentoAlterado ? { instrumento: null } : {}),
      ...(pdfId !== undefined ? { documento_pdf: pdfId } : {}),
      ...((pdfId || (pdfId === undefined && pdfInicial)) && metadadosAlterados ? { data_emissao: emissao || null, beneficiario: beneficiario.trim() || null } : {}),
    };
    // The synchronous latch also covers repeated submits before React paints the pending state.
    gravacao.current = true;
    const versaoSessao = sessao.current;
    const terminou = () => { gravacao.current = false; };
    if (conta && base) {
      const alteracoes: ContaAlteracao = { ...body };
      if (body.descricao === base.descricao) delete alteracoes.descricao;
      if (body.valor_centavos === base.valor_centavos) delete alteracoes.valor_centavos;
      if (body.vencimento === base.vencimento) delete alteracoes.vencimento;
      if (body.subgrupo === base.subgrupo) delete alteracoes.subgrupo;
      if (body.pagador === base.pagador) delete alteracoes.pagador;
      if (body.visibilidade === base.visibilidade) delete alteracoes.visibilidade;
      const acessoBase = base.visibilidade === "restrita" ? base.acesso : [];
      if (body.acesso && JSON.stringify([...body.acesso].sort()) === JSON.stringify([...acessoBase].sort())) delete alteracoes.acesso;
      return editar.mutate({ id: conta.id, body: { ...alteracoes, ...(conta.recorrente ? { escopo: escopoEfetivo } : {}), ...(conta.status === "aguardando" && confirmarChegada ? { confirmar_chegada: true } : {}) } }, { onSuccess: () => { if (sessao.current === versaoSessao) onClose(); }, onSettled: terminou });
    }
    if (centavos === null) { terminou(); return; }
    const entrada: ContaEntrada = { ...body, descricao: descricao.trim(), valor_centavos: centavos, vencimento };
    if (repetir) {
      const dados = { descricao: entrada.descricao, dia_vencimento: Number(diaRecorrencia), valor_tipo: tipoRecorrencia, valor_centavos: tipoRecorrencia === "fixo" ? centavos : null, subgrupo: entrada.subgrupo, pagador: entrada.pagador, visibilidade: entrada.visibilidade, acesso: entrada.acesso, ocorrencia_inicial: { valor_centavos: centavos, vencimento: entrada.vencimento, instrumento: entrada.instrumento, documento_pdf: entrada.documento_pdf, data_emissao: entrada.data_emissao, beneficiario: entrada.beneficiario } };
      const assinatura = JSON.stringify([espaco.id, dados]);
      if (tentativa.current?.assinatura !== assinatura) tentativa.current = { assinatura, chave: crypto.randomUUID() };
      return recorrencias.criar.mutate({ espaco: espaco.id, body: { ...dados, chave_idempotencia: tentativa.current.chave } }, { onSuccess: (resultado) => { if (sessao.current !== versaoSessao) return; onClose(); if (resultado.ocorrencia) router.push(`/contas/${resultado.ocorrencia.id}?mes=${resultado.ocorrencia.vencimento.slice(0, 7)}`); }, onSettled: terminou });
    }
    criar.mutate(
      { espaco: espaco.id, body: entrada },
      {
        onSuccess(nova) {
          if (sessao.current !== versaoSessao) return;
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
      returnFocusTo={returnFocusTo}
      onClose={() => { if (!gravacao.current && !enviando.current && !lendoPdf) onClose(); }}
      busy={ocupado}
      title={conta ? "Editar conta" : "Nova conta"}
      actions={<Button type="submit" form="conta-form" label={ocupado ? "Salvando…" : conta ? "Salvar" : "Salvar conta"} disabled={ocupado} />}
    >
      <form id="conta-form" className={styles.form} onSubmit={salvar} noValidate>
        <fieldset className={styles.campos} disabled={ocupado}>
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

        {podeTrocarInstrumento && <PdfArquivo key={pdfId ?? (pdfId === null ? "removido" : pdfInicial?.id ?? "novo")} arquivo={arquivo} nome={pdfId === undefined ? pdfInicial?.nome : undefined} tamanho={pdfId === undefined ? pdfInicial?.tamanho : undefined} ocupado={ocupado} documentoId={pdfId === undefined ? pdfInicial?.id : pdfId && ["lido", "conferencia_manual"].includes(documento.data?.estado ?? "") ? pdfId : undefined} onEscolher={escolherPdf} onRemover={() => { setArquivo(null); setPdfId(null); setCandidato(""); setPdfErro(""); }} />}
        {lendoPdf && <p className={styles.nota} role="status">{envio.isPending ? "Enviando PDF…" : "Lendo PDF…"}</p>}
        {(pdfErro || documento.error) && <p className={styles.erro} role="alert">{pdfErro || "Não foi possível consultar o PDF. Tente novamente."}</p>}
        {documento.data && ["invalido", "falhou"].includes(documento.data.estado) && <p className={styles.erro} role="alert">Não foi possível ler este PDF. Escolha outro arquivo.</p>}
        {documento.data?.avisos.map((a, i) => <p key={i} className={styles.nota}>{a}</p>)}
        {(documento.data?.resultado?.candidatos?.length ?? 0) > 1 && <Escolha titulo="Escolha a linha do boleto" erro={erros.instrumento}>
          {documento.data?.resultado?.candidatos?.map((c) => <Chip key={c.codigo} label={c.codigo} wrap state={candidato === c.codigo ? "on" : "off"} onClick={() => escolherCandidato(c.codigo)} />)}
        </Escolha>}
        {(documento.data?.resultado?.candidatos?.length ?? 0) > 1 && <p className={styles.nota}>O arquivo inteiro ficará disponível para quem vê a conta. Escolher uma linha não recorta o PDF.</p>}

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
        {(pdfId || (pdfId === undefined && pdfInicial)) && podeTrocarInstrumento && <div className={styles.g2}>
          <Field label="Emissão" type="date" value={emissao} onChange={(e) => { setEmissao(e.target.value); setMetadadosAlterados(true); }} hint="Do PDF" />
          <Field label="Beneficiário" value={beneficiario} maxLength={200} onChange={(e) => { setBeneficiario(e.target.value); setMetadadosAlterados(true); }} hint="Confira o nome no PDF" />
        </div>}
        <Field label="Descrição" placeholder="Energia · Casa 3" maxLength={150} value={descricao} onChange={(e) => setDescricao(e.target.value)} error={erros.descricao} required />
        {conta?.status === "aguardando" && <label className={styles.confirmacao}><input type="checkbox" checked={confirmarChegada} onChange={(e) => setConfirmarChegada(e.target.checked)} />Confirmar valor e vencimento desta conta</label>}
        {!conta && <RepeticaoCampo repetir={repetir} tipo={tipoRecorrencia} dia={diaRecorrencia} disabled={ocupado} erro={local.repeticao} onRepetir={(v) => { setRepetir(v); if (v && !diaRecorrencia && vencimento) setDiaRecorrencia(String(Number(vencimento.slice(8, 10)))); }} onTipo={setTipoRecorrencia} onDia={setDiaRecorrencia} />}
        {conta?.recorrente && modelo.data?.pode_editar && <EscopoRecorrencia value={escopo} onChange={setEscopo} disabled={ocupado} />}

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
              if (window.confirm(escopoEfetivo === "proximos" && conta.recorrente ? `Cancelar ${conta.descricao} neste mês e nos próximos? As contas abertas serão canceladas e as futuras gerações encerradas.` : `Cancelar ${conta.descricao}? Ela sai das listas e dos totais e fica no histórico.`)) {
                gravacao.current = true;
                cancelar.mutate({ id: conta.id, body: conta.recorrente ? { escopo: escopoEfetivo } : undefined }, { onSuccess: onClose, onSettled: () => { gravacao.current = false; } });
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
