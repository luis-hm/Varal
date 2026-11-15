import { request } from "@playwright/test";
import { createAccount, ORIGIN } from "./fixtures";

// P8: on a cold API the two workers' first signups race for allauth's rate-limit lock (1 s wait)
// while the dev server is still importing modules, and one gets 429. One signup alone warms that path.
export default async function globalSetup() {
  const context = await request.newContext({ baseURL: ORIGIN });
  await createAccount(context);
  await context.dispose();
}
