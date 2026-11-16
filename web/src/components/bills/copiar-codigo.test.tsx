import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { CopiarCodigo } from "./copiar-codigo";

afterEach(() => vi.unstubAllGlobals());

test("rf14: copying preserves the complete Pix payload and announces success", async () => {
  const codigo = "00020126330014br.gov.bcb.pix0111chave@x.com6304ABCD";
  const writeText = vi.fn().mockResolvedValue(undefined);
  vi.stubGlobal("navigator", { clipboard: { writeText } });
  render(<CopiarCodigo codigo={codigo} />);
  fireEvent.click(screen.getByRole("button", { name: "Copiar código" }));
  await waitFor(() => expect(screen.getByRole("status").textContent).toBe("Código copiado."));
  expect(writeText).toHaveBeenCalledWith(codigo);
});

test("rf14: denied clipboard exposes and selects the whole key for manual copying", async () => {
  const codigo = "familia@exemplo.com";
  vi.stubGlobal("navigator", { clipboard: { writeText: vi.fn().mockRejectedValue(new Error("denied")) } });
  render(<CopiarCodigo codigo={codigo} chave />);
  fireEvent.click(screen.getByRole("button", { name: "Copiar chave Pix" }));
  const campo = await screen.findByRole("textbox", { name: "Chave Pix para copiar manualmente" }) as HTMLTextAreaElement;
  expect(campo.value).toBe(codigo);
  await waitFor(() => {
    expect(document.activeElement).toBe(campo);
    expect(campo.selectionStart).toBe(0);
    expect(campo.selectionEnd).toBe(codigo.length);
  });
  expect(screen.getByRole("status").textContent).toBe("Selecione e copie o código abaixo.");
});
