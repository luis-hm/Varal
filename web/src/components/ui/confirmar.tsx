"use client";
// Replaces window.confirm with the app's own sheet/modal (Folha adds the ghost "Cancelar"): focus trap, Esc closes.
import { useState, type ReactNode } from "react";
import { Button } from "./button";
import { Folha } from "./folha";

type Pedido = { texto: string; acao: string; origem: HTMLElement | null; resolver: (ok: boolean) => void };

/** `const [confirmar, confirmacao] = useConfirmar();` then `if (!(await confirmar(texto, "Remover"))) return;`
 * and render `{confirmacao}`. The title is the question; the button repeats the action. */
export function useConfirmar(): [(texto: string, acao: string) => Promise<boolean>, ReactNode] {
  const [pedido, setPedido] = useState<Pedido | null>(null);
  const confirmar = (texto: string, acao: string) => new Promise<boolean>((resolver) => {
    const origem = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setPedido({ texto, acao, origem, resolver });
  });
  const fechar = (ok: boolean) => { pedido?.resolver(ok); setPedido(null); };
  const [pergunta, ...resto] = pedido ? pedido.texto.split(/(?<=\?) /) : [""];
  const elemento = <Folha open={!!pedido} onClose={() => fechar(false)} title={pergunta} returnFocusTo={pedido?.origem}
    actions={<Button tone="danger" label={pedido?.acao ?? ""} onClick={() => fechar(true)} />}>
    {resto.length > 0 && <p>{resto.join(" ")}</p>}
  </Folha>;
  return [confirmar, elemento];
}
