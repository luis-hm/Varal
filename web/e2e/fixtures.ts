import { randomUUID } from "node:crypto";
import { expect, test as base, type APIRequestContext } from "@playwright/test";
import type { components } from "../src/types/api";

export const ORIGIN = "http://localhost:3000";
export const AUTH = "/api/auth/browser/v1/";
// Public, disposable development accounts. No personal credentials are used by this suite.
export const TEST_PASSWORD = "Varal-e2e!93-Linha";
export const uniqueEmail = () => `e2e-${randomUUID()}@varal.test`;
type StorageState = Awaited<ReturnType<APIRequestContext["storageState"]>>;

export async function csrf(request: APIRequestContext) {
  const response = await request.get(`${AUTH}config`);
  expect(response.status()).toBe(200);
  const state = await request.storageState();
  const token = state.cookies.find((cookie) => cookie.name === "csrftoken")?.value;
  expect(token, "GET config must bootstrap the browser CSRF cookie").toBeTruthy();
  return token!;
}

export async function createAccount(request: APIRequestContext, email = uniqueEmail()) {
  const response = await request.post(`${AUTH}auth/signup`, {
    headers: { Origin: ORIGIN, "X-CSRFToken": await csrf(request) },
    data: { email, password: TEST_PASSWORD },
  });
  expect(response.status(), await response.text()).toBe(200);
  return email;
}

export async function me(request: APIRequestContext) {
  const response = await request.get("/api/me/");
  expect(response.status()).toBe(200);
  return (await response.json()) as components["schemas"]["Me"];
}

// The design-system suite needs a real server session. Create one per worker,
// then copy its cookies into isolated browser contexts; those tests never log out.
export const test = base.extend<object, { signedInState: StorageState }>({
  signedInState: [async ({ playwright }, provide) => {
    const request = await playwright.request.newContext({ baseURL: ORIGIN });
    try {
      await createAccount(request);
      await provide(await request.storageState());
    } finally {
      await request.dispose();
    }
  }, { scope: "worker" }],
  storageState: async ({ signedInState }, provide) => provide(signedInState),
});

export { expect };
