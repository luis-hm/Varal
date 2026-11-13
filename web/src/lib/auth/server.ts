import "server-only";

import { cache } from "react";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { Me } from "./types";

// React.cache deduplicates within this render only; session data never enters a shared cache.
export const currentUser = cache(async (): Promise<Me | null> => {
  const jar = await cookies();
  if (!jar.has("sessionid")) return null;
  const apiUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
  const response = await fetch(`${apiUrl}/api/me/`, {
    headers: { Cookie: jar.toString() },
    cache: "no-store",
  });
  if (response.status === 401 || response.status === 403) return null;
  if (!response.ok) throw new Error("Não foi possível consultar sua sessão. Tente novamente.");
  return response.json();
});

export async function requireUser() {
  const user = await currentUser();
  if (!user) redirect("/entrar");
  return user;
}
