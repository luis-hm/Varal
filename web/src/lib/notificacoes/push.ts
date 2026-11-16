import type { components } from "@/types/api";
import { inscreverPush, revogarInstalacao } from "./client";

const KEY = "varal.push.instalacao.v1";
let epoch = 0;
let activating = false;
type Instalacao = { id: string; usuario: string; ativa: boolean };
function ler(): Instalacao | null {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(KEY) ?? "null");
    if (value && typeof value === "object" && "id" in value && typeof value.id === "string" && "usuario" in value && typeof value.usuario === "string" && "ativa" in value && typeof value.ativa === "boolean") return { id: value.id, usuario: value.usuario, ativa: value.ativa };
  } catch { /* unavailable storage: activation will fail safely */ }
  return null;
}
function gravar(value: Instalacao) { localStorage.setItem(KEY, JSON.stringify(value)); }
export function estadoPush(user: string) { return ler()?.usuario === user && ler()?.ativa === true; }
export function suportePush() { return typeof window !== "undefined" && window.isSecureContext && "serviceWorker" in navigator && "PushManager" in window && "Notification" in window; }
function chaveBytes(key: string) {
  const raw = atob((key + "=".repeat((4 - key.length % 4) % 4)).replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(raw, (c) => c.charCodeAt(0));
}
async function unsubscribe() {
  if (typeof navigator === "undefined" || !("serviceWorker" in navigator)) return;
  const registration = await navigator.serviceWorker.getRegistration("/");
  const sub = await registration?.pushManager.getSubscription();
  if (sub && !(await sub.unsubscribe())) throw new Error("Não foi possível desativar as notificações neste dispositivo.");
}
export async function ativarPush(user: string, config: components["schemas"]["PushConfiguracao"]) {
  if (activating) throw new Error("Ativação em andamento.");
  if (!suportePush()) throw new Error("Este navegador não permite notificações neste dispositivo.");
  if (!config.habilitado || !config.chave_publica) throw new Error("Notificações indisponíveis no momento.");
  activating = true;
  const atual = epoch;
  const check = () => { if (atual !== epoch) throw new Error("A ativação foi interrompida."); };
  try {
    // Browser permission must be requested while the explicit click still has user activation.
    const permissionRequest = Notification.requestPermission();
    let instalacao = ler();
    if (instalacao && instalacao.usuario !== user) {
      await unsubscribe();
      check();
      localStorage.removeItem(KEY);
      instalacao = null;
    }
    instalacao ??= { id: crypto.randomUUID(), usuario: user, ativa: false };
    gravar(instalacao);
    const permission = await permissionRequest;
    check();
    if (permission !== "granted") throw new Error("Permissão para notificações não concedida neste navegador.");
    const registration = await navigator.serviceWorker.register("/sw-notificacoes.js");
    check();
    const subscription = await registration.pushManager.getSubscription() ?? await registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: chaveBytes(config.chave_publica) });
    if (atual !== epoch) { await subscription.unsubscribe(); check(); }
    const json = subscription.toJSON();
    if (!json.endpoint || !json.keys?.p256dh || !json.keys.auth) throw new Error("Não foi possível preparar este dispositivo.");
    const resultado = await inscreverPush({ instalacao: instalacao.id, endpoint: json.endpoint, keys: { p256dh: json.keys.p256dh, auth: json.keys.auth } });
    if (atual !== epoch) { await subscription.unsubscribe(); check(); }
    if (!resultado.ativo) throw new Error("Não foi possível ativar notificações neste dispositivo.");
    gravar({ ...instalacao, ativa: true });
  } finally { activating = false; }
}
/** Terminate this cycle before any awaits, so late activation cannot restore it. */
export async function desativarPush() {
  epoch++;
  const instalacao = ler();
  try { localStorage.removeItem(KEY); } catch { /* server revocation still attempted */ }
  const outcomes = await Promise.allSettled([instalacao ? revogarInstalacao(instalacao.id) : Promise.resolve(), unsubscribe()]);
  if (outcomes.some((result) => result.status === "rejected")) throw new Error("Não foi possível confirmar a desativação em todos os serviços.");
}
