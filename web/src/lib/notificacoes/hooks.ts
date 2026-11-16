"use client";
import { useInfiniteQuery, useMutation, useQuery, useQueryClient, type InfiniteData } from "@tanstack/react-query";
import type { components } from "@/types/api";
import { ApiError } from "@/lib/grupos/client";
import { atualizarPreferencias, configuracaoPush, lerAviso, lerTodos, listarAvisos, preferencias, resumoAvisos } from "./client";

export const avisoKey = (user: string) => ["avisos", user] as const;
export const useAvisosResumo = (user?: string) => useQuery({ queryKey: [...avisoKey(user ?? ""), "resumo"], queryFn: resumoAvisos, enabled: !!user, retry: false });
export const usePushConfig = (user: string) => useQuery({ queryKey: [...avisoKey(user), "push-config"], queryFn: configuracaoPush, retry: false });
export const useAvisos = (user: string) => useInfiniteQuery({ queryKey: [...avisoKey(user), "lista"], queryFn: ({ pageParam }) => listarAvisos(pageParam), initialPageParam: undefined as string | undefined, getNextPageParam: (page) => page.proximo ?? undefined, retry: false });
export function useLeituraAvisos(user: string) {
  const cache = useQueryClient();
  const atualizar = () => cache.invalidateQueries({ queryKey: avisoKey(user) });
  const um = useMutation({ mutationFn: lerAviso, onError: (error, id) => {
    if (!(error instanceof ApiError) || error.status !== 404) return;
    cache.setQueryData<InfiniteData<components["schemas"]["ListaNotificacoes"]>>([...avisoKey(user), "lista"], (old) => old && ({ ...old, pages: old.pages.map((page) => ({ ...page, resultados: page.resultados.filter((item) => item.id !== id) })) }));
    cache.setQueryData<components["schemas"]["ResumoNotificacoes"]>([...avisoKey(user), "resumo"], (old) => old && ({ ...old, recentes: old.recentes.filter((item) => item.id !== id) }));
  }, onSettled: atualizar });
  const todos = useMutation({ mutationFn: lerTodos, onSettled: atualizar });
  return { um, todos };
}
export function usePreferencias(user: string) {
  const cache = useQueryClient();
  const queryKey = [...avisoKey(user), "preferencias"];
  const query = useQuery({ queryKey, queryFn: preferencias, retry: false });
  const salvar = useMutation({ mutationFn: atualizarPreferencias, onSuccess: (data) => cache.setQueryData(queryKey, data) });
  return { query, salvar };
}
