// Doop: k0kB5dc-Vo / componente Chip
import { Icon, type IconName } from "./icon";
import styles from "./chip.module.css";

type Props = {
  state?: "off" | "on";
  label: string;
  count?: string | number;
  /** Space/house labels may wrap; the selected or focused choice reveals the full name (Q04-39). */
  wrap?: boolean;
  /** Category chips show their icon (COR-04). */
  icon?: IconName;
  onClick: () => void;
};

export function Chip({ state = "off", label, count, wrap = false, icon, onClick }: Props) {
  return (
    <button
      type="button"
      className={styles.chip}
      data-state={state}
      data-wrap={wrap || undefined}
      aria-pressed={state === "on"}
      onClick={onClick}
    >
      {/* The pill is 40px like the Doop; the button around it keeps the 44px touch target (RNF08). */}
      <span className={styles.pill}>
        {icon && <Icon name={icon} size="sm" />}
        {/* People's names remain one line; spaces and houses can use two (Q04-39). */}
        <span className={styles.lbl} title={label}>
          {label}
        </span>
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
