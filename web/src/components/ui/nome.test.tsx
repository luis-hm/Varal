import { render, screen, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { expect, test, vi } from "vitest";
import { ContaCard } from "@/components/bills/bill-card";
import { ContaDetalhe } from "@/components/bills/conta-detalhe";
import { MemberRow } from "@/components/groups/member-row";
import type { Conta, ContaDetalhe as Detalhe } from "@/lib/contas/client";
import styles from "./nome.module.css";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }));

// About 60 characters, the kind of e-mail that used to wrap the BillCard meta and the detail rows.
const EMAIL = "maria.aparecida.dos.santos.oliveira.contas@exemplo-longo.com";
const pessoa = (id: string) => ({ id, nome: EMAIL, sou_eu: false });

const conta = {
  id: "l1",
  descricao: "Energia",
  valor_centavos: 28743,
  vencimento: "2026-11-20",
  status: "pendente",
  status_exibido: "pendente",
  dias_para_vencer: 5,
  espaco: { id: "g1", nome: "Família", tipo: "grupo" },
  subgrupo: null,
  pagador: pessoa("u2"),
} as unknown as Conta;

const literal = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

function cortado(el: HTMLElement, valor: string) {
  expect(el.classList.contains(styles.nome)).toBe(true);
  expect(el.getAttribute("title")).toBe(valor);
}

test("ajuste 29: BillCard meta is one cut line, whole value in title and in the accessible name", () => {
  render(<ContaCard conta={conta} href="/contas/l1" />);
  const meta = `Vence 20/11 · ${EMAIL} paga`;
  cortado(screen.getByTitle(meta), meta);
  expect(screen.getByRole("link", { name: new RegExp(literal(meta)) })).toBeTruthy();
});

test("ajuste 29: detail Quem paga, Quem vê, Criada por and history keep a long e-mail on one line", () => {
  const detalhe = {
    ...conta,
    visibilidade: "restrita",
    acesso: [pessoa("u3")],
    quem_ve: [pessoa("u2"), pessoa("u3"), pessoa("u4")],
    criador: pessoa("u4"),
    criado_em: "2026-11-01T12:00:00Z",
    pode_editar: false,
    pagamento_ativo: null,
    pagamentos: [],
    pode_pagar: false,
    pode_desfazer_pagamento: false,
    pode_anexar_comprovante: false,
    documento_pdf: null,
    instrumento: null,
    historico: [{ acao: "criada", automatica: false, autor: EMAIL, sou_eu: false, dados: {}, criado_em: "2026-11-01T12:00:00Z" }],
  } as unknown as Detalhe;
  render(<QueryClientProvider client={new QueryClient()}><ContaDetalhe conta={detalhe} voltar="/contas" /></QueryClientProvider>);
  const info = screen.getByRole("region", { name: "Informações" });
  cortado(within(info).getAllByTitle(EMAIL)[0], EMAIL); // Quem paga
  const quemVe = within(info).getByText("Quem vê").parentElement!;
  const nomes = within(quemVe).getAllByTitle(EMAIL);
  expect(nomes).toHaveLength(3); // Q04-38: effective audience, including creator and payer, not only `acesso`.
  for (const nome of nomes) cortado(nome, EMAIL);
  expect(within(info).getAllByTitle(EMAIL)).toHaveLength(5); // payer + 3 viewers + creator; date stays outside the cut
  const historico = screen.getByRole("region", { name: "Histórico" });
  cortado(within(historico).getByTitle(EMAIL), EMAIL);
  expect(within(historico).getByRole("listitem").textContent).toContain(`${EMAIL} criou a conta`);
});

test("ajuste 29: member row name is cut on one line; the button's accessible name stays whole", () => {
  render(<MemberRow initials="MA" name={EMAIL} role="membro" onClick={() => {}} />);
  cortado(screen.getByTitle(EMAIL), EMAIL);
  expect(screen.getByRole("button", { name: new RegExp(literal(EMAIL)) })).toBeTruthy();
});
