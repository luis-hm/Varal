import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import Home from "./page";

afterEach(() => vi.unstubAllGlobals());

function renderHome() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <Home />
    </QueryClientProvider>,
  );
}

test("shows the API health returned by /api/health/", async () => {
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "ok" })));
  vi.stubGlobal("fetch", fetchMock);
  renderHome();
  expect(screen.getByRole("heading", { name: "Início" })).toBeTruthy();
  expect(screen.getByText("Em breve")).toBeTruthy();
  expect(await screen.findByText("API: ok")).toBeTruthy();
  expect(fetchMock).toHaveBeenCalledWith("/api/health/");
});

test("shows unavailable when the API fails", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 500 })));
  renderHome();
  expect(await screen.findByText("API: indisponível")).toBeTruthy();
});
