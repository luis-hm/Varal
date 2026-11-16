// RN22 history lines. Decision 8: automatic actions have no author and never read as "Ex-membro";
// a deleted author does (RN30, the API sends "Ex-membro").
import type { Historico } from "./client";
import { reais } from "./formato";

/** A piece of a history line: plain text or a person's name, shown on one line (ajuste 29). */
export type Trecho = string | { nome: string };
const nome = (v: string): Trecho => ({ nome: v });
/** The line as plain text. */
export const texto = (t: Trecho[]) => t.map((x) => (typeof x === "string" ? x : x.nome)).join("");

const campos: Record<string, string> = {
  descricao: "descrição",
  valor_centavos: "valor",
  vencimento: "vencimento",
  subgrupo: "casa",
  pagador: "quem paga",
  visibilidade: "quem vê",
  acesso: "quem mais vê",
  instrumento: "forma de pagamento",
};

function valor(campo: string, v: unknown): Trecho[] {
  if (v === null || v === undefined || (Array.isArray(v) && !v.length)) {
    return [campo === "subgrupo" ? "sem casa" : "ninguém"];
  }
  if (campo === "valor_centavos") return [reais(Number(v))];
  if (campo === "vencimento") return [String(v).split("-").reverse().join("/")];
  if (campo === "visibilidade") return [v === "restrita" ? "só algumas pessoas" : "todo o grupo"];
  if (campo === "instrumento") return [{ manual: "sem código", boleto_bancario: "boleto bancário", boleto_arrecadacao: "boleto de arrecadação", pix: "Pix" }[String(v)] ?? "código"];
  // People: "quem paga" and "quem mais vê" hold names.
  const pessoas = campo === "pagador" || campo === "acesso";
  return (Array.isArray(v) ? v : [v]).flatMap((x, i) => [...(i ? [", "] : []), pessoas ? nome(String(x)) : String(x)]);
}

function mudancas(dados: Historico["dados"]): Trecho[] {
  const camposAlterados = Object.entries(dados)
    .filter(([campo, par]) => campo in campos && Array.isArray(par) && par.length === 2)
    .flatMap(([campo, par], i) => [
      ...(i ? [" · "] : []),
      `${campos[campo]}: `,
      ...valor(campo, (par as unknown[])[0]),
      " → ",
      ...valor(campo, (par as unknown[])[1]),
    ]);
  return [...camposAlterados, ...(dados.codigo_alterado ? [...(camposAlterados.length ? [" · "] : []), "código de pagamento atualizado"] : [])];
}

/** [bold part, detail] of one history line. */
export function linhaHistorico(h: Historico): [Trecho[], Trecho[]] {
  const quem = nome(h.sou_eu ? "Você" : (h.autor ?? ""));
  const naSaida = h.dados.motivo === "saida_rn32" ? " ao sair do grupo" : "";
  switch (h.acao) {
    case "criada":
      return [[quem, " criou a conta"], []];
    case "editada":
      return [[quem, ` editou${naSaida}`], mudancas(h.dados)];
    case "cancelada":
      return [[quem, ` cancelou a conta${naSaida}`], []];
    case "pagador_removido":
      return [["Ficou sem pagador"], [...valor("pagador", (h.dados.pagador as unknown[] | undefined)?.[0]), " saiu do grupo"]];
    case "acesso_removido":
      return [["Saiu de quem vê"], [nome(String(h.dados.pessoa ?? "")), " saiu do grupo"]];
    case "cancelada_automaticamente":
      return [["Cancelada automaticamente"], ["ficou sem ninguém que pudesse vê-la"]];
    case "acesso_preservado":
      return [["Acesso mantido"], ["o papel mudou e esta conta continuaria sem ninguém que a visse"]];
  }
}
