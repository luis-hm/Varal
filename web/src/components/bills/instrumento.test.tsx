import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { useState } from "react";
import type { ContaDetalhe, Leitura } from "@/lib/contas/client";
import { ContaFolha } from "./conta-folha";
import { json, renderComSessao } from "./teste-sessao";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, refresh: vi.fn() }) }));

const CODIGO = "00191234546789012345767890123457710000000012345";
const banco: Leitura = {
  instrumento: { tipo: "boleto_bancario", codigo: CODIGO, chave_pix: null, beneficiario: null },
  valor_centavos: 12345,
  vencimento: "2025-02-22",
  vencimentos_possiveis: ["2025-02-22", "2000-07-03"],
  avisos: ["O fator permite duas datas."],
};
const pessoal = { id: "p1", nome: "Pessoal", tipo: "pessoal" as const };
let preview: () => Promise<Response>;
let enviados: unknown[];
let salvarResposta: () => Promise<Response>;

const contaBanco = (): ContaDetalhe => ({
  id: "l1", descricao: "Boleto antigo", valor_centavos: 12345, vencimento: "2000-07-03", status: "pendente", status_exibido: "vencida", dias_para_vencer: -100,
  espaco: pessoal, subgrupo: null, visibilidade: "grupo", acesso: [], quem_ve: [], pagador: null, criador: { nome: "Dev", sou_eu: true }, criado_em: "2000-07-01T12:00:00Z", historico: [], pode_editar: true,
  instrumento: banco.instrumento,
});

beforeEach(() => {
  push.mockClear();
  document.cookie = "csrftoken=t";
  preview = async () => json(200, banco);
  enviados = [];
  salvarResposta = async () => json(201, { id: "l1", vencimento: "2000-07-03" });
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
    if (url === "/api/boletos/ler/") return preview();
    if ((url === "/api/espacos/p1/lancamentos/" || url === "/api/lancamentos/l1/") && init?.method !== "GET") {
      enviados.push(JSON.parse(String(init?.body)));
      return salvarResposta();
    }
    return json(404, { detail: "Não encontrado" });
  }));
});
afterEach(() => vi.unstubAllGlobals());

const textoCodigo = () => screen.getByRole("textbox", { name: "Linha digitável ou Pix copia e cola" });
const valor = () => screen.getByLabelText("Valor", { exact: true }) as HTMLInputElement;

async function ler(codigo = CODIGO) {
  fireEvent.click(screen.getByRole("button", { name: "Colar código" }));
  fireEvent.change(textoCodigo(), { target: { value: codigo } });
  fireEvent.click(screen.getByRole("button", { name: "Ler código" }));
  await screen.findByText(/conferido\. Confira/);
}

test("rn09/rn11: encoded amount is protected and the legacy due date is an explicit choice sent to save", async () => {
  renderComSessao(<ContaFolha open onClose={() => {}} />, pessoal);
  await ler();
  expect(valor().value).toBe("123,45");
  expect(valor().readOnly).toBe(true);
  const vencimento = screen.getByRole("combobox", { name: "Vencimento" });
  expect([...vencimento.querySelectorAll("option")].map((opcao) => opcao.value)).toEqual(banco.vencimentos_possiveis);
  fireEvent.change(vencimento, { target: { value: "2000-07-03" } });
  fireEvent.change(screen.getByLabelText("Descrição"), { target: { value: "Boleto antigo" } });
  fireEvent.click(screen.getByRole("button", { name: "Salvar conta" }));
  await waitFor(() => expect(enviados).toHaveLength(1));
  expect(enviados[0]).toMatchObject({ valor_centavos: 12345, vencimento: "2000-07-03", instrumento: { codigo: CODIGO } });
});

