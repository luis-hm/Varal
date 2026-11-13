// Doop: k0kB5dc-Vo / componente StatusBadge (com cancelada, D2)
import { Icon, type IconName } from "@/components/ui/icon";
import styles from "./status-badge.module.css";

export type Status = "aguardando" | "pendente" | "vence" | "vencida" | "paga" | "confirmada" | "cancelada";

// Icon + text for every status: never colour alone (RNF09).
const badges: Record<Status, [IconName, string]> = {
  aguardando: ["prendedor", "Aguardando boleto"],
  pendente: ["pendente", "Pendente"],
  vence: ["relogio", "Vence em breve"],
  vencida: ["alerta", "Vencida"],
  paga: ["pago", "Paga"],
  confirmada: ["comprovante", "Confirmada"],
  cancelada: ["fechar", "Cancelada"],
};

export function StatusBadge({ status }: { status: Status }) {
  const [icon, text] = badges[status];
  return (
    <span className={styles.badge} data-status={status}>
      <Icon name={icon} size="sm" className={styles.ic} />
      {text}
    </span>
  );
}
