import type { components } from "@/types/api";
import { csrfToken, getAuthConfig } from "@/lib/auth/client";

type S = components["schemas"];
export type Papel = S["PapelEnum"];
export type GrupoLista = S["GrupoLista"];
export type GrupoDetalhe = S["GrupoDetalhe"];
export type Membro = S["Membro"];
export type Casa = S["Casa"];
export type ConviteCriado = S["ConviteCriado"];
export type ConvitePendente = S["ConvitePendente"];
export type ConvitePublico = S["ConvitePublico"];
export type Aceite = S["Aceite"];

const fallback: Record<number, string> = {
  403: "Seu papel não permite esta ação.",
  404: "Este grupo não existe ou você não participa dele.",
  // RN24/RN31: one message for expired, used, revoked or unknown links.
  410: "Este convite não vale mais. Peça um novo a quem convidou.",
  429: "Muitas tentativas em pouco tempo. Espere um pouco e tente de novo.",
};

export class ApiError extends Error {
  constructor(public readonly status: number, detail?: string) {
    // Only 409 carries a rule message written for people (RN04 and similar, in pt-BR).
    super((status === 409 && detail) || fallback[status] || "Não foi possível concluir. Tente novamente.");
  }
}

async function call<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const headers: Record<string, string> = {};
  if (method !== "GET") {
    if (!csrfToken()) await getAuthConfig();
    headers["X-CSRFToken"] = csrfToken();
  }
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const response = await fetch(`/api/${path}`, {
    method,
    headers,
    credentials: "same-origin",
    cache: "no-store",
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
  const data: unknown = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data && typeof data === "object" && "detail" in data ? String((data as S["Erro"]).detail) : undefined;
    throw new ApiError(response.status, detail);
  }
  return data as T;
}

const g = (id: string, rest = "") => `grupos/${encodeURIComponent(id)}/${rest}`;
const t = (token: string, rest = "") => `convites/${encodeURIComponent(token)}/${rest}`;

export const listarGrupos = () => call<GrupoLista[]>("grupos/");
export const criarGrupo = (body: S["CriarGrupo"]) => call<GrupoDetalhe>("grupos/", "POST", body);
export const verGrupo = (id: string) => call<GrupoDetalhe>(g(id));
export const sairDoGrupo = (id: string) => call<null>(g(id, "sair/"), "POST");
export const listarConvites = (id: string) => call<ConvitePendente[]>(g(id, "convites/"));
export const criarConvite = (id: string, papel: Papel) => call<ConviteCriado>(g(id, "convites/"), "POST", { papel } satisfies S["Papel"]);
export const revogarConvite = (id: string, conviteId: string) => call<null>(g(id, `convites/${conviteId}/`), "DELETE");
export const alterarPapel = (id: string, membroId: string, papel: Papel) =>
  call<Membro>(g(id, `membros/${membroId}/`), "PATCH", { papel } satisfies S["PatchedPapel"]);
export const removerMembro = (id: string, membroId: string) => call<null>(g(id, `membros/${membroId}/`), "DELETE");
export const criarCasa = (id: string, nome: string) => call<Casa>(g(id, "subgrupos/"), "POST", { nome } satisfies Omit<Casa, "id">);
export const alterarCasa = (id: string, casaId: string, body: S["PatchedCasa"]) => call<Casa>(g(id, `subgrupos/${casaId}/`), "PATCH", body);
export const verConvite = (token: string) => call<ConvitePublico>(t(token));
export const aceitarConvite = (token: string) => call<Aceite>(t(token, "aceitar/"), "POST");
