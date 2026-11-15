// Doop: k0kB5dc-Vo / shell JJvrRugL0_ + SMDsrD8FGT; CU01 (authenticated access).
import { cookies } from "next/headers";
import { Suspense, type ReactNode } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { requireUser } from "@/lib/auth/server";
import { COOKIE_ESPACO, resolverEspaco } from "@/lib/espaco";

async function SessionShell({ children }: { children: ReactNode }) {
  const user = await requireUser();
  // Q4: the current space is checked against /api/me/; anything else falls back to the personal space.
  const espaco = resolverEspaco(user, (await cookies()).get(COOKIE_ESPACO)?.value);
  return <AppShell user={user} espaco={espaco}>{children}</AppShell>;
}

export function ProtectedShell({ children }: { children: ReactNode }) {
  return <Suspense fallback={<p role="status">Carregando sua conta…</p>}><SessionShell>{children}</SessionShell></Suspense>;
}
