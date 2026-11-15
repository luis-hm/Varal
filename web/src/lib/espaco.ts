// Current space (decision 2 / Q4): an id in the `espaco` cookie, only a choice of view. The API never trusts
// it: every request names the space and goes through acesso.py. Unknown, foreign or payer-group ids fall
// back to the personal space (the payer only has the simple mode, RN07).
import type { Me } from "@/lib/auth/types";
import type { Papel } from "@/lib/grupos/client";

export const COOKIE_ESPACO = "espaco";

export type EspacoAtual = { id: string; nome: string; tipo: "pessoal" | "grupo"; papel?: Papel };

export function resolverEspaco(user: Me, id: string | undefined): EspacoAtual {
  const grupo = user.grupos.find((g) => g.id === id && g.papel !== "pagador");
  if (grupo) return { id: grupo.id, nome: grupo.nome, tipo: "grupo", papel: grupo.papel };
  return { id: user.espaco_pessoal.id, nome: "Pessoal", tipo: "pessoal" };
}

/** Spaces where the user may create a bill (RN05: owner, admin, member). */
export function espacosParaCriar(user: Me): EspacoAtual[] {
  return [
    resolverEspaco(user, undefined),
    ...user.grupos
      .filter((g) => g.papel === "admin" || g.papel === "membro")
      .map((g) => ({ id: g.id, nome: g.nome, tipo: "grupo" as const, papel: g.papel })),
  ];
}

export function gravarEspaco(id: string) {
  document.cookie = `${COOKIE_ESPACO}=${encodeURIComponent(id)}; path=/; max-age=31536000; samesite=lax`;
}
