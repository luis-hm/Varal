// Doop: k0kB5dc-Vo / 06 · Conferir conta + M02; CU09, Q08-9.
"use client";
import { useId } from "react";
import { Field } from "@/components/ui/field";
import { Icon } from "@/components/ui/icon";
import { RadioCard } from "@/components/ui/radio-card";
import styles from "./repeticao-campo.module.css";

type Props = {
  repetir: boolean;
  tipo: "fixo" | "variavel";
  dia: string;
  disabled?: boolean;
  erro?: string;
  onRepetir: (value: boolean) => void;
  onTipo: (value: "fixo" | "variavel") => void;
  onDia: (value: string) => void;
};

export function RepeticaoCampo({ repetir, tipo, dia, disabled, erro, onRepetir, onTipo, onDia }: Props) {
  const nome = useId();
  return <fieldset className={styles.grupo} disabled={disabled}>
    <label className={styles.toggle}><Icon name="repetir" size="md" /><span><b>Repetir todo mês</b><small>Cadastre uma vez, o Varal cria todo mês.</small></span><input type="checkbox" checked={repetir} onChange={(e) => onRepetir(e.target.checked)} /></label>
    {repetir && <div className={styles.campos}>
      <Field label="Dia das próximas contas" type="number" inputMode="numeric" min={1} max={31} value={dia} onChange={(e) => onDia(e.target.value)} required hint="Em meses mais curtos, a conta vence no último dia." />
      <fieldset className={styles.opcoes}><legend>Valor das próximas contas</legend>
        <RadioCard name={nome} value="fixo" title="Valor fixo" text="As próximas contas usam o valor informado." state={tipo === "fixo" ? "on" : "off"} onChange={() => onTipo("fixo")} />
        <RadioCard name={nome} value="variavel" title="Valor muda" text="O valor das próximas contas fica a definir." state={tipo === "variavel" ? "on" : "off"} onChange={() => onTipo("variavel")} />
      </fieldset>
      <p className={styles.nota}>A conta atual mantém o valor e o vencimento conferidos. O código e o PDF não são copiados para os próximos meses.</p>
      {erro && <p className={styles.erro} role="alert">{erro}</p>}
    </div>}
  </fieldset>;
}
