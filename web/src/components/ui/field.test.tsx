import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Field } from "./field";

test("ca07: the input is named by the label and described by the hint", () => {
  render(<Field label="Valor" hint="Lido do código de barras" defaultValue="R$ 287,43" />);
  const input = screen.getByRole("textbox", { name: "Valor" });
  const hint = document.getElementById(input.getAttribute("aria-describedby")!);
  expect(hint?.textContent).toBe("Lido do código de barras");
  expect(input.getAttribute("aria-invalid")).toBeNull();
});

test("ca07: error state sets aria-invalid and shows the message", () => {
  render(<Field label="Código" hint="47 ou 48 dígitos" error="Código incompleto" defaultValue="1234" />);
  const input = screen.getByRole("textbox", { name: "Código" });
  expect(input.getAttribute("aria-invalid")).toBe("true");
  expect(document.getElementById(input.getAttribute("aria-describedby")!)?.textContent).toBe(
    "Código incompleto",
  );
});

test("without hint there is no description", () => {
  render(<Field label="E-mail" placeholder="voce@email.com" />);
  expect(screen.getByRole("textbox", { name: "E-mail" }).getAttribute("aria-describedby")).toBeNull();
});
