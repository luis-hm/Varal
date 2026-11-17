import type { components } from "@/types/api";
import type { AuthConfig, Authenticated, AuthIssue, Login, RequestPassword, ResetPassword, Signup, Unauthenticated } from "./types";
import { inicioRequisicao, marcarSaidaLocal, SessaoAlterada } from "./isolamento";

const BASE = "/api/auth/browser/v1/";

export class AuthError extends Error {
  constructor(public readonly status: number, public readonly issues: AuthIssue[] = [], public readonly autenticada?: boolean, public readonly flows: components["schemas"]["AllauthFlow"][] = []) {
    super(issues[0]?.message ?? "Não foi possível concluir. Tente novamente.");
  }
}

export function csrfToken() {
  return document.cookie.split("; ").find((cookie) => cookie.startsWith("csrftoken="))?.slice("csrftoken=".length) ?? "";
}

function isUnauthenticated(value: unknown): value is Unauthenticated {
  if (!value || typeof value !== "object") return false;
  const body = value as Partial<Unauthenticated>;
  return body.status === 401 && body.meta?.is_authenticated === false && Array.isArray(body.data?.flows);
}

async function request<T>(path: string, init?: RequestInit, acceptsLogout = false, identidadeEsperada?: string, aoDivergir?: () => void): Promise<T> {
  const response = await fetch(`${BASE}${path}`, { credentials: "same-origin", cache: "no-store", ...init });
  const body: unknown = await response.json().catch(() => null);
  const auth = body && typeof body === "object" && "meta" in body && body.meta && typeof body.meta === "object" && "is_authenticated" in body.meta && typeof body.meta.is_authenticated === "boolean" ? body.meta.is_authenticated : undefined;
  const flows = body && typeof body === "object" && "data" in body && body.data && typeof body.data === "object" && "flows" in body.data && Array.isArray(body.data.flows) ? body.data.flows as components["schemas"]["AllauthFlow"][] : [];
  if (identidadeEsperada && response.headers.get("X-Varal-Identidade") !== identidadeEsperada && !(response.status === 401 && isUnauthenticated(body))) { aoDivergir?.(); throw new AuthError(response.status); }
  if (!response.ok && !(acceptsLogout && response.status === 401 && isUnauthenticated(body))) {
    const errors = body && typeof body === "object" && "errors" in body ? (body as components["schemas"]["AllauthErrorResponse"]).errors : undefined;
    throw new AuthError(response.status, Array.isArray(errors) ? errors : [], auth, flows);
  }
  return body as T;
}

export function getAuthConfig() {
  return request<AuthConfig>("config");
}

async function mutate<T>(path: string, body: Login | Signup | RequestPassword | ResetPassword | components["schemas"]["AllauthVerifyEmail"] | undefined, method = "POST", acceptsLogout = false, identidadeEsperada?: string) {
  // Django rotates CSRF at login: always read the current cookie, never cache the token.
  if (!csrfToken()) await getAuthConfig();
  const token = csrfToken();
  if (!token) throw new AuthError(403, [{ code: "csrf", message: "Atualize a página e tente novamente." }]);
  return request<T>(path, {
    method,
    headers: { "Content-Type": "application/json", "X-CSRFToken": token, ...(identidadeEsperada ? { "X-Varal-Identidade-Esperada": identidadeEsperada } : {}) },
    ...(body ? { body: JSON.stringify(body) } : {}),
  }, acceptsLogout, identidadeEsperada);
}

export const login = (body: Login) => mutate<Authenticated>("auth/login", body);
export const signup = (body: Signup) => mutate<Authenticated>("auth/signup", body);
export const requestPassword = (body: RequestPassword) => mutate<components["responses"]["AllauthStatusOK"]["content"]["application/json"]>("auth/password/request", body);
export const resetPassword = (body: ResetPassword) => mutate<Authenticated | Unauthenticated>("auth/password/reset", body, "POST", true);
export const logout = (identidadeEsperada: string) => mutate<Unauthenticated>("auth/session", undefined, "DELETE", true, identidadeEsperada);

export function validateResetKey(key: string) {
  return request<components["responses"]["AllauthPasswordResetInfo"]["content"]["application/json"]>("auth/password/reset", {
    headers: { "X-Password-Reset-Key": key },
  });
}

export function getSession() {
  return request<Authenticated | Unauthenticated>("auth/session", undefined, true);
}

export function verificarChaveEmail(key: string) {
  return request<components["schemas"]["AllauthEmailVerificationInfo"]>("auth/email/verify", { headers: { "X-Email-Verification-Key": key } });
}
export const confirmarEmail = (key: string) => mutate<Authenticated | Unauthenticated>("auth/email/verify", { key }, "POST", true);

async function autenticada<T>(path: string, method: "GET" | "POST" | "PUT", body?: unknown): Promise<T> {
  const contexto = inicioRequisicao();
  try {
    if (!contexto.dono) throw new SessaoAlterada();
    if (method !== "GET" && !csrfToken()) await getAuthConfig();
    contexto.verificar();
    const headers: Record<string, string> = { "X-Varal-Identidade-Esperada": contexto.dono };
    if (method !== "GET") { headers["X-CSRFToken"] = csrfToken(); headers["Content-Type"] = "application/json"; }
    const result = await request<T>(path, { method, headers, signal: contexto.signal, ...(body === undefined ? {} : { body: JSON.stringify(body) }) }, false, contexto.dono, () => { contexto.verificar(); marcarSaidaLocal(); });
    contexto.verificar();
    return result;
  } finally { contexto.fechar(); }
}
export const reautenticarSenha = (body: components["schemas"]["AllauthReauthenticate"]) => autenticada<Authenticated>("auth/reauthenticate", "POST", body);
export const sessaoAtual = () => autenticada<Authenticated>("auth/session", "GET");
export const solicitarCodigoReauth = (body: components["schemas"]["AllauthRequestReauthenticationCode"]) => autenticada<components["responses"]["AllauthStatusOK"]["content"]["application/json"]>("auth/reauthenticate/code/request", "POST", body);
export const confirmarCodigoReauth = (body: components["schemas"]["AllauthConfirmLoginCode"]) => autenticada<Authenticated>("auth/reauthenticate/code/confirm", "POST", body);
export const emailsProprios = () => autenticada<components["responses"]["AllauthEmailAddresses"]["content"]["application/json"]>("account/email", "GET");
export const solicitarVerificacaoEmail = (email: string) => autenticada<components["responses"]["AllauthStatusOK"]["content"]["application/json"]>("account/email", "PUT", { email } satisfies components["requestBodies"]["AllauthEmail"]["content"]["application/json"]);
