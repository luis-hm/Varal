import { fireEvent, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { PdfArquivo } from "./pdf-arquivo";
import { json, renderComSessao } from "./teste-sessao";

afterEach(() => vi.unstubAllGlobals());

test.each(["javascript:alert(1)", `${window.location.origin}/arquivo.html`, "blob:http://localhost/arquivo"])('prévia recusa URL insegura %s', async (url) => {
  vi.stubGlobal("fetch", vi.fn(async () => json(200, { url, expira_em: "2026-11-16T12:00:00Z" })));
  renderComSessao(<PdfArquivo arquivo={null} nome="conta.pdf" tamanho={10} documentoId="doc" ocupado={false} onEscolher={() => {}} />);
  fireEvent.click(screen.getByRole("button", { name: "Carregar prévia" }));
  expect((await screen.findByRole("alert")).textContent).toContain("Não foi possível abrir a prévia");
  expect(screen.queryByTitle("Prévia do PDF")).toBeNull();
});
