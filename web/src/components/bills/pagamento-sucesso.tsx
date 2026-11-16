// Doop: k0kB5dc-Vo / 09 · Conta paga (y1NUSjOnMM) + M04 (CB5AeHekwg); CU08.
"use client";

import { useEffect, useId, useRef } from "react";
import { Icon } from "@/components/ui/icon";
import styles from "./pagamento-sucesso.module.css";

type Props = {
  open: boolean;
  descricao: string;
  valor: string;
  progresso?: string;
  podeAnexar: boolean;
  onAnexar: () => void;
  onClose: () => void;
};

export function PagamentoSucesso({ open, descricao, valor, progresso, podeAnexar, onAnexar, onClose }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const opener = useRef<HTMLElement | null>(null);
  const titulo = useId();
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      opener.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
    } else if (!open && dialog.open) {
      if (typeof dialog.close === "function") dialog.close();
      else dialog.removeAttribute("open");
      opener.current?.focus();
    }
  }, [open]);
  return <dialog ref={ref} className={styles.dialog} aria-labelledby={titulo} onCancel={(e) => { e.preventDefault(); onClose(); }}>
    {open && <div className={styles.conteudo}>
      <div className={styles.varal} aria-hidden="true">
        <svg viewBox="0 0 480 44" preserveAspectRatio="none"><path d="M-6 8 Q240 44 486 8" /></svg>
        <span className={styles.vermelha} /><span className={styles.vazio} /><span className={styles.saindo} /><span className={styles.verde} />
      </div>
      <div className={styles.check} aria-hidden="true"><svg viewBox="0 0 64 64"><path d="M16 33l11 11 22-24" /></svg></div>
      <h2 id={titulo}>Pagamento registrado.</h2>
      <p>{descricao} · {valor}</p>
      {progresso && <p className={styles.progresso}>{progresso}</p>}
      <div className={styles.acoes}>
        {podeAnexar && <button type="button" className={styles.anexar} onClick={onAnexar}><Icon name="camera" size="md" />Anexar comprovante</button>}
        <button type="button" className={styles.fechar} onClick={onClose}><span className={styles.mobile}>Voltar ao início</span><span className={styles.desktop}>Fechar</span></button>
      </div>
    </div>}
  </dialog>;
}
