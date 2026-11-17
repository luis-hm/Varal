// Doop: k0kB5dc-Vo / shell de 02 · Início (JJvrRugL0_, TabBar) + D02 · Início (SMDsrD8FGT, SideNav)
"use client";

import { usePathname, useRouter } from "next/navigation";
import { createContext, lazy, Suspense, useContext, useEffect, useState, type ReactNode } from "react";
import type { Me } from "@/lib/auth/types";
import { gravarEspaco, type EspacoAtual } from "@/lib/espaco";
import { iniciais, papeis } from "@/lib/grupos/papeis";
import { useAvisosResumo } from "@/lib/notificacoes/hooks";
import { Folha } from "@/components/ui/folha";
import { secaoAtiva } from "./secoes";
import { SideNav, type EspacoOpcao } from "./side-nav";
import { TabBar } from "./tab-bar";
import styles from "./app-shell.module.css";

const ContaFolha = lazy(() => import("@/components/bills/conta-folha").then((modulo) => ({ default: modulo.ContaFolha })));
const AvisosGaveta = lazy(() => import("@/components/notifications/avisos").then((modulo) => ({ default: modulo.AvisosGaveta })));

type SessaoValor = {
  user: Me;
  espaco: EspacoAtual;
  /** FAB "+" and SideNav "Nova conta" (Q3): the bill form opens straight away. */
  novaConta: (origem?: HTMLElement) => void;
  abrirAvisos: (origem?: HTMLElement) => void;
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
  const avisos = useAvisosResumo(user?.id);
  const [nova, setNova] = useState(false);
  const [gaveta, setGaveta] = useState(false);
  const [chave, setChave] = useState(0); // a fresh form on every opening
  const [origemConta, setOrigemConta] = useState<HTMLElement | null>(null);
  const [origemAvisos, setOrigemAvisos] = useState<HTMLElement | null>(null);
  const active = secaoAtiva(pathname);
  // Ajuste 28: the bill detail is a stacked screen below 1024px (07 has TopBar with Back, no TabBar).
  const empilhada = /^\/contas\/[^/]+/.test(pathname) || pathname === "/avisos";
  const simples = /^\/grupos\/[^/]+\/simples\/?$/.test(pathname);
  const espacos = user ? espacosDoUsuario(user, espaco?.id) : undefined;
  const name = user?.nome || user?.email.split("@")[0] || "";
  const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map((word) => word[0]).join("").toUpperCase();

  useEffect(() => {
    const voltar = (event: PopStateEvent) => setGaveta(event.state?.varalAvisos === true);
    window.addEventListener("popstate", voltar);
    return () => window.removeEventListener("popstate", voltar);
  }, []);
  function abrirAvisos(origem?: HTMLElement) {
    if (!window.matchMedia("(min-width: 1024px)").matches) { router.push("/avisos"); return; }
    if (gaveta) return;
    setOrigemAvisos(origem ?? (document.activeElement instanceof HTMLElement ? document.activeElement : null));
    window.history.pushState({ varalAvisos: true }, "", window.location.href);
    setGaveta(true);
  }
  function fecharAvisos() {
    if (window.history.state?.varalAvisos) window.history.back();
    else setGaveta(false);
  }
  function navegarAviso() {
    if (window.history.state?.varalAvisos) window.history.replaceState({ varalAvisos: false }, "", window.location.href);
    setGaveta(false);
  }

  // Decision 2: stay in Início/Contas, otherwise go to Início; a payer group opens the simple mode (not stored).
  function escolherEspaco(o: EspacoOpcao) {
    if (o.papel === "pagador") return router.push(`/grupos/${o.id}/simples`);
    gravarEspaco(o.id);
    if (pathname !== "/" && pathname !== "/contas") router.push(pathname.startsWith("/contas") ? "/contas" : "/");
    router.refresh(); // the shell reads the cookie on the server
  }
  const novaConta = (origem?: HTMLElement) => {
    setOrigemConta(origem ?? (document.activeElement instanceof HTMLElement ? document.activeElement : null));
    setChave((k) => k + 1);
    setNova(true);
  };

  const shell = (
    <div className={styles.shell} data-empilhada={empilhada || undefined} data-simples={simples || undefined}>
      <div className={styles.side}>
        <SideNav
          active={active}
          espaco={espacos?.find((e) => e.atual) ?? espacos?.[0]}
          espacos={espacos}
          onEscolher={escolherEspaco}
          onNovaConta={user ? novaConta : undefined}
          avisos={avisos.data?.nao_lidas}
          onAvisos={user ? abrirAvisos : undefined}
          usuario={user ? { iniciais: initials, nome: name, detalhe: user.email } : undefined}
        />
      </div>
      <main className={styles.main}>{children}</main>
      {!empilhada && !simples && (
        <div className={styles.bottom}>
          <TabBar active={active === "avisos" ? undefined : active} onNovaConta={user ? novaConta : undefined} />
        </div>
      )}
    </div>
  );
  if (!user || !espaco) return shell;
  return (
    <Sessao.Provider value={{ user, espaco, novaConta, escolherEspaco, abrirAvisos }}>
      {shell}
      {gaveta && <Suspense fallback={<Folha open title="Avisos" onClose={fecharAvisos} returnFocusTo={origemAvisos} restoreFocusOnUnmount><p role="status">Carregando avisos…</p></Folha>}><AvisosGaveta onClose={fecharAvisos} onNavigate={navegarAviso} returnFocusTo={origemAvisos} /></Suspense>}
      {chave > 0 && <Suspense fallback={nova ? <Folha open title="Nova conta" onClose={() => setNova(false)} returnFocusTo={origemConta} restoreFocusOnUnmount><p role="status">Carregando formulário…</p></Folha> : null}><ContaFolha key={chave} open={nova} onClose={() => setNova(false)} returnFocusTo={origemConta} /></Suspense>}
    </Sessao.Provider>
  );
}
