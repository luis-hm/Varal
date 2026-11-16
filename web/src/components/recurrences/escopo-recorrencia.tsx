// Doop: k0kB5dc-Vo / RadioCard; 07 · Detalhe + D03. Q08-3: scope choice has no dedicated frame.
import { useId } from "react";
import { RadioCard } from "@/components/ui/radio-card";
import styles from "./escopo-recorrencia.module.css";

type Props = { value: "mes" | "proximos"; onChange: (value: "mes" | "proximos") => void; cancelar?: boolean; disabled?: boolean };

export function EscopoRecorrencia({ value, onChange, cancelar = false, disabled = false }: Props) {
  const nome = useId();
  return <fieldset className={styles.grupo} disabled={disabled}>
    <legend>Aplicar a</legend>
    <RadioCard name={nome} value="mes" title="Só este mês" text={cancelar ? "Cancela apenas esta conta." : "Altera apenas esta conta."} state={value === "mes" ? "on" : "off"} onChange={() => onChange("mes")} />
    <RadioCard name={nome} value="proximos" title="Este mês e próximos" text={cancelar ? "Cancela as contas abertas deste mês em diante e encerra futuras gerações." : "Altera esta conta, o modelo e as próximas contas abertas."} state={value === "proximos" ? "on" : "off"} onChange={() => onChange("proximos")} />
  </fieldset>;
}
