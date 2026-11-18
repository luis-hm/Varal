// Doop: k0kB5dc-Vo / 08 · Marcar como paga (-RwBuRqs8G) + M03 (feyLdQSk81); CU08.
"use client";

import { useId } from "react";
import { Icon } from "@/components/ui/icon";
import styles from "./pagamento.module.css";

type Props = {
  arquivo: File | null;
  ocupado: boolean;
  obrigatorio?: boolean;
  onEscolher: (arquivo: File) => void;
  onRemover: () => void;
};

/** The selected original is uploaded unchanged; validation and authorization belong to the API. */
export function ComprovanteCampo({ arquivo, ocupado, obrigatorio = false, onEscolher, onRemover }: Props) {
  const id = useId();
  const camera = useId();
  const info = useId();
  return (
    <section aria-labelledby={`${id}-titulo`}>
      <p className={styles.rotulo} id={`${id}-titulo`}>Comprovante {!obrigatorio && <span>(opcional)</span>}</p>
      <p id={info} className={styles.aviso}>JPEG, PNG ou PDF de até 5 MB; imagens de até 20 megapixels, sem animação. O arquivo original e seus metadados ficam disponíveis para quem vê a conta.</p>
      <div className={styles.arquivos}>
        <input id={camera} className={styles.inputArquivo} type="file" accept="image/jpeg,image/png" capture="environment" disabled={ocupado} aria-describedby={info} onChange={(e) => {
          const escolhido = e.target.files?.[0];
          e.target.value = "";
          if (escolhido) onEscolher(escolhido);
        }} />
        <label className={styles.upload} data-disabled={ocupado || undefined} htmlFor={camera}><Icon name="camera" /><span className={styles.mobile}>Tirar foto</span><span className={styles.desktop}>Usar a câmera</span></label>
        <input id={id} className={styles.inputArquivo} type="file" accept="image/jpeg,image/png,application/pdf,.jpg,.jpeg,.png,.pdf" disabled={ocupado} aria-describedby={info} onChange={(e) => {
          const escolhido = e.target.files?.[0];
          e.target.value = "";
          if (escolhido) onEscolher(escolhido);
        }} />
        <label className={styles.upload} data-disabled={ocupado || undefined} htmlFor={id} onDragOver={(e) => e.preventDefault()} onDrop={(e) => {
          e.preventDefault();
          if (!ocupado && e.dataTransfer.files[0]) onEscolher(e.dataTransfer.files[0]);
        }}><Icon name="enviar" /><span className={styles.mobile}>Escolher arquivo</span><span className={styles.desktop}>Arraste ou escolha o arquivo</span></label>
      </div>
      {arquivo && <div className={styles.selecionado}><span title={arquivo.name}>{arquivo.name}</span><button type="button" disabled={ocupado} onClick={onRemover}>Remover</button></div>}
      <p className={styles.dica}><Icon name="comprovante" size="sm" />Com o comprovante, a conta fica Confirmada.</p>
    </section>
  );
}
