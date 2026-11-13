// Doop: k0kB5dc-Vo / componente Field
"use client";

import { useId, type InputHTMLAttributes, type ReactNode } from "react";
import styles from "./field.module.css";

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "id"> & {
  label: string;
  hint?: string;
  /** Error message; puts the field in the Doop "error" state and replaces the hint. */
  error?: string;
  /** Doop "filled" state: value read by the system (barcode, PDF). */
  filled?: boolean;
  trailing?: ReactNode;
};

// Doop "placeholder" state is the native placeholder of an empty input.
export function Field({ label, hint, error, filled, trailing, className, ...input }: Props) {
  const id = useId();
  const message = error ?? hint;
  const state = error ? "error" : filled ? "filled" : "default";
  return (
    <div className={className ? `${styles.fld} ${className}` : styles.fld} data-state={state}>
      <label className={styles.lb} htmlFor={id}>
        {label}
      </label>
      <div className={styles.bx}>
        <input
          {...input}
          id={id}
          className={styles.vl}
          aria-invalid={error ? true : undefined}
          aria-describedby={message ? `${id}-hint` : undefined}
        />
        {trailing && <span className={styles.tr}>{trailing}</span>}
      </div>
      {message && (
        <p id={`${id}-hint`} className={styles.hn}>
          {message}
        </p>
      )}
    </div>
  );
}
