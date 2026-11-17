import type { components } from "@/types/api";
import { csrfToken, getAuthConfig } from "@/lib/auth/client";
import { inicioRequisicao } from "@/lib/auth/isolamento";

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
export type Resolucao = S["Resolucao"];
export type ContaRestritaOrfa = S["ContaRestritaOrfa"];

const fallback: Record<number, string> = {
  403: "Seu papel não permite esta ação.",
  404: "Este grupo não existe ou você não participa dele.",
  // RN24/RN31: one message for expired, used, revoked or unknown links.
  410: "Este convite não vale mais. Peça um novo a quem convidou.",
  429: "Muitas tentativas em pouco tempo. Espere um pouco e tente de novo.",
};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    detail?: string,
    /** Raw JSON body: field errors of a 400, the RN32 payload of a 409. */
    public readonly data?: unknown,
  ) {
    // 400 and 409 carry rule messages written for people (RN04, RN11, RN32…, in pt-BR).
    super(((status === 400 || status === 409) && detail) || fallback[status] || "Não foi possível concluir. Tente novamente.");
  }

  /** DRF field errors of a 400 as {campo: primeira mensagem}. */
  get campos(): Record<string, string> {
    if (this.status !== 400 || !this.data || typeof this.data !== "object") return {};
    return Object.fromEntries(
      Object.entries(this.data).map(([campo, v]) => [campo, String(Array.isArray(v) ? v[0] : v)]),
    );
  }
}

export async function call<T>(path: string, method = "GET", body?: unknown, sistema = false): Promise<T> {
  const contexto = inicioRequisicao(sistema);
  try {
  const headers: Record<string, string> = {};
  if (contexto.dono) headers["X-Varal-Identidade-Esperada"] = contexto.dono;
  if (method !== "GET") {
    if (!csrfToken()) await getAuthConfig();
    headers["X-CSRFToken"] = csrfToken();
  }
  contexto.verificar();
  if (body !== undefined && !(body instanceof FormData)) headers["Content-Type"] = "application/json";
  const response = await fetch(`/api/${path}`, {
    method,
    headers,
    credentials: "same-origin",
    cache: "no-store",
    signal: contexto.signal,
    ...(body !== undefined ? { body: body instanceof FormData ? body : JSON.stringify(body) } : {}),
  });
  contexto.verificar(response);
  const data: unknown = response.status === 204 ? null : await response.json().catch(() => null);
  contexto.verificar(response);
  if (!response.ok) {
    const detail =
      data && typeof data === "object"
        ? "detail" in data
          ? String((data as S["Erro"]).detail)
          : String(Object.values(data).flat()[0] ?? "") || undefined
        : undefined;
    throw new ApiError(response.status, detail, data);
  }
  return data as T;
  } finally { contexto.fechar(); }
}

const g = (id: string, rest = "") => `grupos/${encodeURIComponent(id)}/${rest}`;
const t = (token: string, rest = "") => `convites/${encodeURIComponent(token)}/${rest}`;

export const listarGrupos = () => call<GrupoLista[]>("grupos/");
export const criarGrupo = (body: S["CriarGrupo"]) => call<GrupoDetalhe>("grupos/", "POST", body);
export const verGrupo = (id: string) => call<GrupoDetalhe>(g(id));
export const sairDoGrupo = (id: string, resolucoes?: S["Resolucao"][]) =>
  call<null>(g(id, "sair/"), "POST", resolucoes ? ({ resolucoes } satisfies S["Sair"]) : undefined);
export const configurarGrupo = (id: string, janela_alerta_dias: number) =>
  call<GrupoDetalhe>(g(id), "PATCH", { janela_alerta_dias } satisfies S["PatchedConfiguracoes"]);
export const listarConvites = (id: string) => call<ConvitePendente[]>(g(id, "convites/"));
export const criarConvite = (id: string, papel: Papel) => call<ConviteCriado>(g(id, "convites/"), "POST", { papel } satisfies S["Papel"]);
export const revogarConvite = (id: string, conviteId: string) => call<null>(g(id, `convites/${conviteId}/`), "DELETE");
export const alterarPapel = (id: string, membroId: string, papel: Papel) =>
  call<Membro>(g(id, `membros/${membroId}/`), "PATCH", { papel } satisfies S["PatchedPapel"]);
export const removerMembro = (id: string, membroId: string) => call<null>(g(id, `membros/${membroId}/`), "DELETE");
export const criarCasa = (id: string, nome: string) => call<Casa>(g(id, "subgrupos/"), "POST", { nome } satisfies Omit<Casa, "id">);
export const alterarCasa = (id: string, casaId: string, body: S["PatchedCasaAlterar"]) => call<Casa>(g(id, `subgrupos/${casaId}/`), "PATCH", body);
export const previewArquivamento = (id: string, casaId: string) => call<S["ArquivamentoPreview"]>(g(id, `subgrupos/${casaId}/arquivamento/`));
export const verConvite = (token: string) => call<ConvitePublico>(t(token));
export const aceitarConvite = (token: string) => call<Aceite>(t(token, "aceitar/"), "POST");
