// Doop: k0kB5dc-Vo / RecurringRow em 10 · Grupo (SfhuKVOQIF) + D04 (5UzCB5yNaI); CU09.
import { Icon } from "@/components/ui/icon";
import styles from "./recurring-row.module.css";

type Props = { text: string; caption: string; vl: string; onClick?: () => void };

export function RecurringRow({ text, caption, vl, onClick }: Props) {
  const content = <><Icon name="repetir" size="md" /><span className={styles.texto}><b>{text}</b><small>{caption}</small></span><span className={styles.valor}>{vl}</span></>;
  return onClick ? <button type="button" className={styles.linha} onClick={onClick} aria-haspopup="dialog">{content}</button> : <div className={styles.linha}>{content}</div>;
}
