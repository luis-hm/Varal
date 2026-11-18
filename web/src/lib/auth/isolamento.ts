// Session identity is a fence, never a credential. The server authenticates every request.
let usuario: string | null = null;
let epoca = 0;
let bloqueada = false;
const AUTH_GERACAO = "varal.auth.geracao.v1";
const OAUTH_GERACAO = "varal.auth.oauth.v1";
const pendentes = new Set<AbortController>();

export class SessaoAlterada extends Error {
  constructor() { super("A sessão mudou. Entre novamente para continuar."); }
}
export function iniciarIdentidade(id: string) {
  if (usuario !== id) { epoca++; for (const c of pendentes) c.abort(); pendentes.clear(); }
  usuario = id;
}
export const identidadeAtual = () => usuario;
export function cookie(nome: string) {
  if (typeof document === "undefined") return "";
  const par = document.cookie.split("; ").find((v) => v.startsWith(`${nome}=`));
  return par ? decodeURIComponent(par.slice(nome.length + 1)) : "";
}
/** COR-01: the local fence passes unless this browser logged out or another account signed in. A missing
 * hint (browser restarted while the server session is still valid) is not a reason to hide anything. */
export function marcaValida(id: string) {
  const dono = cookie("varal_owner");
  return !cookie("varal_local_locked") && (!dono || dono === id);
}
export const sessaoBloqueada = () => bloqueada;
export function desbloquearSessao() { bloqueada = false; }
export function bloquearSessao() {
  epoca++; bloqueada = true;
  for (const controller of pendentes) controller.abort();
  pendentes.clear();
  if (typeof document !== "undefined") document.documentElement.setAttribute("data-sessao-oculta", "");
}
export function limparBloqueioLocal() {
  if (typeof document === "undefined") return;
  document.cookie = "varal_local_locked=; Path=/; Max-Age=0; SameSite=Lax";
  document.documentElement.removeAttribute("data-sessao-oculta");
  desbloquearSessao();
}
export function iniciarAutenticacao(oauth = false) {
  const geracao = crypto.randomUUID();
  localStorage.setItem(AUTH_GERACAO, geracao);
  if (oauth) sessionStorage.setItem(OAUTH_GERACAO, geracao);
  return geracao;
}
export function autenticacaoOAuth() { return sessionStorage.getItem(OAUTH_GERACAO); }
export function autenticacaoVigente(geracao: string) { return localStorage.getItem(AUTH_GERACAO) === geracao; }
export function concluirAutenticacao(id: string, geracao: string | null, limparCache: () => void) {
  if (!geracao || !autenticacaoVigente(geracao) || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)) throw new SessaoAlterada();
  // Fence the old identity and clear even a root cache whose private guard unmounted.
  bloquearSessao();
  window.dispatchEvent(new Event("varal-sessao-bloqueada"));
  limparCache();
  document.cookie = `varal_owner=${encodeURIComponent(id)}; Path=/; SameSite=Lax; Max-Age=1209600`;
  iniciarIdentidade(id);
  sessionStorage.removeItem(OAUTH_GERACAO);
  limparBloqueioLocal();
  // A tab opened after the start event must also learn that authentication completed.
  try { localStorage.setItem("varal.sessao.evento", crypto.randomUUID()); } catch { /* broadcast fallback */ }
  try { const channel = new BroadcastChannel("varal-sessao-v1"); channel.postMessage("autenticacao"); channel.close(); } catch { /* storage fallback */ }
}
export function marcarSaidaLocal() {
  bloquearSessao();
  window.dispatchEvent(new Event("varal-sessao-bloqueada"));
  document.cookie = "varal_owner=bloqueada; Path=/; SameSite=Lax";
  document.cookie = "varal_local_locked=1; Path=/; SameSite=Lax";
  try { localStorage.setItem(AUTH_GERACAO, crypto.randomUUID()); localStorage.setItem("varal.sessao.evento", crypto.randomUUID()); } catch { /* other tabs still revalidate on restore */ }
  try { const channel = new BroadcastChannel("varal-sessao-v1"); channel.postMessage("saida"); channel.close(); } catch { /* storage fallback */ }
}
export function inicioRequisicao(sistema = false) {
  if (bloqueada && !sistema) throw new SessaoAlterada();
  const atual = epoca;
  const dono = usuario;
  const controller = new AbortController();
  pendentes.add(controller);
  return {
    dono,
    signal: controller.signal,
    verificar: (response?: Response) => {
      if (atual !== epoca || (bloqueada && !sistema)) throw new SessaoAlterada();
      if (dono && response && response.headers.get("X-Varal-Identidade") !== dono) { marcarSaidaLocal(); throw new SessaoAlterada(); }
    },
    fechar: () => pendentes.delete(controller),
  };
}
