import type { components } from "@/types/api";
import { call } from "@/lib/grupos/client";

type S = components["schemas"];
export type Notificacao = S["Notificacao"];
export const resumoAvisos = () => call<S["ResumoNotificacoes"]>("notificacoes/resumo/");
export const listarAvisos = (cursor?: string) => call<S["ListaNotificacoes"]>(`notificacoes/${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ""}`);
export const lerAviso = (id: string) => call<S["Ler"]>(`notificacoes/${encodeURIComponent(id)}/ler/`, "POST");
export const lerTodos = () => call<S["LerTodas"]>("notificacoes/ler-todas/", "POST");
export const preferencias = () => call<S["Preferencias"]>("notificacoes/preferencias/");
export const atualizarPreferencias = (body: S["PatchedPreferenciasEntrada"]) => call<S["Preferencias"]>("notificacoes/preferencias/", "PATCH", body);
export const configuracaoPush = () => call<S["PushConfiguracao"]>("notificacoes/push/configuracao/");
export const inscreverPush = (body: S["InscricaoEntrada"]) => call<S["InscricaoResultado"]>("notificacoes/push/inscricoes/", "POST", body);
export const revogarInstalacao = (id: string) => call<null>(`notificacoes/push/instalacoes/${encodeURIComponent(id)}/`, "DELETE");
