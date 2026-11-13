import type { IconName } from "@/components/ui/icon";

// Navigation sections shared by TabBar, SideNav and AppShell (labels and icons from the Doop).
export const secoes = {
  inicio: { label: "Início", href: "/", icon: "varal" },
  contas: { label: "Contas", href: "/contas", icon: "contas" },
  grupos: { label: "Grupos", href: "/grupos", icon: "grupo" },
  avisos: { label: "Avisos", href: "/avisos", icon: "sino" },
  perfil: { label: "Perfil", href: "/perfil", icon: "perfil" },
} satisfies Record<string, { label: string; href: string; icon: IconName }>;

export type Secao = keyof typeof secoes;

export function secaoAtiva(pathname: string): Secao | undefined {
  return (Object.keys(secoes) as Secao[]).find((s) =>
    s === "inicio" ? pathname === "/" : pathname.startsWith(secoes[s].href),
  );
}
