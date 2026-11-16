import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { resolverEspaco } from "@/lib/espaco";
import { espacosDoUsuario } from "./app-shell";
import { secaoAtiva } from "./secoes";
import { SideNav } from "./side-nav";
import { TabBar } from "./tab-bar";

function current() {
  return screen.getAllByRole("link").filter((a) => a.getAttribute("aria-current") === "page");
}

test("ca11: TabBar marks only the active item, every item is a labelled link", () => {
  for (const [active, label] of [
    ["inicio", "Início"],
    ["contas", "Contas"],
    ["grupos", "Grupos"],
    ["perfil", "Perfil"],
  ] as const) {
    const { unmount } = render(<TabBar active={active} />);
    expect(current().map((a) => a.textContent)).toEqual([label]);
    expect(screen.getAllByRole("link").map((a) => a.textContent)).toEqual([
      "Início",
      "Contas",
      "Grupos",
      "Perfil",
    ]);
    expect(screen.getByRole("button", { name: "Nova conta" })).toBeTruthy();
    unmount();
  }
});

test("ca11: SideNav marks only the active item, with routes for the five sections", () => {
  render(<SideNav active="avisos" avisos={3} />);
  const nav = screen.getAllByRole("link").filter((a) => a.getAttribute("aria-label") !== "Varal, início");
  expect(nav.map((a) => [a.textContent, a.getAttribute("href")])).toEqual([
    ["Início", "/"],
    ["Contas", "/contas"],
    ["Grupos", "/grupos"],
    ["Avisos3", "/avisos"],
    ["Perfil", "/perfil"],
  ]);
  expect(current().map((a) => a.getAttribute("href"))).toEqual(["/avisos"]);
});

test("without active no item is current", () => {
  render(<SideNav />);
  expect(current()).toEqual([]);
});

test("secaoAtiva maps the pathname to the section", () => {
  expect(secaoAtiva("/")).toBe("inicio");
  expect(secaoAtiva("/contas")).toBe("contas");
  expect(secaoAtiva("/grupos/abc")).toBe("grupos");
  expect(secaoAtiva("/dev/componentes")).toBeUndefined();
});

const me = {
  id: "u1",
  email: "dev@varal.local",
  nome: "Dev",
  espaco_pessoal: { id: "p1", nome: "Pessoal", tipo: "pessoal" as const },
  grupos: [
    { id: "g1", nome: "Família Martins", papel: "admin" as const },
    { id: "g2", nome: "Condomínio", papel: "pagador" as const },
  ],
};

test("ca17/ca27: selector options come from /api/me/ and the current one is the cookie space", () => {
  expect(espacosDoUsuario(me, "g1").map((e) => [e.id, e.papel, e.detalhe, !!e.atual])).toEqual([
    ["p1", undefined, "Espaço pessoal", false],
    ["g1", "admin", "Grupo · Admin", true],
    ["g2", "pagador", "Grupo · Pagador", false],
  ]);
  expect(espacosDoUsuario(me, "p1")[0].atual).toBe(true);
});

test("ca27: an unknown or payer space in the cookie falls back to the personal one", () => {
  expect(resolverEspaco(me, "g1")).toMatchObject({ id: "g1", tipo: "grupo", papel: "admin" });
  expect(resolverEspaco(me, "g2")).toMatchObject({ id: "p1", tipo: "pessoal", nome: "Pessoal" });
  expect(resolverEspaco(me, "alheio")).toMatchObject({ id: "p1" });
  expect(resolverEspaco(me, undefined)).toMatchObject({ id: "p1" });
});

test("ca17/ca27: the space selector lists the spaces plus Criar grupo, choosing calls onEscolher, Esc closes", () => {
  const espacos = espacosDoUsuario(me, "p1");
  const escolhidos: string[] = [];
  render(<SideNav espaco={espacos[0]} espacos={espacos} onEscolher={(o) => escolhidos.push(o.id)} />);
  const botao = screen.getByRole("button", { name: /Trocar de espaço/ });
  expect(botao.getAttribute("aria-expanded")).toBe("false");
  fireEvent.click(botao);
  expect(botao.getAttribute("aria-expanded")).toBe("true");
  expect(screen.getByRole("link", { name: "Criar grupo" }).getAttribute("href")).toBe("/grupos?criar=1");
  fireEvent.keyDown(document, { key: "Escape" });
  expect(botao.getAttribute("aria-expanded")).toBe("false");
  expect(document.activeElement).toBe(botao);
  fireEvent.click(botao);
  fireEvent.click(screen.getByRole("button", { name: /Condomínio/ }));
  expect(escolhidos).toEqual(["g2"]);
});
