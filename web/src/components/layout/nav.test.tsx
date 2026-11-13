import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
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
