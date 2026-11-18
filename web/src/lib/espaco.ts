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

/** Spaces where the user may create a bill (RN05: owner, admin, member). Ajuste 30: the current one comes first
 * (the form selects the first); when it cannot take a bill (observer), the order stays as it is. */
export function espacosParaCriar(user: Me, atual?: string): EspacoAtual[] {
  const todos = [
    resolverEspaco(user, undefined),
    ...user.grupos
      // COR-10: an observer may create where the admin allowed it; offered from that group's own screens.
      .filter((g) => g.papel === "admin" || g.papel === "membro" || (g.papel === "observador" && g.id === atual))
      .map((g) => ({ id: g.id, nome: g.nome, tipo: "grupo" as const, papel: g.papel })),
  ];
  const i = todos.findIndex((e) => e.id === atual);
  return i > 0 ? [todos[i], ...todos.slice(0, i), ...todos.slice(i + 1)] : todos;
}

export function gravarEspaco(id: string) {
  document.cookie = `${COOKIE_ESPACO}=${encodeURIComponent(id)}; path=/; max-age=31536000; samesite=lax`;
}