test("rn08: invalid preview preserves the original code and the account fields", async () => {
  preview = async () => json(400, { instrumento: ["Dígito verificador inválido."] });
  renderComSessao(<ContaFolha open onClose={() => {}} />, pessoal);
  fireEvent.change(screen.getByLabelText("Descrição"), { target: { value: "Conta para corrigir" } });
  fireEvent.click(screen.getByRole("button", { name: "Colar código" }));
  fireEvent.change(textoCodigo(), { target: { value: "123.4 inválido" } });
  fireEvent.click(screen.getByRole("button", { name: "Ler código" }));
  expect(await screen.findByText("Dígito verificador inválido.")).toBeTruthy();
  expect((textoCodigo() as HTMLTextAreaElement).value).toBe("123.4 inválido");
  expect((screen.getByLabelText("Descrição") as HTMLInputElement).value).toBe("Conta para corrigir");
  expect(enviados).toEqual([]);
});

test("rf09: dynamic Pix asks for missing fields and does not keep an amount from a previous input", async () => {
  const payload = "000201010212...5406100.50...6304ABCD";
  preview = async () => json(200, { instrumento: { tipo: "pix", codigo: payload, chave_pix: null, beneficiario: "Loja" }, valor_centavos: null, vencimento: null, vencimentos_possiveis: [], avisos: ["Informe o valor e o vencimento."] } satisfies Leitura);
  renderComSessao(<ContaFolha open onClose={() => {}} />, pessoal);
  fireEvent.change(valor(), { target: { value: "100,50" } });
  await ler(payload);
  expect(valor().value).toBe("");
  expect(valor().readOnly).toBe(false);
  const data = screen.getByLabelText("Vencimento") as HTMLInputElement;
  expect(data.value).toBe("");
  expect(data.readOnly).toBe(false);
  fireEvent.click(screen.getByRole("button", { name: "Salvar conta" }));
  expect(screen.getByText("Informe um valor maior que zero, como 287,43.")).toBeTruthy();
  expect(enviados).toEqual([]);
  expect(vi.mocked(fetch).mock.calls.map(([url]) => url)).toEqual(["/api/boletos/ler/"]);
});

test("rf08: a delayed preview cannot overwrite a newer switch to manual entry", async () => {
  let responder!: (resposta: Response) => void;
  preview = () => new Promise((resolve) => { responder = resolve; });
  renderComSessao(<ContaFolha open onClose={() => {}} />, pessoal);
  fireEvent.click(screen.getByRole("button", { name: "Colar código" }));
  fireEvent.change(textoCodigo(), { target: { value: CODIGO } });
  fireEvent.click(screen.getByRole("button", { name: "Ler código" }));
  await waitFor(() => expect(responder).toBeDefined());
  fireEvent.click(screen.getByRole("button", { name: "Digitar conta" }));
  fireEvent.change(valor(), { target: { value: "42,00" } });
  await act(async () => responder(json(200, banco)));
  expect(valor().value).toBe("42,00");
  expect(valor().readOnly).toBe(false);
  expect(screen.queryByText(/Boleto bancário conferido/)).toBeNull();
});

test("rn22: editing the description keeps the original instrument and legacy date", async () => {
  const conta = contaBanco();
  renderComSessao(<ContaFolha conta={conta} open onClose={() => {}} />, pessoal);
  await screen.findByText(/Boleto bancário conferido/);
  expect((screen.getByRole("combobox", { name: "Vencimento" }) as HTMLSelectElement).value).toBe("2000-07-03");
  fireEvent.change(screen.getByLabelText("Descrição"), { target: { value: "Nome corrigido" } });
  fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
  await waitFor(() => expect(enviados).toHaveLength(1));
  expect(enviados[0]).toMatchObject({ descricao: "Nome corrigido", vencimento: "2000-07-03" });
  expect(enviados[0]).not.toHaveProperty("instrumento");
});

