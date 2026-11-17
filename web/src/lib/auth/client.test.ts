import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { AuthError, getAuthConfig, login, logout, resetPassword, validateResetKey } from "./client";

beforeEach(() => { document.cookie = "csrftoken=initial; path=/"; });
afterEach(() => { vi.unstubAllGlobals(); document.cookie = "csrftoken=; max-age=0; path=/"; });

const reply = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const unauthenticated = { status: 401, meta: { is_authenticated: false }, data: { flows: [{ id: "login" }] } };

test("ca11: mutations read the rotated CSRF cookie on every request and keep cookies same-origin", async () => {
  const fetchMock = vi.fn().mockResolvedValue(reply({ status: 200, meta: { is_authenticated: true }, data: {} }));
  vi.stubGlobal("fetch", fetchMock);
  await login({ email: "ana@example.com", password: "password-test" });
  document.cookie = "csrftoken=rotated; path=/";
  await login({ email: "ana@example.com", password: "password-test" });
  expect(fetchMock.mock.calls[0][1]).toMatchObject({ credentials: "same-origin", cache: "no-store", headers: { "X-CSRFToken": "initial" } });
  expect(fetchMock.mock.calls[1][1]).toMatchObject({ headers: { "X-CSRFToken": "rotated" } });
  expect(fetchMock.mock.calls[0][0]).toBe("/api/auth/browser/v1/auth/login");
});

test("ca09: logout accepts only allauth's confirmed unauthenticated 401 payload", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(reply(unauthenticated, 401)));
  expect(await logout("00000000-0000-4000-8000-000000000001")).toEqual(unauthenticated);
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(reply({ detail: "Unauthorized" }, 401)));
  await expect(logout("00000000-0000-4000-8000-000000000001")).rejects.toBeInstanceOf(AuthError);
});

test("ca08: password reset accepts the native success-without-login response and preserves field errors", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(reply(unauthenticated, 401)));
  expect(await resetPassword({ key: "test-key", password: "new-password-test" })).toEqual(unauthenticated);
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(reply({ status: 400, errors: [{ code: "invalid", param: "key", message: "Link inválido." }] }, 400)));
  await expect(resetPassword({ key: "bad-key", password: "new-password-test" })).rejects.toMatchObject({ status: 400, issues: [{ param: "key", message: "Link inválido." }] });
});

test("ca08: reset key is sent in its contract header rather than URL or persistent storage", async () => {
  const fetchMock = vi.fn().mockResolvedValue(reply({ status: 200, data: {} }));
  vi.stubGlobal("fetch", fetchMock);
  await validateResetKey("private-reset-key");
  expect(fetchMock).toHaveBeenCalledWith("/api/auth/browser/v1/auth/password/reset", expect.objectContaining({ headers: { "X-Password-Reset-Key": "private-reset-key" }, cache: "no-store" }));
  expect(localStorage.length).toBe(0);
  expect(sessionStorage.length).toBe(0);
});

test("ca12: configuration failures remain recoverable errors", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("Unavailable", { status: 503 })));
  await expect(getAuthConfig()).rejects.toMatchObject({ status: 503 });
});
