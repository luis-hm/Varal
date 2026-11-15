import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
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

test("ca17: selector options come from /api/me/; the payer goes to the simple mode", () => {
  expect(espacosDoUsuario(me, "/grupos/g1").map((e) => [e.href, e.detalhe, !!e.atual])).toEqual([
    ["/", "Espaço pessoal", false],
    ["/grupos/g1", "Grupo · Admin", true],
    ["/grupos/g2/simples", "Grupo · Pagador", false],
  ]);
  expect(espacosDoUsuario(me, "/contas")[0].atual).toBe(true);
});

test("ca17: the space selector opens a list of spaces plus Criar grupo, and Esc closes it", () => {
  const espacos = espacosDoUsuario(me, "/");
  render(<SideNav espaco={espacos[0]} espacos={espacos} />);
  const botao = screen.getByRole("button", { name: /Trocar de espaço/ });
  expect(botao.getAttribute("aria-expanded")).toBe("false");
  fireEvent.click(botao);
  expect(botao.getAttribute("aria-expanded")).toBe("true");
  expect(screen.getByRole("link", { name: /Condomínio/ }).getAttribute("href")).toBe("/grupos/g2/simples");
  expect(screen.getByRole("link", { name: "Criar grupo" }).getAttribute("href")).toBe("/grupos?criar=1");
  fireEvent.keyDown(document, { key: "Escape" });
  expect(botao.getAttribute("aria-expanded")).toBe("false");
  expect(document.activeElement).toBe(botao);
});
