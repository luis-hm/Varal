import type { components, operations } from "@/types/api";
import { call } from "@/lib/grupos/client";

type S = components["schemas"];
export type Conta = S["Conta"];
export type ContaDetalhe = S["ContaDetalhe"];
export type ContaEntrada = S["ContaEntrada"];
export type Historico = S["Historico"];
export type Lista = S["Lista"];
export type Resumo = S["Resumo"];
export type StatusExibido = S["StatusExibidoEnum"];
export type Filtros = NonNullable<operations["lancamentos_listar"]["parameters"]["query"]>;
export type FiltroStatus = NonNullable<Filtros["status"]>;
export type InstrumentoEntrada = S["InstrumentoEntrada"];
export type Leitura = S["Leitura"];
export type DocumentoPDF = S["DocumentoPDF"];

const e = (id: string, rest: string) => `espacos/${encodeURIComponent(id)}/${rest}`;
const l = (id: string, rest = "") => `lancamentos/${encodeURIComponent(id)}/${rest}`;

export function listarContas(espacoId: string, filtros: Filtros) {
  const query = new URLSearchParams(Object.entries(filtros).filter((kv): kv is [string, string] => !!kv[1]));
  return call<Lista>(`${e(espacoId, "lancamentos/")}${query.size ? `?${query}` : ""}`);
}
export const verResumo = (espacoId: string) => call<Resumo>(e(espacoId, "resumo/"));
export const criarConta = (espacoId: string, body: ContaEntrada) => call<ContaDetalhe>(e(espacoId, "lancamentos/"), "POST", body);
export const verConta = (id: string) => call<ContaDetalhe>(l(id));
export const editarConta = (id: string, body: S["PatchedContaEntrada"]) => call<ContaDetalhe>(l(id), "PATCH", body);
export const cancelarConta = (id: string) => call<ContaDetalhe>(l(id, "cancelar/"), "POST");
export const lerInstrumento = (body: InstrumentoEntrada) => call<Leitura>("boletos/ler/", "POST", body);
export function enviarPdf(espaco: string, arquivo: File, lancamentoId?: string) {
  const dados = new FormData();
  dados.append("arquivo", arquivo);
  if (lancamentoId) dados.append("lancamento_id", lancamentoId);
  return call<DocumentoPDF>(e(espaco, "boletos/pdf/"), "POST", dados);
}
export const verPdf = (id: string) => call<DocumentoPDF>(`boletos/pdfs/${encodeURIComponent(id)}/`);
export const linkPdf = (id: string) => call<S["URLPDF"]>(`boletos/pdfs/${encodeURIComponent(id)}/arquivo/`);
export const linkPdfConta = (id: string) => call<S["URLPDF"]>(l(id, "pdf/"));
