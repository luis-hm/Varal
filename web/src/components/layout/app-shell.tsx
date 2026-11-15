// Doop: k0kB5dc-Vo / shell de 02 · Início (JJvrRugL0_, TabBar) + D02 · Início (SMDsrD8FGT, SideNav)
"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import type { Me } from "@/lib/auth/types";
import { iniciais, papeis } from "@/lib/grupos/papeis";
import { secaoAtiva } from "./secoes";
import { SideNav, type EspacoOpcao } from "./side-nav";
import { TabBar } from "./tab-bar";
import styles from "./app-shell.module.css";

// One app: below 1024px the TabBar, from 1024px the fixed 264px SideNav (CSS decides, no JS).
// Selector options come from /api/me/ (no extra request): personal space plus each group with the role.
export function espacosDoUsuario(user: Me, pathname: string): EspacoOpcao[] {
  const grupoAtual = pathname.match(/^\/grupos\/([^/]+)/)?.[1];
  return [
    { href: "/", iniciais: "P", nome: user.espaco_pessoal.nome, detalhe: "Espaço pessoal", atual: !grupoAtual },
    ...user.grupos.map((g) => ({
      // RN07: the payer only has the simple mode.
      href: g.papel === "pagador" ? `/grupos/${g.id}/simples` : `/grupos/${g.id}`,
      iniciais: iniciais(g.nome),
      nome: g.nome,
      detalhe: `Grupo · ${papeis[g.papel].title}`,
      atual: g.id === grupoAtual,
    })),
  ];
}

export function AppShell({ children, user }: { children: ReactNode; user?: Me }) {
  const pathname = usePathname();
  const active = secaoAtiva(pathname);
  const espacos = user ? espacosDoUsuario(user, pathname) : undefined;
  const name = user?.nome || user?.email.split("@")[0] || "";
  const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map((word) => word[0]).join("").toUpperCase();
  return (
    <div className={styles.shell}>
      <div className={styles.side}>
        <SideNav active={active} espaco={espacos?.find((e) => e.atual) ?? espacos?.[0]} espacos={espacos} usuario={user ? { iniciais: initials, nome: name, detalhe: user.email } : undefined} />
      </div>
      <main className={styles.main}>{children}</main>
      <div className={styles.bottom}>
        <TabBar active={active === "avisos" ? undefined : active} />
      </div>
    </div>
  );
}
