// Doop: k0kB5dc-Vo / 12 · Pedir para alguém pagar (MFZW3LUORq) + M06 (3OQOmTm6BG); CU10, Q10-1–3, Q10-13–14.
"use client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useSessao } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Folha } from "@/components/ui/folha";
import type { ContaDetalhe } from "@/lib/contas/client";
import { dataCivil, valorConta } from "@/lib/contas/formato";
import { ApiError } from "@/lib/grupos/client";
import { abandonarSolicitacao, criarSolicitacao, opcoesSolicitacao, recuperarSolicitacao, type EntradaSolicitacao } from "@/lib/solicitacoes/client";
import { guardarTentativa, removerTentativa, tentativaPendente } from "@/lib/solicitacoes/marcador";
import styles from "./solicitacao.module.css";

function lerMarcador(usuario: string, origem: string) {
  try { return tentativaPendente(usuario, origem); } catch { return null; }
}
export function SolicitacaoAcoes({ conta }: { conta: ContaDetalhe }) {
  const { user } = useSessao();
  const [aberta, setAberta] = useState(false);
  const [chave, setChave] = useState(0);
  const [marcador, setMarcador] = useState<string | null>(null);
  useEffect(() => { const t = window.setTimeout(() => setMarcador(lerMarcador(user.id, conta.id)), 0); return () => window.clearTimeout(t); }, [user.id, conta.id, aberta]);
  if (conta.espaco.tipo !== "pessoal") return null;
  const ativa = conta.solicitacao_ativa;
  if (!conta.pode_solicitar && !ativa && !marcador) return null;
  return <>
    <Button tone="secondary" icon="pedir" label={ativa || marcador ? "Ver pedido" : "Pedir para alguém pagar"} onClick={() => { setChave((v) => v + 1); setAberta(true); }} />
    {aberta && <SolicitacaoFolha key={chave} conta={conta} usuario={user.id} onClose={() => setAberta(false)} />}
  </>;
}
function SolicitacaoFolha({ conta, usuario, onClose }: { conta: ContaDetalhe; usuario: string; onClose: () => void }) {
  const cache = useQueryClient();
  // The summary and the version token are captured together; refetch never rewrites this confirmation.
  const [base] = useState(() => ({ descricao: conta.descricao, valor: conta.valor_centavos, vencimento: conta.vencimento, instrumento: conta.instrumento, pdf: conta.documento_pdf, versao: conta.versao_compartilhamento }));
  const [nonce, setNonce] = useState<string | null>(() => lerMarcador(usuario, conta.id) ?? conta.solicitacao_ativa?.nonce ?? null);
  const [storageErro] = useState(() => { try { tentativaPendente(usuario, conta.id); return false; } catch { return true; } });
  const [grupo, setGrupo] = useState("");
  const [pagador, setPagador] = useState("");
  const [mensagem, setMensagem] = useState("");
  const [confirmado, setConfirmado] = useState(false);
  const [enviado, setEnviado] = useState<EntradaSolicitacao | null>(null);
  const [busy, setBusy] = useState(false);
  const [erro, setErro] = useState("");
  const [revisao, setRevisao] = useState(false);
  const latch = useRef(false);
  const epoch = useRef(0);
  const escolhaInicial = useRef(false);
  useEffect(() => () => { epoch.current++; }, []);
  const opcoes = useQuery({ queryKey: ["solicitacoes", "opcoes", usuario, conta.id], queryFn: () => opcoesSolicitacao(conta.id), enabled: !nonce && conta.pode_solicitar, retry: false });
  const tentativa = useQuery({ queryKey: ["solicitacoes", "tentativa", usuario, conta.id, nonce], queryFn: () => recuperarSolicitacao(conta.id, nonce!), enabled: !!nonce, retry: false, refetchInterval: (q) => q.state.error ? false : q.state.data?.estado === "preparando" ? 1500 : false });
  const grupos = opcoes.isError ? [] : (opcoes.data ?? []);
  const grupoId = grupo;
  const opGrupo = grupos.find((g) => g.id === grupoId);
  const pessoa = opGrupo?.pagadores.find((p) => p.id === pagador);
  const temCodigo = !!(base.instrumento?.codigo || base.instrumento?.chave_pix);
  const estado = tentativa.isError ? undefined : tentativa.data?.estado;
  const terminal = estado === "encerrada" || estado === "falhou";
  const refresh = () => { void cache.invalidateQueries({ queryKey: ["contas"] }); void cache.invalidateQueries({ queryKey: ["grupos"] }); };
  useEffect(() => {
    if (nonce || escolhaInicial.current || !opcoes.isSuccess || opcoes.isError) return;
    let cancelado = false;
    queueMicrotask(() => {
      if (cancelado || escolhaInicial.current) return;
      escolhaInicial.current = true;
      if (opcoes.data.length === 1) setGrupo(opcoes.data[0].id);
    });
    return () => { cancelado = true; };
  }, [nonce, opcoes.isSuccess, opcoes.isError, opcoes.data]);
  useEffect(() => {
    if (nonce || (!opcoes.isSuccess && !opcoes.isError)) return;
    if (!(grupo && !opGrupo) && !(pagador && !pessoa)) return;
    let cancelado = false;
    queueMicrotask(() => { if (!cancelado) { setPagador(""); setConfirmado(false); } });
    return () => { cancelado = true; };
  }, [nonce, opcoes.isSuccess, opcoes.isError, grupo, pagador, opGrupo, pessoa]);
  useEffect(() => {
    if (!estado || estado === "preparando") return;
    void cache.invalidateQueries({ queryKey: ["contas"] });
    void cache.invalidateQueries({ queryKey: ["grupos"] });
  }, [estado, cache]);
  async function enviar() {
    if (latch.current || busy) return;
    if (storageErro) { setErro("Não foi possível recuperar tentativas neste dispositivo."); return; }
    if (!enviado && (!conta.pode_solicitar || !base.versao || conta.versao_compartilhamento !== base.versao)) {
      setConfirmado(false); setRevisao(true); setErro("A cobrança mudou ou não está mais disponível. Feche e revise os dados antes de confirmar novamente."); return;
    }
    if (!enviado && (!grupoId || !pessoa || !confirmado || !base.versao)) { setErro("Escolha o grupo, quem paga e confirme o compartilhamento."); return; }
    let corpo = enviado;
    if (!corpo) {
      try {
        const anterior = tentativaPendente(usuario, conta.id);
        if (anterior) { setNonce(anterior); setErro("Existe uma tentativa anterior para verificar antes de enviar outro pedido."); return; }
      } catch { setErro("Não foi possível recuperar tentativas neste dispositivo."); return; }
      const novo = crypto.randomUUID();
      try { guardarTentativa(usuario, conta.id, novo); } catch { setErro("Não foi possível guardar a tentativa com segurança neste dispositivo."); return; }
      corpo = { nonce: novo, grupo_id: grupoId, pagador_id: pagador, mensagem, confirmar_compartilhamento: true, versao_compartilhamento: base.versao! };
      setEnviado(corpo); setNonce(novo);
    }
    latch.current = true; setBusy(true); setErro(""); const atual = ++epoch.current;
    try {
      const resultado = await criarSolicitacao(conta.id, corpo);
      if (epoch.current !== atual) return;
      cache.setQueryData(["solicitacoes", "tentativa", usuario, conta.id, corpo.nonce], resultado); refresh();
    } catch (error) {
      if (epoch.current !== atual) return;
      setConfirmado(false);
      setErro(error instanceof ApiError && error.status === 409 ? "A cobrança ou o pedido mudou. Encerre esta tentativa e revise os dados." : "Não foi possível confirmar o envio. Tente novamente com os mesmos dados ou encerre esta tentativa.");
    } finally { if (epoch.current === atual) { latch.current = false; setBusy(false); } }
  }
  async function abandonar() {
    if (!nonce || latch.current) return;
    latch.current = true; setBusy(true); setErro(""); const atual = ++epoch.current;
    try {
      await abandonarSolicitacao(conta.id, nonce);
      if (epoch.current !== atual) return;
      removerTentativa(usuario, conta.id, nonce); setNonce(null); setEnviado(null); setConfirmado(false); setRevisao(true); refresh();
      setErro("Tentativa encerrada. Feche e revise os dados para fazer outro pedido.");
    } catch { if (epoch.current === atual) { setErro("Não foi possível encerrar a tentativa. Consulte novamente o estado do pedido."); void tentativa.refetch(); } }
    finally { if (epoch.current === atual) { latch.current = false; setBusy(false); } }
  }
  return <Folha open mobileFull title="Pedir para alguém pagar" onClose={onClose}>
    {nonce ? <div className={styles.conteudo}>
      {tentativa.isLoading && <p role="status">Consultando pedido…</p>}
      {busy && <p>Você pode fechar esta janela. O envio pode continuar em andamento.</p>}
      {estado === "preparando" && <><p role="status">Preparando pedido…</p><p>Você pode fechar esta janela. O pedido continuará sendo preparado.</p></>}
      {estado === "ativa" && <p role="status">Pedido criado.</p>}
      {estado === "quitada" && <p>Este pedido já foi pago.</p>}
      {terminal && <p>{estado === "falhou" ? "Não foi possível preparar o pedido." : "Este pedido foi encerrado."}</p>}
      {tentativa.isError && <p role="alert">Ainda não foi possível confirmar o estado desta tentativa. Um envio anterior ainda pode ser concluído.</p>}
      {erro && <p role="alert">{erro}</p>}
      {enviado && tentativa.isError && <Button label="Tentar novamente" disabled={busy} onClick={enviar} />}
      {(tentativa.isError || tentativa.data?.pode_cancelar) && <Button tone="secondary" label={estado === "preparando" ? "Cancelar preparação" : "Encerrar tentativa"} disabled={busy} onClick={abandonar} />}
      {terminal && <Button tone="secondary" label="Revisar e começar outro pedido" disabled={busy} onClick={() => { try { removerTentativa(usuario, conta.id, nonce); } catch { setErro("Não foi possível limpar a tentativa neste dispositivo."); return; } setNonce(null); setEnviado(null); setRevisao(true); setErro("Feche e revise a cobrança antes de iniciar outro pedido."); refresh(); }} />}
    </div> : <div className={styles.conteudo}>
      <div className={styles.origem}><strong>Pessoal</strong><span aria-hidden="true">→</span><strong>{opGrupo?.nome ?? "Escolha o grupo"}</strong></div>
      <div className={styles.resumo}><strong>{base.descricao}</strong><span>{valorConta(base.valor)} · Vence {dataCivil(base.vencimento)}</span>{temCodigo && <span>O código de pagamento também será compartilhado.</span>}{base.pdf && <span>Com PDF do boleto</span>}</div>
      {opcoes.isLoading && <p role="status">Carregando grupos…</p>}
      {opcoes.isError && <p role="alert">Não foi possível carregar os grupos. <button type="button" onClick={() => opcoes.refetch()}>Tentar novamente</button></p>}
      {opcoes.isSuccess && !grupos.length && <p>Você precisa ser membro ou admin de um grupo para enviar este pedido.</p>}
      {(grupos.length > 1 || (grupos.length > 0 && (!grupo || !opGrupo))) && <label>Grupo<select value={opGrupo ? grupo : ""} onChange={(e) => { setGrupo(e.target.value); setPagador(""); setConfirmado(false); }}><option value="">Escolha um grupo</option>{grupos.map((g) => <option key={g.id} value={g.id}>{g.nome}</option>)}</select></label>}
      {opGrupo && <fieldset><legend>Quem vai pagar</legend>{opGrupo.pagadores.length ? opGrupo.pagadores.map((p) => <Chip key={p.id} label={p.nome} state={p.id === pagador ? "on" : "off"} onClick={() => { setPagador(p.id); setConfirmado(false); }} />) : <p>Nenhuma pessoa elegível para pagar neste grupo.</p>}</fieldset>}
      <label>Mensagem (opcional)<textarea value={mensagem} onChange={(e) => setMensagem(e.target.value)} maxLength={500} /></label>
      {pessoa && <p>{pessoa.id === usuario ? "Esta cópia ficará restrita a você." : `Esta cópia ficará restrita a você e ${pessoa.nome}.`}</p>}
      <p>Descrição, valor, vencimento e mensagem serão compartilhados{temCodigo ? ", junto com o código de pagamento" : ""}.</p>
      {base.instrumento?.beneficiario && <p>Beneficiário: {base.instrumento.beneficiario}</p>}
      {base.instrumento?.data_emissao && <p>Data de emissão: {dataCivil(base.instrumento.data_emissao)}</p>}
      {base.pdf && <p>O PDF inteiro, com todas as páginas e metadados, será compartilhado. Confira se ele contém informações que você quer compartilhar.</p>}
      <label className={styles.check}><input type="checkbox" checked={confirmado} disabled={!pessoa || revisao} onChange={(e) => setConfirmado(e.target.checked)} /> Confirmo o compartilhamento destes dados com as pessoas indicadas.</label>
      {storageErro && <p role="alert">Não foi possível recuperar tentativas neste dispositivo.</p>}
      {erro && <p role="alert">{erro}</p>}
      <Button label="Enviar pedido" icon="enviar" disabled={busy || storageErro || revisao || !pessoa || !grupoId || !confirmado || !conta.pode_solicitar} onClick={enviar} />
    </div>}
  </Folha>;
}
