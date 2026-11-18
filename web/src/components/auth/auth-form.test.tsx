import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { AuthForm } from "./auth-form";

const reply = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const config = { status: 200, data: { account: {}, socialaccount: { providers: [] } } };
beforeEach(() => { document.cookie = "csrftoken=test-token; path=/"; });
afterEach(() => { vi.unstubAllGlobals(); document.cookie = "csrftoken=; max-age=0; path=/"; });

function show(mode: "login" | "signup" | "request" | "reset", resetKey?: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><AuthForm mode={mode} resetKey={resetKey} /></QueryClientProvider>);
}

test("ca02/ca14: API validation is associated with its labelled field and announced", async () => {
  vi.stubGlobal("fetch", vi.fn().mockImplementation((url) => Promise.resolve(String(url).endsWith("config") ? reply(config) : reply({ status: 400, errors: [{ param: "email", code: "email_taken", message: "Este e-mail já está cadastrado." }] }, 400))));
  show("signup");
  fireEvent.change(screen.getByLabelText("E-mail"), { target: { value: "ana@example.com" } });
  fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "valid-password-test" } });
  fireEvent.submit(screen.getByRole("form", { name: "Criar conta" }));
  await screen.findByText("Este e-mail já está cadastrado.");
  expect(screen.getByLabelText("E-mail").getAttribute("aria-invalid")).toBe("true");
  expect(screen.getByLabelText("E-mail").getAttribute("aria-describedby")).toBeTruthy();
  expect(screen.getByRole("alert").textContent).toBe("Confira os campos indicados.");
  // CU01: e-mail already registered offers signing in or recovering the password.
  expect(screen.getAllByRole("link", { name: "Entrar" }).length).toBe(2);
  expect(screen.getByRole("link", { name: "recuperar a senha" }).getAttribute("href")).toBe("/recuperar-senha");
});

test("ca07: recovery confirms the same generic message without exposing whether the account exists", async () => {
  vi.stubGlobal("fetch", vi.fn().mockImplementation((url) => Promise.resolve(String(url).endsWith("config") ? reply(config) : reply({ status: 200 }))));
  show("request");
  fireEvent.change(screen.getByLabelText("E-mail"), { target: { value: "unknown@example.com" } });
  fireEvent.submit(screen.getByRole("form", { name: "Recuperar senha" }));
  expect(await screen.findByRole("status")).toHaveProperty("textContent", "Se houver uma conta com esse e-mail, você receberá um link para criar uma nova senha.");
  expect(screen.queryByRole("button", { name: "Enviar link" })).toBeNull();
});

test("ca08: an expired recovery key does not expose a usable password form", async () => {
  vi.stubGlobal("fetch", vi.fn().mockImplementation((url) => Promise.resolve(String(url).endsWith("config") ? reply(config) : reply({ status: 400, errors: [{ code: "invalid", message: "Invalid key" }] }, 400))));
  show("reset", "expired-key");
  await screen.findByText("Este link é inválido ou expirou. Solicite um novo link para recuperar sua senha.");
  expect(screen.queryByLabelText("Nova senha")).toBeNull();
  expect(screen.getByRole("link", { name: "Solicitar novo link" })).toBeTruthy();
});

