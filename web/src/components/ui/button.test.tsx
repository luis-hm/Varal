import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { Button } from "./button";

const tones = ["primary", "secondary", "ghost", "success", "danger"] as const;

test("ca05: every tone is a real <button> of type button", () => {
  for (const tone of tones) {
    const { unmount } = render(<Button tone={tone} label="Copiar código" />);
    const btn = screen.getByRole("button", { name: "Copiar código" });
    expect(btn.tagName).toBe("BUTTON");
    expect(btn.getAttribute("type")).toBe("button");
    expect(btn.dataset.tone).toBe(tone);
    unmount();
  }
});

test("ca05: width full is exposed for the full-width style", () => {
  render(<Button width="full" label="Entrar" />);
  expect(screen.getByRole("button").dataset.width).toBe("full");
});

test("ca05: icon-only button is named by aria-label and the icon is hidden", () => {
  render(<Button tone="ghost" icon="copiar" aria-label="Copiar código" />);
  const btn = screen.getByRole("button", { name: "Copiar código" });
  expect(btn.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
});

test("forwards clicks", () => {
  const onClick = vi.fn();
  render(<Button label="Já paguei" tone="success" onClick={onClick} />);
  fireEvent.click(screen.getByRole("button"));
  expect(onClick).toHaveBeenCalledOnce();
});

test("ca05/d1: the button is 52px tall in every tone (no tone overrides the height)", async () => {
  const { readFileSync } = await import("node:fs");
  const css = readFileSync(`${__dirname}/button.module.css`, "utf8");
  expect(css.match(/height:\s*([^;]+);/g)).toEqual(["height: 52px;"]);
});

test("ca05: an icon-only button without aria-label does not typecheck", () => {
  // @ts-expect-error icon-only buttons must name themselves
  render(<Button icon="copiar" />);
  expect(screen.getByRole("button")).toBeTruthy();
});
