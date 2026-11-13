// Doop: k0kB5dc-Vo / frame Logo (t4pHch9UDR) e logo do componente SideNav
import styles from "./logo.module.css";

type Props = {
  variant?: "horizontal" | "simbolo";
  /** Symbol width in px. Below 64px the Doop uses the version without clothespins. */
  size?: number;
};

export function Logo({ variant = "horizontal", size = 44 }: Props) {
  const symbol = (
    <svg
      className={styles.symbol}
      width={size}
      height={Math.round((size * 100) / 120)}
      viewBox="0 0 120 100"
      aria-hidden="true"
    >
      {size >= 64 ? (
        <>
          <path className={styles.line} d="M8 28 Q60 52 112 28" strokeWidth="5" />
          <g transform="rotate(-6 32 37)">
            <rect className={styles.red} x="22" y="40" width="20" height="30" rx="4" />
            <rect className={styles.pin} x="30" y="32" width="4" height="12" rx="1.5" />
          </g>
          <rect className={styles.amber} x="50" y="44" width="20" height="30" rx="4" />
          <rect className={styles.pin} x="58" y="35" width="4" height="12" rx="1.5" />
          <g transform="rotate(5 88 37)">
            <rect className={styles.green} x="78" y="40" width="20" height="30" rx="4" />
            <rect className={styles.pin} x="86" y="32" width="4" height="12" rx="1.5" />
          </g>
        </>
      ) : (
        <>
          <path className={styles.line} d="M8 28 Q60 52 112 28" strokeWidth="7" />
          <rect className={styles.red} x="20" y="40" width="22" height="32" rx="4" />
          <rect className={styles.amber} x="49" y="44" width="22" height="32" rx="4" />
          <rect className={styles.green} x="78" y="40" width="22" height="32" rx="4" />
        </>
      )}
    </svg>
  );
  if (variant === "simbolo") return symbol;
  return (
    <span className={styles.logo}>
      {symbol}
      <b className={styles.word}>varal</b>
    </span>
  );
}
