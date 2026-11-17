// Doop: k0kB5dc-Vo / shell JJvrRugL0_ + SMDsrD8FGT; CU01 (authenticated access).
import { cookies } from "next/headers";
import { Suspense, type ReactNode } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { requireUser } from "@/lib/auth/server";
import { COOKIE_ESPACO, resolverEspaco } from "@/lib/espaco";
import { SessaoGuard } from "./sessao-guard";

import { bootstrap } from "./bootstrap-sessao";

async function SessionShell({ children }: { children: ReactNode }) {
  const user = await requireUser();
  // Q4: the current space is checked against /api/me/; anything else falls back to the personal space.
  const espaco = resolverEspaco(user, (await cookies()).get(COOKIE_ESPACO)?.value);
  return <><div key={user.id} data-sessao-privada data-usuario={user.id} hidden suppressHydrationWarning><script dangerouslySetInnerHTML={{ __html: bootstrap }} /><SessaoGuard usuario={user.id}><AppShell user={user} espaco={espaco}>{children}</AppShell></SessaoGuard></div><p data-sessao-status role="status">Verificando sua sessão. Conecte-se para continuar. <a href="/entrar">Entrar</a></p></>;
}

export function ProtectedShell({ children }: { children: ReactNode }) {
  return <Suspense fallback={<p role="status">Carregando sua conta…</p>}><SessionShell>{children}</SessionShell></Suspense>;
}
