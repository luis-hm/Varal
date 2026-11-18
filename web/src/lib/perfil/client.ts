import type { components } from "@/types/api";
import { inicioRequisicao } from "@/lib/auth/isolamento";
import { ApiError, call } from "@/lib/grupos/client";

type S = components["schemas"];
export type Exportacao = S["Exportacao"];
export const solicitarExportacao = (body: S["ExportacaoPedido"]) => call<Exportacao>("me/exportacoes/", "POST", body);
export const consultarExportacao = (id: string) => call<Exportacao>(`me/exportacoes/${encodeURIComponent(id)}/`);
export const criarIntencao = () => call<S["Intencao"]>("me/exclusao/intencoes/", "POST");
export const editarNome = (body: S["PatchedMeNome"]) => call<S["Me"]>("me/", "PATCH", body);
export const excluirConta = (body: S["ConfirmacaoExclusao"]) => call<null>("me/", "DELETE", body);

export async function baixarExportacao(id: string) {
  const contexto = inicioRequisicao();
  try {
    if (!contexto.dono) throw new ApiError(401);
    const response = await fetch(`/api/me/exportacoes/${encodeURIComponent(id)}/download/`, {
      credentials: "same-origin", cache: "no-store", signal: contexto.signal,
      headers: { "X-Varal-Identidade-Esperada": contexto.dono },
    });
    contexto.verificar(response);
    if (!response.ok) {
      const data: unknown = await response.json().catch(() => null);
      contexto.verificar(response);
      throw new ApiError(response.status, undefined, data);
    }
    const blob = await response.blob();
    contexto.verificar(response);
    const url = URL.createObjectURL(blob);
    try {
      const a = document.createElement("a");
      a.href = url; a.download = "varal-exportacao.json"; a.click();
    } finally { URL.revokeObjectURL(url); }
  } finally { contexto.fechar(); }
}
