// Doop: k0kB5dc-Vo / 07 + D03, 08 + M03, 09 + M04; CU08, RN14–RN16.
"use client";

import { useConfirmar } from "@/components/ui/confirmar";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import type { ContaDetalhe } from "@/lib/contas/client";
import { dataCivil, hoje, nomeMes, reais, valorConta } from "@/lib/contas/formato";
import { useAcoesPagamento, useContas } from "@/lib/contas/hooks";
import { PagamentoFolha } from "./pagamento-folha";
import { PagamentoSucesso } from "./pagamento-sucesso";
import styles from "./pagamento.module.css";

export function PagamentoAcoes({ conta, modoSimples = false, iniciar = false, aoConcluir, aoCancelar, retorno }: { conta: ContaDetalhe; modoSimples?: boolean; iniciar?: boolean; aoConcluir?: () => void; aoCancelar?: () => void; retorno?: string }) {
  const [pedir, confirmacao] = useConfirmar();
  const router = useRouter();
  const acoes = useAcoesPagamento();
  const [modo, setModo] = useState<"marcar" | "anexar" | null>(() => iniciar && conta.pode_pagar ? "marcar" : null);
  const [sucesso, setSucesso] = useState<ContaDetalhe | null>(null);
  const resumo = useContas(sucesso ? conta.espaco.id : undefined, { mes: conta.vencimento.slice(0, 7) });
  const [data, setData] = useState(() => hoje());
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [erro, setErro] = useState("");
  const [estado, setEstado] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const trava = useRef(false);
  const geracao = useRef(0);
  useEffect(() => () => { geracao.current++; }, []);
  const pagamento = conta.pagamento_ativo;

  function abrir(novo: "marcar" | "anexar") {
    if (trava.current) return;
    geracao.current++;
    setData(hoje()); setArquivo(null); setErro(""); setEstado(""); setModo(novo);
  }
  function fechar() {
    if (trava.current) return;
    geracao.current++;
    setModo(null); setArquivo(null); setErro(""); setEstado("");
    if (modoSimples) aoCancelar?.();
  }
  async function salvar() {
    if (trava.current || !modo) return;
    const valorAtual = conta.valor_centavos;
    if (valorAtual === null) { setErro("Defina o valor antes de registrar o pagamento."); return; }
    trava.current = true;
    setOcupado(true); setErro("");
    const atual = ++geracao.current;
    const vigente = () => geracao.current === atual;
    try {
      let documentoId: string | undefined;
      if (arquivo) {
        if (arquivo.size <= 0 || arquivo.size > 5 * 1024 * 1024) throw new Error("Escolha um arquivo de até 5 MiB.");
        setEstado("Enviando comprovante…");
        const documento = await acoes.enviar.mutateAsync({ id: conta.id, arquivo, pagamento: modo === "anexar" ? pagamento?.id : undefined });
        if (!vigente()) return;
        documentoId = documento.id;
        let resultado = documento;
        for (let n = 0; resultado.estado === "pendente" || resultado.estado === "lendo"; n++) {
          if (n >= 60) throw new Error("A validação está demorando. Tente novamente.");
          setEstado("Validando comprovante…");
          await new Promise((resolve) => setTimeout(resolve, 1000));
          if (!vigente()) return;
          resultado = await acoes.consultar.mutateAsync(documentoId);
          if (!vigente()) return;
        }
        if (resultado.estado === "invalido") throw new Error("Formato ou conteúdo do comprovante não aceito. Escolha outro arquivo ou remova-o.");
        if (resultado.estado !== "valido") throw new Error("Não foi possível validar o comprovante. Remova-o ou tente novamente.");
      }
      if (modo === "anexar" && (!pagamento || !documentoId)) throw new Error("Escolha um comprovante.");
      setEstado("Registrando…");
      const resultado = modo === "anexar" && pagamento && documentoId
        ? await acoes.anexar.mutateAsync({ id: conta.id, pagamento: pagamento.id, body: { comprovante_id: documentoId } })
        : await acoes.marcar.mutateAsync({ id: conta.id, body: { pago_em: data, valor_centavos_esperado: valorAtual, ...(documentoId ? { comprovante_id: documentoId } : {}) } });
      if (!vigente()) return;
      setModo(null); setArquivo(null); setEstado("");
      if (modo === "marcar") setSucesso(resultado);
    } catch (e) {
      if (vigente()) setErro(e instanceof Error ? e.message : "Não foi possível concluir. Tente novamente.");
    } finally {
      if (vigente()) { trava.current = false; setOcupado(false); setEstado(""); }
    }
  }
  async function desfazer() {
    if (trava.current || !pagamento || !(await pedir("Desfazer este pagamento? A conta volta a ficar pendente.", "Desfazer pagamento"))) return;
    trava.current = true; setOcupado(true); setErro("");
    const atual = ++geracao.current;
    try { await acoes.desfazer.mutateAsync({ id: conta.id, pagamento: pagamento.id }); }
    catch (e) { if (geracao.current === atual) setErro(e instanceof Error ? e.message : "Não foi possível desfazer."); }
    finally { if (geracao.current === atual) { trava.current = false; setOcupado(false); } }
  }
  async function abrirArquivo(id: string) {
    if (trava.current) return;
    trava.current = true; setOcupado(true); setErro("");
    const atual = ++geracao.current;
    try {
      const { url } = await acoes.abrir.mutateAsync(id);
      if (geracao.current !== atual) return;
      const destino = new URL(url);
      if (!(["http:", "https:"].includes(destino.protocol)) || destino.origin === window.location.origin) throw new Error("Não foi possível abrir o comprovante.");
      const link = document.createElement("a"); link.href = destino.href; link.target = "_blank"; link.rel = "noopener noreferrer"; link.click();
    } catch (e) { if (geracao.current === atual) setErro(e instanceof Error ? e.message : "Não foi possível abrir o comprovante."); }
    finally { acoes.abrir.reset(); if (geracao.current === atual) { trava.current = false; setOcupado(false); } }
  }
  return <>
    {confirmacao}
    {!modoSimples && conta.pagamentos.length > 0 && <section className={styles.historicoPagamentos} aria-label="Pagamentos registrados">
      <h2>Pagamentos registrados</h2>
      <ul>{conta.pagamentos.map((p) => <li key={p.id}>
        <span>{p.desfeito_em ? "Pagamento desfeito" : p.derivado ? "Pagamento derivado de solicitação" : "Pagamento registrado"} · {dataCivil(p.pago_em)} · {reais(p.valor_pago_centavos)} · {p.derivado ? "Sistema" : p.marcado_por}</span>
        {p.comprovante_id && <Button tone="secondary" label="Abrir comprovante" icon="comprovante" disabled={ocupado} onClick={() => abrirArquivo(p.comprovante_id!)} />}
      </li>)}</ul>
    </section>}
    {erro && !modo && <p role="alert" className={styles.erro}>{erro}</p>}
    <div className={styles.acoesConta}>
      {conta.pode_pagar && !iniciar && <Button tone="success" icon="pago" label="Já paguei" disabled={ocupado} onClick={() => abrir("marcar")} />}
      {!modoSimples && conta.pode_anexar_comprovante && <Button tone="secondary" icon="comprovante" label="Anexar comprovante" disabled={ocupado} onClick={() => abrir("anexar")} />}
      {!modoSimples && conta.pode_desfazer_pagamento && <Button tone="ghost" label={ocupado ? "Aguarde…" : "Desfazer pagamento"} disabled={ocupado} onClick={desfazer} />}
    </div>
    <PagamentoFolha open={!!modo} descricao={conta.descricao} valor={valorConta(conta.valor_centavos)} data={data} hoje={hoje()} arquivo={arquivo} ocupado={ocupado} erro={erro} estadoArquivo={estado} anexando={modo === "anexar"} onData={setData} onArquivo={(f) => { setArquivo(f); setErro(""); }} onSubmit={salvar} onClose={fechar} />
    <PagamentoSucesso open={!!sucesso} descricao={conta.descricao} valor={valorConta(conta.valor_centavos)} progresso={resumo.data && !resumo.isFetching && resumo.data.contagens.todas ? `${nomeMes(resumo.data.mes ?? conta.vencimento.slice(0, 7))}: ${resumo.data.contagens.pagas} de ${resumo.data.contagens.todas} contas pagas` : undefined} podeAnexar={!!sucesso?.pode_anexar_comprovante} onAnexar={() => { setSucesso(null); abrir("anexar"); }} rotuloVoltar={modoSimples || retorno ? "Voltar às contas" : undefined} onClose={() => { setSucesso(null); if (modoSimples) aoConcluir?.(); else if (!window.matchMedia?.("(min-width: 1024px)").matches) router.push(retorno ?? "/"); }} />
  </>;
}
