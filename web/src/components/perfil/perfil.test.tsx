import { fireEvent, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import { renderComSessao } from "@/components/bills/teste-sessao";
import { ApiError } from "@/lib/grupos/client";
import { Perfil } from "./perfil";

const mocks = vi.hoisted(() => ({ nome: vi.fn(), refresh: vi.fn(), solicitar: vi.fn(), consultar: vi.fn(), baixar: vi.fn(), intencao: vi.fn(), excluir: vi.fn(), sessao: vi.fn(), senha: vi.fn(), emails: vi.fn(), codigo: vi.fn() }));
vi.mock("@/components/notifications/avisos", () => ({ Preferencias: () => <div>Preferências</div> }));
vi.mock("@/components/auth/logout-button", () => ({ LogoutButton: () => <button>Sair</button> }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: mocks.refresh }) }));
vi.mock("@/lib/perfil/client", () => ({ editarNome: mocks.nome, solicitarExportacao: mocks.solicitar, consultarExportacao: mocks.consultar, baixarExportacao: mocks.baixar, criarIntencao: mocks.intencao, excluirConta: mocks.excluir }));
vi.mock("@/lib/auth/client", async (original) => ({ ...await original<typeof import("@/lib/auth/client")>(), sessaoAtual: mocks.sessao, reautenticarSenha: mocks.senha, emailsProprios: mocks.emails, solicitarCodigoReauth: mocks.codigo }));
beforeEach(() => { vi.clearAllMocks(); });

test("reauth de exportação exige confirmação e repete a mesma chave após falha", async () => {
  mocks.solicitar.mockRejectedValueOnce(new ApiError(401, undefined, { code: "reauth_required", meta: { is_authenticated: true }, status: 401 })).mockResolvedValueOnce({ id: "e1", estado: "pronto", expira_em: "2030-01-01T00:00:00Z" });
  mocks.sessao.mockResolvedValue({ data: { user: { has_usable_password: true } } });
  mocks.senha.mockResolvedValue({});
  renderComSessao(<Perfil />);
  fireEvent.click(screen.getByRole("button", { name: "Preparar exportação" }));
  fireEvent.change(await screen.findByLabelText("Senha"), { target: { value: "senha" } });
  fireEvent.click(screen.getByRole("button", { name: "Confirmar identidade" }));
  await screen.findByText("Identidade confirmada. Continue a ação solicitada.");
  expect(mocks.solicitar).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("button", { name: "Preparar exportação" }));
  await screen.findByRole("button", { name: "Baixar exportação" });
  expect(mocks.solicitar.mock.calls[0][0]).toEqual(mocks.solicitar.mock.calls[1][0]);
});

test("sessão expirada não é confundida com solicitação de nova prova", async () => {
  mocks.solicitar.mockRejectedValueOnce(new ApiError(401, undefined, { meta: { is_authenticated: false }, status: 401 }));
  renderComSessao(<Perfil />);
  fireEvent.click(screen.getByRole("button", { name: "Preparar exportação" }));
  expect((await screen.findByRole("alert")).textContent).toContain("Sua sessão expirou");
  await waitFor(() => expect(mocks.sessao).not.toHaveBeenCalled());
});


test("conflito de exclusão mantém a sessão e a intenção sem afirmar sucesso", async () => {
  mocks.intencao.mockResolvedValue({ id: "i1", segredo: "segredo", expira_em: "2030-01-01T00:00:00Z" });
  mocks.excluir.mockRejectedValue(new ApiError(409));
  renderComSessao(<Perfil />);
  fireEvent.click(screen.getByRole("button", { name: "Preparar exclusão" }));
  fireEvent.click(await screen.findByRole("checkbox", { name: "Quero excluir minha conta" }));
  fireEvent.click(screen.getByRole("button", { name: "Confirmar exclusão" }));
  await screen.findByRole("alert");
  expect(mocks.excluir).toHaveBeenCalledWith({ id: "i1", segredo: "segredo", confirmar: true });
  expect(screen.getByRole("checkbox", { name: "Quero excluir minha conta" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Sair" })).toBeTruthy();
});


test("usuário sem senha solicita código para endereço próprio verificado", async () => {
  mocks.solicitar.mockRejectedValueOnce(new ApiError(401, undefined, { code: "reauth_required", meta: { is_authenticated: true }, status: 401 }));
  mocks.sessao.mockResolvedValue({ data: { user: { has_usable_password: false } } });
  mocks.emails.mockResolvedValue({ data: [{ email: "principal@example.test", primary: true, verified: false }, { email: "verificado@example.test", primary: false, verified: true }] });
  mocks.codigo.mockResolvedValue({});
  renderComSessao(<Perfil />);
  fireEvent.click(screen.getByRole("button", { name: "Preparar exportação" }));
  fireEvent.click(await screen.findByRole("button", { name: "Enviar código" }));
  await screen.findByLabelText("Código de confirmação");
  expect(mocks.codigo).toHaveBeenCalledWith({ email: "verificado@example.test" });
  expect(mocks.solicitar).toHaveBeenCalledTimes(1);
});


test("exportação pendente consulta estado e só oferece download quando pronta", async () => {
  const item = { id: "e2", expira_em: "2030-01-01T00:00:00Z" };
  mocks.solicitar.mockResolvedValueOnce({ ...item, estado: "pendente" });
  mocks.consultar.mockResolvedValueOnce({ ...item, estado: "pronto" });
  renderComSessao(<Perfil />);
  fireEvent.click(screen.getByRole("button", { name: "Preparar exportação" }));
  await screen.findByRole("button", { name: "Baixar exportação" });
  expect(mocks.consultar).toHaveBeenCalledWith("e2");
});

test("q12-2: nome é editado no próprio cartão, salva, atualiza a sessão e pode ficar em branco", async () => {
  mocks.nome.mockResolvedValue({});
  renderComSessao(<Perfil />);
  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Dev Martins");
  fireEvent.click(screen.getByRole("button", { name: "Editar nome" }));
  const campo = screen.getByLabelText("Nome") as HTMLInputElement;
  expect(campo.value).toBe("Dev Martins");
  fireEvent.change(campo, { target: { value: "" } });
  fireEvent.click(screen.getByRole("button", { name: "Salvar nome" }));
  await screen.findByText("Nome salvo.");
  expect(mocks.nome).toHaveBeenCalledWith({ nome: "" });
  expect(mocks.refresh).toHaveBeenCalled();
  expect(screen.queryByLabelText("Nome")).toBeNull();
});

test("q12-2: cancelar descarta o rascunho e erro de salvar mantém a edição", async () => {
  mocks.nome.mockRejectedValue(new ApiError(429));
  renderComSessao(<Perfil />);
  fireEvent.click(screen.getByRole("button", { name: "Editar nome" }));
  fireEvent.change(screen.getByLabelText("Nome"), { target: { value: "Outro" } });
  fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
  expect(mocks.nome).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Editar nome" }));
  expect((screen.getByLabelText("Nome") as HTMLInputElement).value).toBe("Dev Martins");
  fireEvent.click(screen.getByRole("button", { name: "Salvar nome" }));
  expect((await screen.findByRole("alert")).textContent).toContain("Muitas tentativas");
  expect(screen.getByLabelText("Nome")).toBeTruthy();
  expect(mocks.refresh).not.toHaveBeenCalled();
});
