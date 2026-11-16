import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { AppShell } from "./app-shell";

let pathname = "/";
vi.mock("next/navigation", () => ({ usePathname: () => pathname, useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }));

// SideNav and TabBar both link "Contas"; the TabBar is the second one (the SideNav is hidden by CSS below 1024px).
const tabBar = () => screen.getAllByRole("link", { name: "Contas" }).length === 2;

test("ajuste 28: the bill detail (07) is a stacked screen without TabBar; the list keeps it", () => {
  pathname = "/contas/abc";
  const { container, unmount } = render(<AppShell>x</AppShell>);
  expect(tabBar()).toBe(false);
  expect(container.querySelector("[data-empilhada]")).toBeTruthy(); // no bottom room kept for the TabBar
  unmount();
  pathname = "/contas";
  render(<AppShell>x</AppShell>);
  expect(tabBar()).toBe(true);
});
