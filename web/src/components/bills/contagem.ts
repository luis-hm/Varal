"use client";

import { useEffect, useState } from "react";

export const movimentoReduzido = () =>
  typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;

/** count-up (guide varal-ui): 0 → value in 1.2s, cubic ease-out, requestAnimationFrame; off with reduced motion. */
export function useContagem(alvo: number) {
  const [valor, setValor] = useState(() => (movimentoReduzido() ? alvo : 0));
  useEffect(() => {
    const duracao = movimentoReduzido() ? 0 : 1200; // reduced motion: straight to the value on the next frame
    let inicio: number | undefined;
    let id = 0;
    const passo = (t: number) => {
      inicio ??= t;
      const p = duracao ? Math.min((t - inicio) / duracao, 1) : 1;
      setValor(Math.round(alvo * (1 - (1 - p) ** 3)));
      if (p < 1) id = requestAnimationFrame(passo);
    };
    id = requestAnimationFrame(passo);
    return () => cancelAnimationFrame(id);
  }, [alvo]);
  return valor;
}
