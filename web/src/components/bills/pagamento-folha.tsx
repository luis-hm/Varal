// Doop: k0kB5dc-Vo / 08 · Marcar como paga (-RwBuRqs8G) + M03 (feyLdQSk81); CU08.
"use client";

import { useId, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Folha } from "@/components/ui/folha";
import { ComprovanteCampo } from "./comprovante-campo";
import styles from "./pagamento.module.css";

type Props = {
  open: boolean;
  descricao: string;
  valor: string;
  data: string;
  hoje: string;
  arquivo: File | null;
  ocupado: boolean;
  erro?: string;
  estadoArquivo?: string;
  anexando?: boolean;
  onData: (data: string) => void;
  onArquivo: (arquivo: File | null) => void;
  onSubmit: () => void;
  onClose: () => void;
};

export function PagamentoFolha({ open, descricao, valor, data, hoje, arquivo, ocupado, erro, estadoArquivo, anexando = false, onData, onArquivo, onSubmit, onClose }: Props) {
  const formId = useId();
  function enviar(event: FormEvent) { event.preventDefault(); if (!ocupado) onSubmit(); }
  return <Folha open={open} title={anexando ? "Anexar comprovante" : "Marcar como paga"} subtitle={`${descricao} · ${valor}`} onClose={onClose} busy={ocupado}
    actions={<Button tone="success" icon="pago" type="submit" form={formId} label={ocupado ? "Salvando…" : anexando ? "Anexar comprovante" : "Confirmar pagamento"} disabled={ocupado || (anexando && !arquivo)} />}>
    <form id={formId} onSubmit={enviar} className={styles.formulario}>
      {!anexando && <Field label="Data do pagamento" type="date" value={data} max={hoje} onChange={(e) => onData(e.target.value)} disabled={ocupado} required />}
      <ComprovanteCampo arquivo={arquivo} ocupado={ocupado} obrigatorio={anexando} onEscolher={onArquivo} onRemover={() => onArquivo(null)} />
      {estadoArquivo && <p role="status" className={styles.dica}>{estadoArquivo}</p>}
      {erro && <p role="alert" className={styles.erro}>{erro}</p>}
      <p className={styles.dica}>O pagamento é feito no aplicativo do banco. Aqui você registra que pagou.</p>
    </form>
    <button type="button" className={styles.cancelarMobile} disabled={ocupado} onClick={onClose}>Cancelar</button>
  </Folha>;
}
