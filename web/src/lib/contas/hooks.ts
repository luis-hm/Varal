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
export const useRecorrencias = (espaco: string | undefined) => useQuery({ queryKey: ["recorrencias", "lista", espaco], queryFn: () => api.listarRecorrencias(espaco!), enabled: !!espaco, retry });
export const useRecorrencia = (id: string | undefined) => useQuery({ queryKey: ["recorrencias", "detalhe", id], queryFn: () => api.verRecorrencia(id!), enabled: !!id, retry });
export function useAcoesRecorrencia() {
  const qc = useQueryClient();
  const atualizar = () => { for (const key of ["recorrencias", "contas", "grupos"]) void qc.invalidateQueries({ queryKey: [key] }); };
  return {
    criar: useMutation({ mutationFn: ({ espaco, body }: { espaco: string; body: api.CriarRecorrencia }) => api.criarRecorrencia(espaco, body), onSuccess: atualizar }),
    editar: useMutation({ mutationFn: ({ id, body }: { id: string; body: api.EditarRecorrencia }) => api.editarRecorrencia(id, body), onSuccess: atualizar }),
    acao: useMutation({ mutationFn: ({ id, acao }: { id: string; acao: "pausar" | "retomar" | "encerrar" }) => api.acaoRecorrencia(id, acao), onSuccess: atualizar }),
  };
}

export function useAcoesPagamento() {
  const qc = useQueryClient();
  const atualizar = (conta: api.ContaDetalhe) => {
    qc.setQueryData(["contas", "detalhe", conta.id], conta);
    void qc.invalidateQueries({ queryKey: ["contas"] });
    void qc.invalidateQueries({ queryKey: ["grupos"] });
  };
  return {
    enviar: useMutation({ mutationFn: ({ id, arquivo, pagamento }: { id: string; arquivo: File; pagamento?: string }) => api.enviarComprovante(id, arquivo, pagamento) }),
    consultar: useMutation({ mutationFn: api.verComprovante }),
    abrir: useMutation({ mutationFn: api.linkComprovante, gcTime: 0 }),
    marcar: useMutation({ mutationFn: ({ id, body }: { id: string; body: Parameters<typeof api.marcarPagamento>[1] }) => api.marcarPagamento(id, body), onSuccess: atualizar }),
    anexar: useMutation({ mutationFn: ({ id, pagamento, body }: { id: string; pagamento: string; body: Parameters<typeof api.anexarComprovante>[2] }) => api.anexarComprovante(id, pagamento, body), onSuccess: atualizar }),
    desfazer: useMutation({ mutationFn: ({ id, pagamento }: { id: string; pagamento: string }) => api.desfazerPagamento(id, pagamento), onSuccess: atualizar }),
  };
}

// Every bill query starts with ["contas"]: a write refreshes lists, totals and the open detail.
export function useAcoesConta() {
  const qc = useQueryClient();
  const onSuccess = () => {
    void qc.invalidateQueries({ queryKey: ["grupos"] });
    void qc.invalidateQueries({ queryKey: ["recorrencias"] });
    return qc.invalidateQueries({ queryKey: ["contas"] });
  };
  return {
    criar: useMutation({ mutationFn: ({ espaco, body }: { espaco: string; body: api.ContaEntrada }) => api.criarConta(espaco, body), onSuccess }),
    editar: useMutation({ mutationFn: ({ id, body }: { id: string; body: Parameters<typeof api.editarConta>[1] }) => api.editarConta(id, body), onSuccess }),
    cancelar: useMutation({ mutationFn: ({ id, body }: { id: string; body?: Parameters<typeof api.cancelarConta>[1] }) => api.cancelarConta(id, body), onSuccess }),
  };
}
