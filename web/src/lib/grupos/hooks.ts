"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as api from "./client";

const keys = {
  lista: ["grupos"] as const,
  grupo: (id: string) => ["grupos", id] as const,
  convites: (id: string) => ["grupos", id, "convites"] as const,
};

// 403/404 are answers (pagador, not a member), not transient failures: never retry them.
const retry = (count: number, error: Error) => !(error instanceof api.ApiError && error.status < 500) && count < 2;

export const useGrupos = () => useQuery({ queryKey: keys.lista, queryFn: api.listarGrupos, retry });
export const useGrupo = (id: string, enabled = true) => useQuery({ queryKey: keys.grupo(id), queryFn: () => api.verGrupo(id), retry, enabled });
export const useConvitesPendentes = (id: string, enabled: boolean) =>
  useQuery({ queryKey: keys.convites(id), queryFn: () => api.listarConvites(id), enabled, retry });
export const usePreviewArquivamento = (id: string, casa: string | undefined) => useQuery({ queryKey: ["grupos", id, "arquivamento", casa], queryFn: () => api.previewArquivamento(id, casa!), enabled: !!casa, retry });

// ["grupos"] prefixes every group query (list, detail, pending invites).
function useInvalidar() {
  const qc = useQueryClient();
  return () => { for (const key of ["grupos", "contas", "recorrencias"]) void qc.invalidateQueries({ queryKey: [key] }); };
}

export const useCriarGrupo = () => {
  const invalidar = useInvalidar();
  return useMutation({ mutationFn: api.criarGrupo, onSuccess: invalidar });
};

export function useAcoesGrupo(id: string) {
  const invalidar = useInvalidar();
  const opts = { onSuccess: invalidar };
  return {
    sair: useMutation({ mutationFn: (resolucoes?: api.Resolucao[]) => api.sairDoGrupo(id, resolucoes) }),
    configurar: useMutation({ mutationFn: (janela: number) => api.configurarGrupo(id, janela), ...opts }),
    alterarPapel: useMutation({ mutationFn: ({ membro, papel }: { membro: string; papel: api.Papel }) => api.alterarPapel(id, membro, papel), ...opts }),
    remover: useMutation({ mutationFn: (membro: string) => api.removerMembro(id, membro), ...opts }),
    criarCasa: useMutation({ mutationFn: (body: Parameters<typeof api.criarCasa>[1]) => api.criarCasa(id, body), ...opts }),
    alterarCasa: useMutation({ mutationFn: ({ casa, ...body }: { casa: string } & Parameters<typeof api.alterarCasa>[2]) => api.alterarCasa(id, casa, body), ...opts }),
    // The invite URL carries a bearer token (RN31): keep it in memory only, drop it at once.
    criarConvite: useMutation({ mutationFn: (papel: api.Papel) => api.criarConvite(id, papel), gcTime: 0, ...opts }),
    revogarConvite: useMutation({ mutationFn: (convite: string) => api.revogarConvite(id, convite), ...opts }),
  };
}

export const useConvitePublico = (token: string) =>
  useQuery({ queryKey: ["convite", token], queryFn: () => api.verConvite(token), retry, gcTime: 0 });
export const useAceitarConvite = (token: string) => useMutation({ mutationFn: () => api.aceitarConvite(token), gcTime: 0 });
