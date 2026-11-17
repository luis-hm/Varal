"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { getAuthConfig, login, logout, requestPassword, resetPassword, signup } from "./client";
import { desativarPush } from "@/lib/notificacoes/push";

export const useAuthConfig = () => useQuery({ queryKey: ["auth-config"], queryFn: getAuthConfig, staleTime: 300_000, retry: false });
export const useLogin = () => useMutation({ mutationFn: login });
export const useSignup = () => useMutation({ mutationFn: signup });
export const useRequestPassword = () => useMutation({ mutationFn: requestPassword });
export const useResetPassword = () => useMutation({ mutationFn: resetPassword });
export const useLogout = () => useMutation({ mutationFn: async (usuario: string) => {
  // The server also revokes the session's registrations when logout succeeds.
  // Local unsubscribe is attempted even if installation revocation fails.
  try { await desativarPush(usuario); } catch {
    try { sessionStorage.setItem("varal.push.logout-aviso", "1"); } catch { /* storage unavailable */ }
  }
  return logout(usuario);
} });
