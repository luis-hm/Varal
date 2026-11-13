import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { Chip } from "./chip";

test("ca06: click calls onClick and aria-pressed follows state", () => {
  const onClick = vi.fn();
  const { rerender } = render(<Chip label="Vencidas" count={2} onClick={onClick} />);
  const chip = screen.getByRole("button", { name: "Vencidas 2" });
  expect(chip.getAttribute("aria-pressed")).toBe("false");
  fireEvent.click(chip);
  expect(onClick).toHaveBeenCalledOnce();
  rerender(<Chip state="on" label="Vencidas" count={2} onClick={onClick} />);
  expect(chip.getAttribute("aria-pressed")).toBe("true");
});

test("ca06: count is part of the text; without count only the label", () => {
  render(<Chip label="Todas" onClick={() => {}} />);
  expect(screen.getByRole("button").textContent).toBe("Todas");
});
