import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { AVISO_VISIBILIDADE, ContaFolha } from "./conta-folha";
import { json, me, renderComSessao } from "./teste-sessao";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, refresh: vi.fn() }) }));

let criar: { status: number; body: unknown };
const enviados: unknown[] = [];

beforeEach(() => {
  document.cookie = "csrftoken=t";
  enviados.length = 0;
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
    if (url === "/api/grupos/g1/")
      return json(200, {
        id: "g1", nome: "Família", meu_papel: "admin", janela_alerta_dias: 3, casas: [{ id: "c1", nome: "Casa 1" }],
        membros: [
          { id: "m1", nome: "Dev", email: "dev@varal.local", papel: "admin", sou_eu: true },
          { id: "m2", usuario: "u2", nome: "Mãe", email: "mae@x", papel: "pagador", sou_eu: false },
          { id: "m3", usuario: "u3", nome: "Ana", email: "ana@x", papel: "observador", sou_eu: false },
        ],
      });
    if (url === "/api/espacos/g1/lancamentos/" && init?.method === "POST") {
      enviados.push(JSON.parse(String(init.body)));
      return json(criar.status, criar.body);
    }
    return json(404, { detail: "x" });
  }));
});
afterEach(() => vi.unstubAllGlobals());

// Waits for the mocked group (its payer chips). The fetch resolves at once, but the first render of the file
// pays the cold JSDOM/React Query start: under a loaded machine (full `make test`, parallel runs) it took
// 1.5–2s and broke the 1s default. 5s still fails fast if the group never loads.
const grupoCarregado = () => screen.findByRole("button", { name: "Mãe" }, { timeout: 5_000 });

function preencher() {
  fireEvent.change(screen.getByLabelText("Valor"), { target: { value: "287,43" } });
  fireEvent.change(screen.getByLabelText("Vencimento"), { target: { value: "2026-11-20" } });
  fireEvent.change(screen.getByLabelText("Descrição"), { target: { value: "Energia" } });
}

test("ca28: restricted bill with another payer warns before saving; observer is not a payer option", async () => {
  renderComSessao(<ContaFolha open onClose={() => {}} destino={{ espaco: "g1" }} />);
  const mae = await grupoCarregado();
  expect(screen.getByRole("button", { name: "Eu" }).getAttribute("aria-pressed")).toBe("true");
  expect(screen.queryByText(AVISO_VISIBILIDADE)).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Só algumas pessoas" }));
  expect(screen.queryByText(AVISO_VISIBILIDADE)).toBeNull(); // "Eu" pays
  fireEvent.click(mae);
  expect(screen.getByText(AVISO_VISIBILIDADE)).toBeTruthy();
  const quemPaga = screen.getByRole("group", { name: "Quem paga" });
  expect(quemPaga.textContent).not.toContain("Ana");
  expect(screen.getByRole("group", { name: "Quem mais vê" }).textContent).toContain("Ana");
  expect(enviados).toEqual([]); // shown before saving
});

test("q19b: the API's 400 message shows next to Quem vê and nothing navigates", async () => {
  const msg = "Você é a única pessoa que vê esta conta. Escolha outra pessoa antes de sair da lista.";
  criar = { status: 400, body: { acesso: [msg] } };
  renderComSessao(<ContaFolha open onClose={() => {}} destino={{ espaco: "g1" }} />);
  await grupoCarregado();
  preencher();
  fireEvent.click(screen.getByRole("button", { name: "Salvar conta" }));
  expect(await screen.findByText(msg)).toBeTruthy();
  expect(push).not.toHaveBeenCalled();
});

test("creating sends cents and opens the new bill in its group context", async () => {
  criar = { status: 201, body: { id: "n1", vencimento: "2026-11-20", espaco: { id: "g1", nome: "Família", tipo: "grupo" } } };
  renderComSessao(<ContaFolha open onClose={() => {}} destino={{ espaco: "g1" }} />);
  await grupoCarregado();
  preencher();
  fireEvent.click(screen.getByRole("button", { name: "Salvar conta" }));
  await waitFor(() => expect(push).toHaveBeenCalledWith("/contas/n1?espaco=g1"));
  expect(enviados[0]).toMatchObject({ valor_centavos: 28743, vencimento: "2026-11-20", descricao: "Energia", pagador: "u1", visibilidade: "grupo" });
});

