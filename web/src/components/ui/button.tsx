// Doop: k0kB5dc-Vo / componente Button (52px, D1)
import type { ButtonHTMLAttributes } from "react";
import { Icon, type IconName } from "./icon";
import styles from "./button.module.css";

type Base = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children"> & {
  tone?: "primary" | "secondary" | "ghost" | "success" | "danger";
  width?: "auto" | "full";
  icon?: IconName;
};

// Icon-only buttons have no visible text, so they must name themselves (D1).
type Props = Base & ({ label: string } | { label?: undefined; icon: IconName; "aria-label": string });

export function Button({ tone = "primary", width = "auto", label, icon, className, ...rest }: Props) {
  return (
    <button
      type="button"
      {...rest}
      data-tone={tone}
      data-width={width}
      className={className ? `${styles.btn} ${className}` : styles.btn}
    >
      {icon && <Icon name={icon} size="md" />}
      {label}
    </button>
  );
}
