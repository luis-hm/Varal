// RN22 history lines. Decision 8: automatic actions have no author and never read as "Ex-membro";
// a deleted author does (RN30, the API sends "Ex-membro").
import type { Historico } from "./client";
import { reais } from "./formato";

const campos: Record<string, string> = {
  descricao: "descrição",
  valor_centavos: "valor",
  vencimento: "vencimento",
  subgrupo: "casa",
  pagador: "quem paga",
  visibilidade: "quem vê",
  acesso: "quem mais vê",
};

function valor(campo: string, v: unknown): string {
  if (v === null || v === undefined || (Array.isArray(v) && !v.length)) {
    return campo === "pagador" ? "ninguém" : campo === "subgrupo" ? "sem casa" : "ninguém";
  }
  if (campo === "valor_centavos") return reais(Number(v));
  if (campo === "vencimento") return String(v).split("-").reverse().join("/");
  if (campo === "visibilidade") return v === "restrita" ? "só algumas pessoas" : "todo o grupo";
  if (Array.isArray(v)) return v.join(", ");
  return String(v);
}

function mudancas(dados: Historico["dados"]) {
  return Object.entries(dados)
    .filter(([campo, par]) => campo in campos && Array.isArray(par) && par.length === 2)
    .map(([campo, par]) => `${campos[campo]}: ${valor(campo, (par as unknown[])[0])} → ${valor(campo, (par as unknown[])[1])}`)
    .join(" · ");
}

/** [bold part, detail] of one history line. */
export function linhaHistorico(h: Historico): [string, string] {
  const quem = h.sou_eu ? "Você" : (h.autor ?? "");
  const naSaida = h.dados.motivo === "saida_rn32" ? " ao sair do grupo" : "";
  switch (h.acao) {
    case "criada":
      return [`${quem} criou a conta`, ""];
    case "editada":
      return [`${quem} editou${naSaida}`, mudancas(h.dados)];
    case "cancelada":
      return [`${quem} cancelou a conta${naSaida}`, ""];
    case "pagador_removido":
      return ["Ficou sem pagador", `${valor("pagador", (h.dados.pagador as unknown[] | undefined)?.[0])} saiu do grupo`];
    case "acesso_removido":
      return ["Saiu de quem vê", `${String(h.dados.pessoa ?? "")} saiu do grupo`];
    case "cancelada_automaticamente":
      return ["Cancelada automaticamente", "ficou sem ninguém que pudesse vê-la"];
    case "acesso_preservado":
      return ["Acesso mantido", "o papel mudou e esta conta continuaria sem ninguém que a visse"];
  }
}
