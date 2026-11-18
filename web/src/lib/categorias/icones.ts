// COR-04: the closed list of category icons (api/apps/espacos/models.py Icone). Order = picker order.
import type { IconName } from "@/components/ui/icon";

export const ICONES_CATEGORIA = [
  ["casa", "Casa"], ["luz", "Luz"], ["agua", "Água"], ["internet", "Internet"], ["telefone", "Telefone"],
  ["carro", "Carro"], ["mercado", "Mercado"], ["saude", "Saúde"], ["educacao", "Educação"], ["cartao", "Cartão"],
  ["trabalho", "Trabalho"], ["lazer", "Lazer"], ["pet", "Pet"], ["contas", "Outras"],
] as const satisfies readonly (readonly [IconName, string])[];

export type IconeCategoria = (typeof ICONES_CATEGORIA)[number][0];

/** null / unknown (bills without category) fall back to the generic list icon. */
export const iconeDe = (icone?: string | null): IconName => (ICONES_CATEGORIA.some(([n]) => n === icone) ? (icone as IconName) : "contas");

/** URL segment for the bills without category inside a group (COR-07/COR-11). */
export const SEM_CATEGORIA = "sem-categoria";
