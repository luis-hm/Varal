// Names and e-mails never wrap (ajuste 29): one line, cut with an ellipsis, the whole value in `title`.
// The text node keeps the full value, so the accessible name of whatever contains it stays complete.
import styles from "./nome.module.css";

export function Nome({ children, className }: { children: string; className?: string }) {
  return (
    <span className={className ? `${styles.nome} ${className}` : styles.nome} title={children}>
      {children}
    </span>
  );
}
