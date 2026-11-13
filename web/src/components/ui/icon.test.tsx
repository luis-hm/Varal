import { render } from "@testing-library/react";
import { expect, test } from "vitest";
import { Icon, iconNames } from "./icon";

test("ca03: the 29 Doop icons render a 24x24 svg with currentColor, hidden from AT", () => {
  expect(iconNames).toHaveLength(29);
  for (const name of iconNames) {
    const { container, unmount } = render(<Icon name={name} />);
    const svg = container.querySelector("svg")!;
    expect(svg.getAttribute("viewBox")).toBe("0 0 24 24");
    expect(svg.getAttribute("stroke")).toBe("currentColor");
    expect(svg.getAttribute("aria-hidden")).toBe("true");
    expect(svg.children.length).toBeGreaterThan(0);
    unmount();
  }
});

test("ca04: sizes match the Doop (sm 16, md 20, lg 24, xl 32)", () => {
  const cases = { sm: "16", md: "20", lg: "24", xl: "32" } as const;
  for (const [size, px] of Object.entries(cases)) {
    const { container, unmount } = render(<Icon name="sino" size={size as keyof typeof cases} />);
    const svg = container.querySelector("svg")!;
    expect([svg.getAttribute("width"), svg.getAttribute("height")]).toEqual([px, px]);
    unmount();
  }
});

test("an icon with a label is an image with that name", () => {
  const { getByRole } = render(<Icon name="sino" label="Avisos" />);
  expect(getByRole("img", { name: "Avisos" })).toBeTruthy();
});
