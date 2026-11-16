// Doop: k0kB5dc-Vo / 07 · Detalhe (efJzW9e5vx) + D03 · Contas + Detalhe (cWdVUX2y8H).
// RF14/CU08: the exact authorized payment code, never a rebuilt BR Code.
"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import styles from "./instrumento.module.css";

export function CopiarCodigo({ codigo, chave = false }: { codigo: string; chave?: boolean }) {
  const [estado, setEstado] = useState<"inicial" | "copiando" | "copiado" | "manual">("inicial");
  const campo = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (estado !== "manual") return;
    campo.current?.focus();
    campo.current?.select();
  }, [estado]);

  async function copiar() {
    setEstado("copiando");
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(codigo);
      setEstado("copiado");
    } catch {
      setEstado("manual");
      campo.current?.focus();
      campo.current?.select();
    }
  }

  return (
    <div className={styles.copia}>
      <Button tone="ghost" width="full" icon="copiar" label={chave ? "Copiar chave Pix" : "Copiar código"} onClick={copiar} disabled={estado === "copiando"} />
      <p className={styles.nota} role="status" aria-live="polite">
        {estado === "copiado" ? (chave ? "Chave Pix copiada." : "Código copiado.") : estado === "manual" ? "Selecione e copie o código abaixo." : ""}
      </p>
      {estado === "manual" && (
        <textarea ref={campo} className={styles.entrada} aria-label={chave ? "Chave Pix para copiar manualmente" : "Código para copiar manualmente"} value={codigo} readOnly rows={3} onFocus={(e) => e.currentTarget.select()} />
      )}
    </div>
  );
}
