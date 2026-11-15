import type { Papel } from "./client";

// Doop: k0kB5dc-Vo / RadioCard texts in 11 · Convidar membro (bkv_O9ohNO) and M05 (8XSFrkwy2d).
export const papeis: Record<Papel, { title: string; text: string }> = {
  admin: { title: "Admin", text: "Faz tudo, inclusive convidar e criar casas" },
  membro: { title: "Membro", text: "Cria, edita e paga contas do grupo" },
  pagador: { title: "Pagador", text: "Vê só as contas dele e marca como pagas" },
  observador: { title: "Observador", text: "Só acompanha, sem alterar nada" },
};

export const ordemPapeis: Papel[] = ["admin", "membro", "pagador", "observador"];

export function iniciais(nome: string) {
  return nome.split(/[\s@._-]+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
}

/** RN31: the link is always shown shortened, ellipsis in the middle; copy/share use the full URL. */
export function encurtarLink(url: string) {
  const { host, pathname } = new URL(url);
  const token = pathname.split("/").pop() ?? "";
  return `${host}/c/${token.slice(0, 8)}…${token.slice(-4)}`;
}

export function expiraEm(iso: string, agora = Date.now()) {
  const dias = Math.ceil((new Date(iso).getTime() - agora) / 86_400_000);
  if (dias <= 0) return "Expira hoje";
  return `Expira em ${dias} ${dias === 1 ? "dia" : "dias"}`;
}
