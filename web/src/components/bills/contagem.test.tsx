import { act } from "@testing-library/react";
import { hydrateRoot } from "react-dom/client";
import { renderToString } from "react-dom/server";
import { afterEach, expect, test, vi } from "vitest";
import { useContagem } from "./contagem";

afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

test("hidrata o valor do servidor com movimento reduzido e conclui no próximo quadro", async () => {
  function Contador() { return <span>{useContagem(491)}</span>; }
  vi.stubGlobal("matchMedia", undefined);
  const html = renderToString(<Contador />);
  expect(html).toBe("<span>0</span>");

  let quadro: FrameRequestCallback | undefined;
  vi.stubGlobal("matchMedia", () => ({ matches: true }));
  vi.stubGlobal("requestAnimationFrame", (fn: FrameRequestCallback) => { quadro = fn; return 1; });
  vi.stubGlobal("cancelAnimationFrame", () => {});
  const recuperavel = vi.fn();
  const consoleErro = vi.spyOn(console, "error").mockImplementation(() => {});
  const container = document.createElement("div");
  container.innerHTML = html;
  document.body.appendChild(container);
  let raiz!: ReturnType<typeof hydrateRoot>;
  await act(async () => { raiz = hydrateRoot(container, <Contador />, { onRecoverableError: recuperavel }); });
  expect(container.textContent).toBe("0");
  expect(recuperavel).not.toHaveBeenCalled();
  expect(consoleErro).not.toHaveBeenCalled();
  expect(quadro).toBeDefined();
  act(() => quadro!(0));
  expect(container.textContent).toBe("491");
  expect(recuperavel).not.toHaveBeenCalled();
  await act(async () => raiz.unmount());
  container.remove();
});