test("PDF sem código permite conferir manualmente antes de vincular", async () => {
  const anterior = vi.mocked(fetch).getMockImplementation()!;
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (input === "/api/espacos/g1/boletos/pdf/" && init?.method === "POST") {
      expect(init.body).toBeInstanceOf(FormData);
      return json(202, { id: "pdf1", estado: "pendente", nome: "conta.pdf", tamanho: 5, resultado: {}, avisos: [] });
    }
    if (input === "/api/boletos/pdfs/pdf1/") return json(200, { id: "pdf1", estado: "conferencia_manual", nome: "conta.pdf", tamanho: 5, resultado: { candidatos: [], data_emissao: null, beneficiario: null }, avisos: ["Confira os dados manualmente."] });
    if (input === "/api/boletos/pdfs/pdf1/arquivo/") return json(200, { url: "http://storage.example/conta.pdf", expira_em: "2026-11-16T12:00:00Z" });
    return anterior(input, init);
  });
  criar = { status: 201, body: { id: "n1", vencimento: "2026-11-20", espaco: { id: "g1", nome: "Família", tipo: "grupo" } } };
  renderComSessao(<ContaFolha open onClose={() => {}} destino={{ espaco: "g1" }} />);
  await grupoCarregado();
  const file = new File(["%PDF-"], "conta.pdf", { type: "application/pdf" });
  fireEvent.change(screen.getByLabelText(/Escolha ou arraste/), { target: { files: [file] } });
  expect(await screen.findByText("Confira os dados manualmente.")).toBeTruthy();
  expect(screen.queryByTitle("Prévia do PDF")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Carregar prévia" }));
  expect((await screen.findByTitle("Prévia do PDF")).getAttribute("src")).toBe("http://storage.example/conta.pdf");
  expect(screen.getByRole("button", { name: "Abrir PDF em outra aba" })).toBeTruthy();
  preencher();
  fireEvent.click(screen.getByRole("button", { name: "Salvar conta" }));
  await waitFor(() => expect(enviados[0]).toMatchObject({ documento_pdf: "pdf1", valor_centavos: 28743, vencimento: "2026-11-20" }));
});

test("PDF com várias linhas exige escolha e informa acesso ao arquivo inteiro", async () => {
  const anterior = vi.mocked(fetch).getMockImplementation()!;
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (input === "/api/espacos/g1/boletos/pdf/" && init?.method === "POST") return json(202, { id: "pdf2", estado: "pendente", nome: "contas.pdf", tamanho: 5, resultado: {}, avisos: [] });
    if (input === "/api/boletos/pdfs/pdf2/") return json(200, { id: "pdf2", estado: "lido", nome: "contas.pdf", tamanho: 5, resultado: { candidatos: [{ codigo: "111" }, { codigo: "222" }] }, avisos: [] });
    return anterior(input, init);
  });
  renderComSessao(<ContaFolha open onClose={() => {}} destino={{ espaco: "g1" }} />);
  await grupoCarregado();
  fireEvent.change(screen.getByLabelText(/Escolha ou arraste/), { target: { files: [new File(["%PDF-"], "contas.pdf")] } });
  expect(await screen.findByText(/O arquivo inteiro ficará disponível/)).toBeTruthy();
  preencher();
  fireEvent.click(screen.getByRole("button", { name: "Salvar conta" }));
  expect(await screen.findAllByText("Escolha uma das linhas encontradas no PDF.")).not.toHaveLength(0);
  expect(enviados).toHaveLength(0);
});

// Ajuste 30: "Onde fica" starts on the space you are in, already selected.
function onde() {
  const chips = within(screen.getByRole("group", { name: /Onde fica/ })).getAllByRole("button");
  return chips.map((b) => `${b.textContent}${b.getAttribute("aria-pressed") === "true" ? "*" : ""}`);
}

test("COR-06: without a destination the bill is personal, even if the session points at a group", () => {
  renderComSessao(<ContaFolha open onClose={() => {}} />);
  expect(onde()).toEqual(["Pessoal*", "Família"]);
});

test("COR-06: opened from a group, that group comes first and selected; the others keep their order", async () => {
  const user = { ...me, grupos: [{ id: "g0", nome: "Trabalho", papel: "membro" as const }, ...me.grupos] };
  renderComSessao(<ContaFolha open onClose={() => {}} destino={{ espaco: "g1" }} />, undefined, user);
  expect(onde()).toEqual(["Família*", "Pessoal", "Trabalho"]);
  await grupoCarregado();
});

test("COR-06: opened from a group where you only observe, the order stays and the first is selected", () => {
  const user = { ...me, grupos: [...me.grupos, { id: "g2", nome: "Condomínio", papel: "observador" as const }] };
  renderComSessao(<ContaFolha open onClose={() => {}} destino={{ espaco: "g2" }} />, undefined, user);
  expect(onde()).toEqual(["Pessoal*", "Família"]);
});
