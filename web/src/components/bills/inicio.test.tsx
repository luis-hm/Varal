import { screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { Inicio } from "./inicio";
import { json, renderComSessao } from "./teste-sessao";
import houseStyles from "@/components/groups/house-card.module.css";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }));

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(async (url: string) =>
    url === "/api/espacos/g1/resumo/"
      ? json(200, { mes: "2026-11", total_centavos: 287455, qtd: 9, pagas_qtd: 3, vencidas_qtd: 2, vence_qtd: 3, janela_alerta_dias: 3, atencao: [], por_casa: [{ id: "c1", nome: "Casa 1", total_centavos: 147960, qtd: 4, pagas_qtd: 2 }] })
      : json(404, { detail: "x" }),
  ));
});
afterEach(() => vi.unstubAllGlobals());

test("q07-7: the hero and houses show visible paid counts for the month", async () => {
  renderComSessao(<Inicio />);
  expect(await screen.findByText("Total de novembro")).toBeTruthy();
  expect(screen.getByText("9 contas")).toBeTruthy();
  expect(screen.getAllByText("R$ 2.874,55").length).toBeGreaterThan(0);
  expect(screen.getByText("2 de 4 pagas em novembro")).toBeTruthy();
  expect(screen.getByRole("progressbar").getAttribute("aria-valuetext")).toBe("3 de 9 contas pagas");
  expect(document.body.textContent).not.toContain("API:");
});

test("q07-7: a house without bills names the month and has no progress bar", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => json(200, { mes: "2026-11", total_centavos: 0, qtd: 0, pagas_qtd: 0, vencidas_qtd: 0, vence_qtd: 0, janela_alerta_dias: 3, atencao: [], por_casa: [{ id: "c1", nome: "Casa 1", total_centavos: 0, qtd: 0, pagas_qtd: 0 }] })));
  renderComSessao(<Inicio />);
  const legenda = await screen.findByText("0 contas em novembro");
  expect(legenda.parentElement?.querySelector(`.${houseStyles.bar}`)).toBeNull();
});