test.each(["criar", "editar"] as const)("rn22: pending %s cannot reset or send twice when entry changes or the form is submitted again", async (acao) => {
  let responder!: (resposta: Response) => void;
  salvarResposta = () => new Promise((resolve) => { responder = resolve; });
  const onClose = vi.fn();
  renderComSessao(<ContaFolha conta={acao === "editar" ? contaBanco() : undefined} open onClose={onClose} />, pessoal);
  if (acao === "criar") await ler();
  else await screen.findByText(/Boleto bancário conferido/);
  fireEvent.change(screen.getByLabelText("Descrição"), { target: { value: "Pagamento sem duplicata" } });
  fireEvent.click(screen.getByRole("button", { name: acao === "criar" ? "Salvar conta" : "Salvar" }));
  await waitFor(() => expect(enviados).toHaveLength(1));
  const entrada = textoCodigo();
  const botaoLer = screen.getByRole("button", { name: "Ler código" });
  fireEvent.click(screen.getByRole("button", { name: "Digitar conta" }));
  fireEvent.change(entrada, { target: { value: "outro código" } });
  fireEvent.click(botaoLer);
  await act(async () => fireEvent.submit(document.getElementById("conta-form")!));
  fireEvent(screen.getByRole("dialog"), new Event("cancel", { bubbles: true, cancelable: true }));
  expect(onClose).not.toHaveBeenCalled();
  expect(enviados).toHaveLength(1);
  expect(screen.getByRole("button", { name: "Colar código" }).getAttribute("aria-pressed")).toBe("true");
  expect((textoCodigo() as HTMLTextAreaElement).value).toBe(CODIGO);
  expect((screen.getByRole("button", { name: "Salvando…" }) as HTMLButtonElement).disabled).toBe(true);
  await act(async () => responder(json(201, { id: "l1", vencimento: "2000-07-03" })));
  await waitFor(() => expect(onClose).toHaveBeenCalledOnce());
  expect(enviados).toHaveLength(1);
  if (acao === "criar") expect(push).toHaveBeenCalledOnce();
});

test("rf08/rn22: a remote instrument refetch cannot replace the preview of a dirty local entry", async () => {
  const local: Leitura = { instrumento: { tipo: "pix", codigo: null, chave_pix: "local@exemplo.com", beneficiario: null }, valor_centavos: null, vencimento: null, vencimentos_possiveis: [], avisos: [] };
  const remoto: Leitura = { ...banco, instrumento: { ...banco.instrumento, codigo: "99999" } };
  const resultados = [banco, local, remoto];
  preview = vi.fn(async () => json(200, resultados.shift()));
  let refetch!: (nova: ContaDetalhe) => void;
  function Refetch() {
    const [conta, atualizar] = useState(contaBanco);
    refetch = atualizar;
    return <ContaFolha conta={conta} open onClose={() => {}} />;
  }
  renderComSessao(<Refetch />, pessoal);
  await screen.findByText(/Boleto bancário conferido/);
  fireEvent.click(screen.getByRole("button", { name: "Chave Pix" }));
  fireEvent.change(screen.getByLabelText("Chave Pix", { exact: true }), { target: { value: "local@exemplo.com" } });
  fireEvent.click(screen.getByRole("button", { name: "Conferir chave" }));
  await screen.findByText(/Pix conferido/);
  fireEvent.change(valor(), { target: { value: "42,00" } });
  fireEvent.change(screen.getByLabelText("Vencimento"), { target: { value: "2026-11-20" } });
  await act(async () => refetch({ ...contaBanco(), instrumento: remoto.instrumento }));
  expect(vi.mocked(preview)).toHaveBeenCalledTimes(2);
  expect(screen.queryByText(/Boleto bancário conferido/)).toBeNull();
  expect(screen.getByText(/Pix conferido/)).toBeTruthy();
  expect((screen.getByLabelText("Chave Pix", { exact: true }) as HTMLInputElement).value).toBe("local@exemplo.com");
  expect(valor().readOnly).toBe(false);
  expect(valor().value).toBe("42,00");
  fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
  await waitFor(() => expect(enviados).toHaveLength(1));
  expect(enviados[0]).toMatchObject({ instrumento: { chave_pix: "local@exemplo.com" }, valor_centavos: 4200, vencimento: "2026-11-20" });
});
