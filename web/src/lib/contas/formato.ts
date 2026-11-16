// Money in cents, civil dates ("AAAA-MM-DD") and instants shown in America/Fortaleza (RNF11), all with Intl.
import type { Conta } from "./client";

export const FUSO = "America/Fortaleza";

const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
// Intl puts a no-break space after "R$"; the Doop copy uses a plain one.
export const reais = (centavos: number) => brl.format(centavos / 100).replace(/\s/g, " ");

/** An unknown amount is not zero and must remain identifiable in every account state. */
export const valorConta = (centavos: number | null) => centavos === null ? "Valor a definir" : reais(centavos);

/** Label a partial sum and the amount of missing values in the same visible universe. */
export function totalConhecido(centavos: number, indefinidos: number): string {
  return indefinidos ? `${reais(centavos)} · ${plural(indefinidos, "valor a definir", "valores a definir")}` : reais(centavos);
}

/** Hero number: "R$ 287" and ",43" (cents half size, .55 opacity in the Doop). */
export function partesReais(centavos: number): [string, string] {
  const texto = reais(centavos);
  const virgula = texto.lastIndexOf(",");
  return [texto.slice(0, virgula), texto.slice(virgula)];
}

/** "287,43", "1.200", "R$ 12,5" → cents; null when it is not a positive amount (RN11). */
export function lerValor(texto: string): number | null {
  const limpo = texto.replace(/[R$\s]/g, "");
  if (!/^\d{1,3}(\.?\d{3})*(,\d{1,2})?$/.test(limpo)) return null;
  const [inteiro, frac = ""] = limpo.replace(/\./g, "").split(",");
  const centavos = Number(inteiro) * 100 + Number(frac.padEnd(2, "0"));
  return centavos > 0 ? centavos : null;
}

/** Cents → "287,43" for an editable field. */
export const valorEditavel = (centavos: number) => reais(centavos).replace("R$ ", "");

/** Today in Fortaleza as "AAAA-MM-DD". */
export const hoje = (agora = new Date()) => new Intl.DateTimeFormat("en-CA", { timeZone: FUSO }).format(agora);
export const mesAtual = (agora = new Date()) => hoje(agora).slice(0, 7);

// Civil dates have no time zone: format them at UTC noon so no offset can move the day.
const civil = (data: string) => new Date(`${data}T12:00:00Z`);
const fmt = (opts: Intl.DateTimeFormatOptions) => new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC", ...opts });

/** "2026-11" → "novembro". */
export const nomeMes = (mes: string) => fmt({ month: "long" }).format(civil(`${mes}-01`));
/** "2026-11" → "Novembro 2026". */
export function mesAno(mes: string) {
  const nome = nomeMes(mes);
  return `${nome[0].toUpperCase()}${nome.slice(1)} ${mes.slice(0, 4)}`;
}
/** "2026-11" ± n months. */
export function somarMes(mes: string, n: number) {
  const [ano, m] = mes.split("-").map(Number);
  const d = new Date(Date.UTC(ano, m - 1 + n, 1));
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`;
}

/** "2026-11-14" → "14/11". */
export const diaMes = (data: string) => `${data.slice(8, 10)}/${data.slice(5, 7)}`;
/** Civil date, including its year; never convert it to an instant in Fortaleza. */
export const dataCivil = (data: string) => fmt({ day: "2-digit", month: "2-digit", year: "numeric" }).format(civil(data));
/** "2026-11-14" → "sex., 14/11". */
export const diaSemana = (data: string) => `${fmt({ weekday: "short" }).format(civil(data))}, ${diaMes(data)}`;

/** Instant (UTC ISO) → "11/11, 07:00" in Fortaleza. */
export const quando = (iso: string) =>
  new Intl.DateTimeFormat("pt-BR", { timeZone: FUSO, day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }).format(new Date(iso));

/** Instant → "01/11" in Fortaleza. */
export const dia = (iso: string) => new Intl.DateTimeFormat("pt-BR", { timeZone: FUSO, day: "2-digit", month: "2-digit" }).format(new Date(iso));

export function saudacao(agora = new Date()) {
  const hora = Number(new Intl.DateTimeFormat("en-GB", { timeZone: FUSO, hour: "2-digit", hourCycle: "h23" }).format(agora));
  return hora < 12 ? "Bom dia" : hora < 18 ? "Boa tarde" : "Boa noite";
}

export const plural = (n: number, um: string, varios: string) => `${n} ${n === 1 ? um : varios}`;

/** "em 2 dias", "amanhã", "hoje", "ontem", "há 5 dias". */
export function prazo(dias: number) {
  if (dias === 0) return "hoje";
  if (dias === 1) return "amanhã";
  if (dias === -1) return "ontem";
  return dias > 0 ? `em ${dias} dias` : `há ${-dias} dias`;
}

/** BillCard meta: "Vence 14/11 · Mãe paga", "Venceu 28/10 · Sem pagador" (CA17: the date, never a month label). */
export function metaConta(conta: Conta) {
  const vencida = conta.status_exibido === "vencida";
  const partes = [`${vencida ? "Venceu" : "Vence"} ${diaMes(conta.vencimento)}`];
  if (conta.espaco.tipo === "grupo") {
    partes.push(!conta.pagador ? "Sem pagador" : conta.pagador.sou_eu ? "Você paga" : `${conta.pagador.nome} paga`);
  }
  return partes.join(" · ");
}
