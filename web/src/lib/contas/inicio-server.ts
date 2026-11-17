import "server-only";
import { cookies } from "next/headers";
import type { components } from "@/types/api";
import { requireUser } from "@/lib/auth/server";
import { COOKIE_ESPACO, resolverEspaco } from "@/lib/espaco";

type S = components["schemas"];
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export async function dadosInicio() {
  const user = await requireUser();
  const jar = await cookies();
  const espaco = resolverEspaco(user, jar.get(COOKIE_ESPACO)?.value);
  if (!UUID.test(espaco.id)) return { usuario: user.id, espaco: espaco.id };
  const api = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
  async function get<T>(path: string): Promise<T | undefined> {
    try {
      const response = await fetch(`${api}${path}`, { cache: "no-store", headers: { Cookie: jar.toString(), "X-Varal-Identidade-Esperada": user.id } });
      if (!response.ok || response.headers.get("X-Varal-Identidade") !== user.id) return undefined;
      return await response.json() as T;
    } catch { return undefined; }
  }
  const [resumo, avisos] = await Promise.all([
    get<S["Resumo"]>(`/api/espacos/${encodeURIComponent(espaco.id)}/resumo/`),
    get<S["ResumoNotificacoes"]>("/api/notificacoes/resumo/"),
  ]);
  return { usuario: user.id, espaco: espaco.id, resumo, avisos };
}
