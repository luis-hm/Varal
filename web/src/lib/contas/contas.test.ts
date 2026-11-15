import { expect, test } from "vitest";
import { agrupar } from "@/components/bills/contas-pagina";
import type { Conta, Historico } from "./client";
import { lerValor, reais } from "./formato";
import { linhaHistorico } from "./historico";

test("money: pt-BR input to cents and back", () => {
  expect(lerValor("287,43")).toBe(28743);
  expect(lerValor("1.250")).toBe(125000);
  expect(lerValor("0")).toBeNull();
  expect(lerValor("12,345")).toBeNull();
  expect(reais(287455).replace(/\s/g, " ")).toBe("R$ 2.874,55");
});

const c = (id: string, status_exibido: Conta["status_exibido"], dias: number) => ({ id, status_exibido, dias_para_vencer: dias, valor_centavos: 100 }) as Conta;

test("d2: list groups by due date, cancelled only in its own group", () => {
  const grupos = agrupar([c("a", "pendente", 20), c("b", "vencida", -2), c("c", "vence", 2), c("d", "paga", 1), c("e", "cancelada", 3)]);
  expect(grupos.map(([n, l]) => [n, l.map((x) => x.id)])).toEqual([
    ["Vencidas", ["b"]],
    ["Esta semana", ["c"]],
    ["Mais adiante", ["a"]],
    ["Pagas", ["d"]],
    ["Canceladas", ["e"]],
  ]);
});

const h = (p: Partial<Historico>) => ({ automatica: false, autor: null, sou_eu: false, dados: {}, criado_em: "2026-11-01T12:00:00Z", ...p }) as Historico;

test("rn22/rn30: automatic actions have no author, a deleted author reads Ex-membro", () => {
  expect(linhaHistorico(h({ acao: "pagador_removido", automatica: true, dados: { pagador: ["Mãe", null] } }))).toEqual(["Ficou sem pagador", "Mãe saiu do grupo"]);
  expect(linhaHistorico(h({ acao: "cancelada_automaticamente", automatica: true }))[0]).toBe("Cancelada automaticamente");
  expect(linhaHistorico(h({ acao: "criada", autor: "Ex-membro" }))[0]).toBe("Ex-membro criou a conta");
  expect(linhaHistorico(h({ acao: "editada", sou_eu: true, dados: { valor_centavos: [100, 250], motivo: "saida_rn32" } }))).toEqual([
    "Você editou ao sair do grupo",
    expect.stringMatching(/^valor: R\$\s1,00 → R\$\s2,50$/),
  ]);
});
