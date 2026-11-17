import "server-only";

import { cache } from "react";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { Me } from "./types";

// React.cache deduplicates within this render only; session data never enters a shared cache.
export const currentUser = cache(async (): Promise<Me | null> => {
  const jar = await cookies();
  const owner = jar.get("varal_owner")?.value;
  if (!jar.has("sessionid") || jar.has("varal_local_locked") || !owner || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(owner)) return null;
  const apiUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
  const response = await fetch(`${apiUrl}/api/me/`, {
    headers: { Cookie: jar.toString(), "X-Varal-Identidade-Esperada": owner },
    cache: "no-store",
  });
  if ([401, 403, 409].includes(response.status) || response.headers.get("X-Varal-Identidade") !== owner) return null;
  if (!response.ok) throw new Error("Não foi possível consultar sua sessão. Tente novamente.");
  const data: Me = await response.json();
  return data.id === owner ? data : null;
});

export async function requireUser() {
  const user = await currentUser();
  if (!user) redirect("/entrar");
  return user;
}
