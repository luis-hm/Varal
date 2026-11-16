// Doop: k0kB5dc-Vo / 13 · Modo simples (mIvLheR2TS) + D05 (YTtAtGSyCI); CU11, Q10-10–12.
"use client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { LogoutButton } from "@/components/auth/logout-button";
import { SairDoGrupo } from "@/components/groups/sair-do-grupo";
import { CopiarCodigo } from "@/components/bills/copiar-codigo";
import { PagamentoAcoes } from "@/components/bills/pagamento-acoes";
import { StatusBadge } from "@/components/bills/status-badge";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { listarModoSimples, verConta, type ContaDetalhe } from "@/lib/contas/client";
import { diaSemana, valorConta } from "@/lib/contas/formato";
import { useLinkPdfConta } from "@/lib/contas/hooks";
import { ApiError } from "@/lib/grupos/client";
import type { components } from "@/types/api";
import { CabecalhoSimples } from "./cabecalho-simples";
import styles from "./simples.module.css";

type Conta = components["schemas"]["ContaSimples"];
function Card({ conta, pagar, busy, pagas }: { conta: Conta; pagar: (conta: Conta) => void; busy: boolean; pagas: boolean }) {
  const pdf = useLinkPdfConta();
  const [erroPdf, setErroPdf] = useState(false);
  const codigo = conta.instrumento?.codigo ?? conta.instrumento?.chave_pix;
  async function abrirPdf() {
    setErroPdf(false);
    try {
      const { url } = await pdf.mutateAsync(conta.id);
      const link = document.createElement("a"); link.href = url; link.target = "_blank"; link.rel = "noopener noreferrer"; link.click();
    } catch { setErroPdf(true); } finally { pdf.reset(); }
  }
  return <article className={styles.card} data-atencao={conta.status_exibido === "vence" || conta.status_exibido === "vencida" || undefined}>
    <StatusBadge status={conta.status_exibido} rotulo={conta.status === "aguardando" ? "Aguardando conferência" : undefined} />
    <h2><Link className={styles.detalhe} href={`/contas/${encodeURIComponent(conta.id)}?origem=simples${pagas ? "&pagas=1" : ""}`}>{conta.descricao}{conta.subgrupo ? ` · ${conta.subgrupo.nome}` : ""}</Link></h2>
    <p className={styles.valor}>{valorConta(conta.valor_centavos)}</p>
    <p>Vencimento <strong>{diaSemana(conta.vencimento)}</strong></p>
    {conta.documento_pdf && <button className={styles.pdf} type="button" onClick={() => { void abrirPdf(); }} disabled={pdf.isPending}><Icon name="baixar" size="md" /> Baixar boleto em PDF</button>}
    {erroPdf && <p role="alert">Não foi possível abrir o PDF. Tente novamente.</p>}
    <div className={styles.acoes}>
      {codigo && <CopiarCodigo codigo={codigo} chave={!!conta.instrumento?.chave_pix} />}
      {conta.pode_pagar && conta.valor_centavos !== null && conta.status === "pendente" && <Button tone="success" icon="pago" label="Já paguei" disabled={busy} onClick={() => pagar(conta)} />}
    </div>
    {!conta.pode_pagar && conta.status === "pendente" && <p>Você pode consultar esta conta.</p>}
  </article>;
}
export function ContasSimples({ grupoId, grupoNome, nome, inicialPagas = false }: { grupoId: string; grupoNome: string; nome: string; inicialPagas?: boolean }) {
  const [pagas, setPagas] = useState(inicialPagas);
  const [selecionada, setSelecionada] = useState<ContaDetalhe | null>(null);
  const [busy, setBusy] = useState(false);
  const [erro, setErro] = useState("");
  const [revogado, setRevogado] = useState(false);
  const trava = useRef(false);
  const epoch = useRef(0);
  const client = useQueryClient();
  const lista = useQuery({ queryKey: ["contas", "simples", grupoId, pagas], queryFn: () => listarModoSimples(grupoId, pagas), retry: false });
  const acessoPerdido = revogado || (lista.error instanceof ApiError && [403, 404].includes(lista.error.status));
  useEffect(() => () => { epoch.current++; }, [grupoId]);
  useEffect(() => {
    if (!acessoPerdido) return;
    epoch.current++;
    client.removeQueries({ queryKey: ["contas"] });
    queueMicrotask(() => { setRevogado(true); setSelecionada(null); });
  }, [acessoPerdido, client]);
  async function pagar(conta: Conta) {
    if (trava.current) return;
    trava.current = true; setBusy(true); setErro("");
    const atual = ++epoch.current;
    try {
      const detalhe = await client.fetchQuery({ queryKey: ["contas", "detalhe", conta.id], queryFn: () => verConta(conta.id), staleTime: 0 });
      if (atual !== epoch.current) return;
      if (!detalhe.pode_pagar || detalhe.valor_centavos === null || detalhe.status !== "pendente") throw new Error("Esta conta não pode mais ser paga. Atualize a lista.");
      setSelecionada(detalhe);
    } catch (error) {
      if (atual === epoch.current) { setErro(error instanceof ApiError && [403, 404].includes(error.status) ? "Esta conta não está mais disponível." : error instanceof Error ? error.message : "Não foi possível abrir a conta."); void client.invalidateQueries({ queryKey: ["contas", "simples", grupoId] }); }
    } finally { if (atual === epoch.current) { trava.current = false; setBusy(false); } }
  }
  return <><CabecalhoSimples nome={nome} grupo={acessoPerdido ? "Grupo indisponível" : grupoNome} sair={<LogoutButton />} /><div className={styles.corpo}>
    {acessoPerdido ? <p role="alert">Este grupo não está mais disponível. Volte para Grupos.</p> : lista.isError ? <p role="alert">Não foi possível carregar as contas. <button type="button" onClick={() => lista.refetch()}>Tentar novamente</button></p> : !lista.data ? <p role="status">Carregando contas…</p> : <>
      <h1>{pagas ? "Contas deste mês já pagas" : lista.data.abertas_qtd ? `Você tem ${lista.data.abertas_qtd} ${lista.data.abertas_qtd === 1 ? "conta em aberto" : "contas em aberto"}.` : "Nenhuma conta em aberto."}</h1>
      {erro && <p role="alert">{erro}</p>}
      {pagas && <button className={styles.pdf} type="button" onClick={() => setPagas(false)}>Voltar às contas em aberto</button>}
      {pagas && !lista.data.itens.length && <p>Nenhuma conta deste mês foi paga.</p>}
      <div className={styles.grade}>{lista.data.itens.map((conta) => <Card key={conta.id} conta={conta} pagar={pagar} busy={busy} pagas={pagas} />)}</div>
      {!pagas && <button className={styles.pagas} type="button" onClick={() => setPagas(true)}><Icon name="comprovante" size="md" /> {lista.data.pagas_mes_qtd} {lista.data.pagas_mes_qtd === 1 ? "conta deste mês já paga" : "contas deste mês já pagas"} <Icon name="chevron" size="md" /></button>}
      <SairDoGrupo grupoId={grupoId} grupoNome={grupoNome} />
    </>}
    {!acessoPerdido && selecionada && <PagamentoAcoes key={selecionada.id} conta={selecionada} modoSimples iniciar aoCancelar={() => setSelecionada(null)} aoConcluir={() => setSelecionada(null)} />}
  </div></>;
}
