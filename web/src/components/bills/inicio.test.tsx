import { screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { Inicio } from "./inicio";
import { json, renderComSessao } from "./teste-sessao";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }));

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(async (url: string) =>
    url === "/api/espacos/g1/resumo/"
      ? json(200, { mes: "2026-11", total_centavos: 287455, qtd: 9, vencidas_qtd: 2, vence_qtd: 3, janela_alerta_dias: 3, atencao: [], por_casa: [{ id: "c1", nome: "Casa 1", total_centavos: 147960, qtd: 4 }] })
      : json(404, { detail: "x" }),
  ));
});
afterEach(() => vi.unstubAllGlobals());

test("q9/q12/q23: the hero names its month, no paid bar and no 'pagas'", async () => {
  renderComSessao(<Inicio />);
  expect(await screen.findByText("Total de novembro")).toBeTruthy();
  expect(screen.getByText("9 contas")).toBeTruthy();
  expect(screen.getAllByText("R$ 2.874,55").length).toBeGreaterThan(0);
  expect(screen.getByText("4 contas em novembro")).toBeTruthy();
  expect(screen.queryByRole("progressbar")).toBeNull();
  expect(document.body.textContent).not.toMatch(/pagas|de \d+ pagas/);
  expect(document.body.textContent).not.toContain("API:");
});
