import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { TopBar } from "./top-bar";

test("ca10: the title is a heading and the action sits in the slot", () => {
  render(<TopBar title="Avisos" backHref="/" action={<button aria-label="Filtrar">f</button>} />);
  expect(screen.getByRole("heading", { level: 1, name: "Avisos" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Filtrar" })).toBeTruthy();
  expect(screen.getByRole("link", { name: "Voltar" }).getAttribute("href")).toBe("/");
});

test("without backHref there is no back link", () => {
  render(<TopBar title="Contas" />);
  expect(screen.queryByRole("link")).toBeNull();
});