test("ca12: unavailable Google explains the alternative without attempting an invalid provider handshake", async () => {
  const fetchMock = vi.fn().mockResolvedValue(reply(config));
  vi.stubGlobal("fetch", fetchMock);
  show("login");
  await waitFor(() => expect(screen.getByRole("button", { name: "Continuar com Google" }).hasAttribute("disabled")).toBe(false));
  fireEvent.click(screen.getByRole("button", { name: "Continuar com Google" }));
  expect(await screen.findByRole("status")).toHaveProperty("textContent", "O login com Google está indisponível no momento. Use seu e-mail para entrar ou criar uma conta.");
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test("ca08: a consumed recovery key keeps the successful password-change message", async () => {
  let consumed = false;
  vi.stubGlobal("fetch", vi.fn().mockImplementation((url, init?: RequestInit) => {
    if (String(url).endsWith("config")) return Promise.resolve(reply(config));
    if (init?.method === "POST") {
      consumed = true;
      return Promise.resolve(reply({ status: 401, meta: { is_authenticated: false }, data: { flows: [{ id: "login" }] } }, 401));
    }
    return Promise.resolve(consumed
      ? reply({ status: 400, errors: [{ code: "invalid", message: "Invalid key" }] }, 400)
      : reply({ status: 200, data: { email: "ana@example.com" } }));
  }));
  show("reset", "valid-key");
  await waitFor(() => expect(screen.getByRole("button", { name: "Salvar nova senha" }).hasAttribute("disabled")).toBe(false));
  fireEvent.change(screen.getByLabelText("Nova senha", { selector: "input" }), { target: { value: "new-valid-password-test" } });
  fireEvent.submit(screen.getByRole("form", { name: "Nova senha" }));
  await screen.findByText("Senha alterada. Entre com sua nova senha.");
  await waitFor(() => expect(screen.queryByText("Este link é inválido ou expirou. Solicite um novo link para recuperar sua senha.")).toBeNull());
  expect(screen.queryByLabelText("Nova senha", { selector: "input" })).toBeNull();
  expect(screen.getByRole("link", { name: "Voltar para Entrar" })).toBeTruthy();
});

test("sessão legada autenticada permite nova entrada explícita após logout cercado", async () => {
  const anterior = "00000000-0000-4000-8000-000000000001";
  let logins = 0;
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.endsWith("config")) return reply(config);
    if (url.endsWith("auth/login")) return ++logins === 1 ? reply({ status: 409 }, 409) : reply({ status: 400, errors: [{ message: "Resposta de teste." }] }, 400);
    if (url.endsWith("auth/session") && init?.method === "DELETE") return new Response(JSON.stringify({ status: 401, meta: { is_authenticated: false }, data: { flows: [] } }), { status: 401, headers: { "X-Varal-Identidade": anterior } });
    if (url.endsWith("auth/session")) return reply({ status: 200, meta: { is_authenticated: true }, data: { user: { id: anterior } } });
    return reply({}, 500);
  });
  vi.stubGlobal("fetch", fetchMock);
  show("login");
  fireEvent.change(screen.getByLabelText("E-mail"), { target: { value: "nova@example.com" } });
  fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "senha-teste" } });
  fireEvent.submit(screen.getByRole("form", { name: "Entrar" }));
  await screen.findByText("Resposta de teste.");
  const saida = fetchMock.mock.calls.find(([url, init]) => url.endsWith("auth/session") && init?.method === "DELETE");
  expect(saida?.[1]?.headers).toMatchObject({ "X-Varal-Identidade-Esperada": anterior });
  expect(logins).toBe(2);
  expect(document.cookie).not.toContain(`varal_owner=${anterior}`);
});

test("tentativa substituída não encerra sessão após consulta legada tardia", async () => {
  const { iniciarAutenticacao } = await import("@/lib/auth/isolamento");
  let resolver!: (value: Response) => void;
  const fetchMock = vi.fn((url: string) => {
    if (url.endsWith("config")) return Promise.resolve(reply(config));
    if (url.endsWith("auth/login")) return Promise.resolve(reply({ status: 409 }, 409));
    if (url.endsWith("auth/session")) return new Promise<Response>((resolve) => { resolver = resolve; });
    return Promise.resolve(reply({}, 500));
  });
  vi.stubGlobal("fetch", fetchMock);
  show("login");
  fireEvent.change(screen.getByLabelText("E-mail"), { target: { value: "nova@example.com" } });
  fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "senha-teste" } });
  fireEvent.submit(screen.getByRole("form", { name: "Entrar" }));
  await waitFor(() => expect(resolver).toBeDefined());
  expect(screen.getByRole("form", { name: "Entrar" }).getAttribute("aria-busy")).toBe("true");
  fireEvent.submit(screen.getByRole("form", { name: "Entrar" }));
  iniciarAutenticacao();
  resolver(reply({ status: 200, meta: { is_authenticated: true }, data: { user: { id: "00000000-0000-4000-8000-000000000001" } } }));
  await waitFor(() => expect(screen.getByRole("form", { name: "Entrar" }).getAttribute("aria-busy")).toBe("false"));
  expect(fetchMock.mock.calls.filter(([url]) => url.endsWith("auth/login"))).toHaveLength(1);
  expect(fetchMock.mock.calls.filter(([url]) => url.endsWith("auth/session"))).toHaveLength(1);
});
