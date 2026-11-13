import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { expect, test } from "vitest";

const src = path.resolve(__dirname, "..");
const tokensCss = readFileSync(path.join(__dirname, "tokens.css"), "utf8");
const color = (name: string) => tokensCss.match(new RegExp(`--color-${name}:\\s*(#[0-9A-Fa-f]{6});`))![1];

function luminance(hex: string) {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(fg: string, bg: string) {
  const [a, b] = [luminance(color(fg)), luminance(color(bg))].sort((x, y) => y - x);
  return (a + 0.05) / (b + 0.05);
}

test("ca09/rnf09: badge and main text pairs reach 4.5:1", () => {
  const pairs: [string, string][] = [
    ["ink-muted", "neutral-soft"], // pendente
    ["ink-muted", "bg"], // aguardando (transparent badge on the app background)
    ["ink-muted", "surface"], // aguardando on a card, cancelada
    ["amber-text", "amber-soft"], // vence
    ["red-text", "red-soft"], // vencida
    ["green-text", "green-soft"], // paga, confirmada
    ["ink", "bg"], // main text
    ["ink", "surface"],
    ["surface", "ink"], // primary button
    ["surface", "green-text"], // success button
    ["red-text", "surface"], // danger button
  ];
  for (const [fg, bg] of pairs) expect(contrast(fg, bg), `${fg} on ${bg}`).toBeGreaterThanOrEqual(4.5);
});

function files(dir: string): string[] {
  return readdirSync(dir, { recursive: true, encoding: "utf8" }).map((f) => path.join(dir, f));
}

test("ca01: no hex colour in src outside tokens.css and the favicon", () => {
  const allowed = [path.join(__dirname, "tokens.css"), path.join(src, "app", "icon.svg")];
  const offenders = files(src)
    .filter((f) => /\.(css|tsx?|svg)$/.test(f) && !allowed.includes(f) && !f.endsWith(".test.ts"))
    .filter((f) => /#[0-9A-Fa-f]{3,8}\b/.test(readFileSync(f, "utf8")));
  expect(offenders).toEqual([]);
});

test("ca01: CSS modules take colour, shadow, font size and line height from var(--…)", () => {
  const rule = /\b(color|background|border(?:-color)?|box-shadow|font-size|line-height):\s*([^;]+);/g;
  const offenders: string[] = [];
  for (const f of files(src).filter((f) => f.endsWith(".module.css"))) {
    for (const [, prop, value] of readFileSync(f, "utf8").matchAll(rule)) {
      const bad =
        prop === "font-size" || prop === "line-height" || prop === "box-shadow"
          ? !/^var\(--/.test(value) && value !== "none"
          : /#[0-9a-f]{3,8}\b|rgba?\(|hsla?\(/i.test(value);
      if (bad) offenders.push(`${path.relative(src, f)}: ${prop}: ${value}`);
    }
  }
  expect(offenders).toEqual([]);
});

test("ca01: the Doop block holds the get_tokens values, incl. --text-4xl and no --spacing-7", () => {
  expect(tokensCss).toContain("--text-4xl: 64px;");
  expect(tokensCss).not.toContain("--spacing-7");
  expect(color("ink")).toBe("#1C2541");
});
