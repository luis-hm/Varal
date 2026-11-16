"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/lib/grupos/client";
import * as api from "./client";

// 4xx are answers (404 = not yours or not there, RN06), not transient failures: never retry them.
const retry = (count: number, error: Error) => !(error instanceof ApiError && error.status < 500) && count < 2;

export const useContas = (espacoId: string | undefined, filtros: api.Filtros) =>
  useQuery({ queryKey: ["contas", "lista", espacoId, filtros], queryFn: () => api.listarContas(espacoId!, filtros), enabled: !!espacoId, retry });
export const useResumo = (espacoId: string | undefined) =>
  useQuery({ queryKey: ["contas", "resumo", espacoId], queryFn: () => api.verResumo(espacoId!), enabled: !!espacoId, retry });
export const useConta = (id: string | undefined) =>
  useQuery({ queryKey: ["contas", "detalhe", id], queryFn: () => api.verConta(id!), enabled: !!id, retry });
export const useLerInstrumento = () => useMutation({ mutationFn: api.lerInstrumento });
export const useEnviarPdf = () => useMutation({ mutationFn: ({ espaco, arquivo, lancamentoId }: { espaco: string; arquivo: File; lancamentoId?: string }) => api.enviarPdf(espaco, arquivo, lancamentoId) });
export const usePdf = (id: string | undefined) => useQuery({
  queryKey: ["pdf", id],
  queryFn: () => api.verPdf(id!),
  enabled: !!id,
  retry,
  refetchInterval: (query) => ["pendente", "lendo"].includes(query.state.data?.estado ?? "") ? 1500 : false,
});
export const useLinkPdfConta = () => useMutation({ mutationFn: api.linkPdfConta });
export const useLinkPdf = () => useMutation({ mutationFn: api.linkPdf });

// Every bill query starts with ["contas"]: a write refreshes lists, totals and the open detail.
export function useAcoesConta() {
  const qc = useQueryClient();
  const onSuccess = () => qc.invalidateQueries({ queryKey: ["contas"] });
  return {
    criar: useMutation({ mutationFn: ({ espaco, body }: { espaco: string; body: api.ContaEntrada }) => api.criarConta(espaco, body), onSuccess }),
    editar: useMutation({ mutationFn: ({ id, body }: { id: string; body: Parameters<typeof api.editarConta>[1] }) => api.editarConta(id, body), onSuccess }),
    cancelar: useMutation({ mutationFn: api.cancelarConta, onSuccess }),
  };
}
