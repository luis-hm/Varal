// Doop: k0kB5dc-Vo / shell de 02 · Início (JJvrRugL0_, TabBar) + D02 · Início (SMDsrD8FGT, SideNav)
"use client";

import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useState, type ReactNode } from "react";
import { ContaFolha } from "@/components/bills/conta-folha";
import type { Me } from "@/lib/auth/types";
import { gravarEspaco, type EspacoAtual } from "@/lib/espaco";
import { iniciais, papeis } from "@/lib/grupos/papeis";
import { secaoAtiva } from "./secoes";
import { SideNav, type EspacoOpcao } from "./side-nav";
import { TabBar } from "./tab-bar";
import styles from "./app-shell.module.css";

type SessaoValor = {
  user: Me;
  espaco: EspacoAtual;
  /** FAB "+" and SideNav "Nova conta" (Q3): the bill form opens straight away. */
  novaConta: () => void;
  escolherEspaco: (opcao: EspacoOpcao) => void;
};
export const Sessao = createContext<SessaoValor | null>(null);

export function useSessao() {
  const sessao = useContext(Sessao);
  if (!sessao) throw new Error("useSessao fora do AppShell");
  return sessao;
}

// Selector options come from /api/me/ (no extra request): personal space plus each group with the role.
export function espacosDoUsuario(user: Me, atual?: string): EspacoOpcao[] {
  return [
    { id: user.espaco_pessoal.id, iniciais: "P", nome: "Pessoal", detalhe: "Espaço pessoal", atual: atual === user.espaco_pessoal.id },
    ...user.grupos.map((g) => ({
      id: g.id,
      papel: g.papel,
      iniciais: iniciais(g.nome),
      nome: g.nome,
      detalhe: `Grupo · ${papeis[g.papel].title}`,
      atual: g.id === atual,
    })),
  ];
}

// One app: below 1024px the TabBar, from 1024px the fixed 264px SideNav (CSS decides, no JS).
export function AppShell({ children, user, espaco }: { children: ReactNode; user?: Me; espaco?: EspacoAtual }) {
  const pathname = usePathname();
  const router = useRouter();
  const [nova, setNova] = useState(false);
  const [chave, setChave] = useState(0); // a fresh form on every opening
  const active = secaoAtiva(pathname);
  const espacos = user ? espacosDoUsuario(user, espaco?.id) : undefined;
  const name = user?.nome || user?.email.split("@")[0] || "";
  const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map((word) => word[0]).join("").toUpperCase();

  // Decision 2: stay in Início/Contas, otherwise go to Início; a payer group opens the simple mode (not stored).
  function escolherEspaco(o: EspacoOpcao) {
    if (o.papel === "pagador") return router.push(`/grupos/${o.id}/simples`);
    gravarEspaco(o.id);
    if (pathname !== "/" && pathname !== "/contas") router.push(pathname.startsWith("/contas") ? "/contas" : "/");
    router.refresh(); // the shell reads the cookie on the server
  }
  const novaConta = () => {
    setChave((k) => k + 1);
    setNova(true);
  };

  const shell = (
    <div className={styles.shell}>
      <div className={styles.side}>
        <SideNav
          active={active}
          espaco={espacos?.find((e) => e.atual) ?? espacos?.[0]}
          espacos={espacos}
          onEscolher={escolherEspaco}
          onNovaConta={user ? novaConta : undefined}
          usuario={user ? { iniciais: initials, nome: name, detalhe: user.email } : undefined}
        />
      </div>
      <main className={styles.main}>{children}</main>
      <div className={styles.bottom}>
        <TabBar active={active === "avisos" ? undefined : active} onNovaConta={user ? novaConta : undefined} />
      </div>
    </div>
  );
  if (!user || !espaco) return shell;
  return (
    <Sessao.Provider value={{ user, espaco, novaConta, escolherEspaco }}>
      {shell}
      {chave > 0 && <ContaFolha key={chave} open={nova} onClose={() => setNova(false)} />}
    </Sessao.Provider>
  );
}
