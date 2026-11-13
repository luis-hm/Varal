// Doop: k0kB5dc-Vo / componente Chip
import styles from "./chip.module.css";

type Props = {
  state?: "off" | "on";
  label: string;
  count?: string | number;
  onClick: () => void;
};

export function Chip({ state = "off", label, count, onClick }: Props) {
  return (
    <button
      type="button"
      className={styles.chip}
      data-state={state}
      aria-pressed={state === "on"}
      onClick={onClick}
    >
      {/* The pill is 40px like the Doop; the button around it keeps the 44px touch target (RNF08). */}
      <span className={styles.pill}>
        {label}
        {count != null && (
          <>
            {" "}
            <span className={styles.n}>{count}</span>
          </>
        )}
      </span>
    </button>
  );
}
