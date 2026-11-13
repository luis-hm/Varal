// Doop: k0kB5dc-Vo / shell JJvrRugL0_ + SMDsrD8FGT; CU01 (authenticated access).
import { Suspense, type ReactNode } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { requireUser } from "@/lib/auth/server";

async function SessionShell({ children }: { children: ReactNode }) {
  const user = await requireUser();
  return <AppShell user={user}>{children}</AppShell>;
}

export function ProtectedShell({ children }: { children: ReactNode }) {
  return <Suspense fallback={<p role="status">Carregando sua conta…</p>}><SessionShell>{children}</SessionShell></Suspense>;
}
