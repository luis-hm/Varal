// Doop: k0kB5dc-Vo / 05 + M01 (envio), 06 + M02 (arquivo e prévia).
"use client";

import { useId, useState } from "react";
import { Icon } from "@/components/ui/icon";
import { useLinkPdf } from "@/lib/contas/hooks";
import styles from "./pdf-arquivo.module.css";

type Props = {
  arquivo: File | null;
  nome?: string;
  tamanho?: number;
  ocupado: boolean;
  documentoId?: string;
  onEscolher: (arquivo: File) => void;
  onRemover?: () => void;
};

export function PdfArquivo({ arquivo, nome, tamanho, ocupado, documentoId, onEscolher, onRemover }: Props) {
  const id = useId();
  const previa = useLinkPdf();
  const [url, setUrl] = useState<string>();
  const [erroUrl, setErroUrl] = useState(false);
  function abrir(novaAba: boolean) {
    if (!documentoId) return;
    setErroUrl(false);
    previa.mutate(documentoId, { onSuccess: ({ url: assinada }) => {
      let destino: URL;
      try { destino = new URL(assinada); } catch { setErroUrl(true); return; }
      if (!['http:', 'https:'].includes(destino.protocol) || destino.origin === window.location.origin) { setErroUrl(true); return; }
      if (novaAba) {
        const link = document.createElement("a");
        link.href = assinada;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.click();
      } else setUrl(assinada);
    } });
  }
  const temArquivo = !!nome || !!arquivo;
  return (
    <section className={styles.pdf} aria-label="PDF do boleto">
      <input id={id} className={styles.input} type="file" accept=".pdf,application/pdf" disabled={ocupado} onChange={(e) => {
        const escolhido = e.target.files?.[0];
        e.target.value = "";
        if (escolhido) onEscolher(escolhido);
      }} />
      {temArquivo ? (
        <>
          <div className={styles.arquivo}>
            <span className={styles.icone}><Icon name="pdf" size="md" />PDF</span>
            <span className={styles.nome}><b title={nome ?? arquivo?.name}>{nome ?? arquivo?.name}</b><small>{Math.ceil((tamanho ?? arquivo?.size ?? 0) / 1024)} KB</small></span>
            {!ocupado && <label className={styles.acao} htmlFor={id}>Trocar</label>}
            {!ocupado && onRemover && <button className={styles.acao} type="button" onClick={onRemover}>Remover</button>}
          </div>
          {documentoId && <div className={styles.previa}>
            <span>Confira o arquivo original.</span>
            <button className={styles.acao} type="button" disabled={previa.isPending || ocupado} onClick={() => abrir(false)}>{previa.isPending ? "Abrindo…" : "Carregar prévia"}</button>
            <button className={styles.acao} type="button" disabled={previa.isPending || ocupado} onClick={() => abrir(true)}>Abrir PDF em outra aba</button>
            {url && <iframe className={styles.visualizador} title="Prévia do PDF" src={url} />}
            {(previa.error || erroUrl) && <span role="alert">Não foi possível abrir a prévia. Tente novamente.</span>}
          </div>}
        </>
      ) : (
        <label className={styles.escolher} htmlFor={id} onDragOver={(e) => e.preventDefault()} onDrop={(e) => {
          e.preventDefault();
          if (!ocupado && e.dataTransfer.files[0]) onEscolher(e.dataTransfer.files[0]);
        }}>
          <span className={styles.enviar}><Icon name="enviar" /></span>
          <b>Enviar PDF do boleto</b>
          <span>Escolha ou arraste o arquivo. A gente lê o código, o valor, a emissão e o vencimento. PDF de até 5 MB.</span>
        </label>
      )}
    </section>
  );
}
