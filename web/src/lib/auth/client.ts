import type { components } from "@/types/api";
import type { AuthConfig, Authenticated, AuthIssue, Login, RequestPassword, ResetPassword, Signup, Unauthenticated } from "./types";

const BASE = "/api/auth/browser/v1/";

export class AuthError extends Error {
  constructor(public readonly status: number, public readonly issues: AuthIssue[] = []) {
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

async function request<T>(path: string, init?: RequestInit, acceptsLogout = false): Promise<T> {
  const response = await fetch(`${BASE}${path}`, { credentials: "same-origin", cache: "no-store", ...init });
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok && !(acceptsLogout && response.status === 401 && isUnauthenticated(body))) {
    const errors = body && typeof body === "object" && "errors" in body ? (body as components["schemas"]["AllauthErrorResponse"]).errors : undefined;
    throw new AuthError(response.status, Array.isArray(errors) ? errors : []);
  }
  return body as T;
}

export function getAuthConfig() {
  return request<AuthConfig>("config");
}

async function mutate<T>(path: string, body: Login | Signup | RequestPassword | ResetPassword | undefined, method = "POST", acceptsLogout = false) {
  // Django rotates CSRF at login: always read the current cookie, never cache the token.
  if (!csrfToken()) await getAuthConfig();
  const token = csrfToken();
  if (!token) throw new AuthError(403, [{ code: "csrf", message: "Atualize a página e tente novamente." }]);
  return request<T>(path, {
    method,
    headers: { "Content-Type": "application/json", "X-CSRFToken": token },
    ...(body ? { body: JSON.stringify(body) } : {}),
  }, acceptsLogout);
}

export const login = (body: Login) => mutate<Authenticated>("auth/login", body);
export const signup = (body: Signup) => mutate<Authenticated>("auth/signup", body);
export const requestPassword = (body: RequestPassword) => mutate<components["responses"]["AllauthStatusOK"]["content"]["application/json"]>("auth/password/request", body);
export const resetPassword = (body: ResetPassword) => mutate<Authenticated | Unauthenticated>("auth/password/reset", body, "POST", true);
export const logout = () => mutate<Unauthenticated>("auth/session", undefined, "DELETE", true);

export function validateResetKey(key: string) {
  return request<components["responses"]["AllauthPasswordResetInfo"]["content"]["application/json"]>("auth/password/reset", {
    headers: { "X-Password-Reset-Key": key },
  });
}

export function getSession() {
  return request<Authenticated | Unauthenticated>("auth/session", undefined, true);
}
