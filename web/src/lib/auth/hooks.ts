"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { getAuthConfig, login, logout, requestPassword, resetPassword, signup } from "./client";

export const useAuthConfig = () => useQuery({ queryKey: ["auth-config"], queryFn: getAuthConfig, staleTime: 300_000, retry: false });
export const useLogin = () => useMutation({ mutationFn: login });
export const useSignup = () => useMutation({ mutationFn: signup });
export const useRequestPassword = () => useMutation({ mutationFn: requestPassword });
export const useResetPassword = () => useMutation({ mutationFn: resetPassword });
export const useLogout = () => useMutation({ mutationFn: logout });
