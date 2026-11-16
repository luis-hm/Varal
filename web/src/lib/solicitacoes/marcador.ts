// T10-E: only opaque identifiers survive reload; confirmed financial content stays in memory.
const PREFIXO = "varal.solicitacao.v1.";
function prefixo(usuario: string, origem: string) {
  return `${PREFIXO}${encodeURIComponent(usuario)}.${encodeURIComponent(origem)}.`;
}

/** Returns the nonce to reconcile; an unreadable store must not silently start a new attempt. */
export function tentativaPendente(usuario: string, origem: string): string | null {
  const prefix = prefixo(usuario, origem);
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key?.startsWith(prefix)) return key.slice(prefix.length);
  }
  return null;
}
export function guardarTentativa(usuario: string, origem: string, nonce: string): void {
  localStorage.setItem(`${prefixo(usuario, origem)}${nonce}`, "1");
}
/** Call only after the server confirms the matching attempt is terminal or abandoned. */
export function removerTentativa(usuario: string, origem: string, nonce: string): void {
  localStorage.removeItem(`${prefixo(usuario, origem)}${nonce}`);
}
