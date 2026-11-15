// Doop: k0kB5dc-Vo / folha de 11 · Convidar membro (bkv_O9ohNO) + modal M05 (8XSFrkwy2d).
// One <dialog>: below 1024px it is a bottom sheet (sheet-up), from 1024px a centred modal (modal-pop).
"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";
import { Button } from "./button";
import { Icon } from "./icon";
import styles from "./folha.module.css";

type Props = {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  /** Action buttons. On desktop a ghost "Cancelar" comes first (M05); on mobile they go full width (11). */
  actions?: ReactNode;
  /** M05 is a fixed 560×480 window. */
  size?: "auto" | "convite";
  children: ReactNode;
};

export function Folha({ open, onClose, title, subtitle, actions, size = "auto", children }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const opener = useRef<Element | null>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      opener.current = document.activeElement;
      // showModal() makes the page inert (focus trap) and gives Esc for free.
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
    } else if (!open && dialog.open) {
      if (typeof dialog.close === "function") dialog.close();
      else dialog.removeAttribute("open");
      // Give focus back to whatever opened the sheet.
      (opener.current as HTMLElement | null)?.focus?.();
    }
  }, [open]);

  // Every way out (Esc, backdrop, buttons) asks the parent; the effect above closes the dialog.
  const handleClose = onClose;

  return (
    <dialog
      ref={ref}
      className={styles.folha}
      data-size={size}
      aria-labelledby={titleId}
      onCancel={(e) => {
        e.preventDefault();
        handleClose();
      }}
      // A click on the backdrop lands on the <dialog> itself.
      onClick={(e) => e.target === e.currentTarget && handleClose()}
    >
      {open && (
        <div className={styles.inner}>
          <button type="button" className={styles.handle} aria-label="Fechar" onClick={handleClose}>
            <span />
          </button>
          <header className={styles.head}>
            <div>
              <h2 id={titleId} className={styles.title}>{title}</h2>
              {subtitle && <p className={styles.sub}>{subtitle}</p>}
            </div>
            <button type="button" className={styles.close} aria-label="Fechar" onClick={handleClose}>
              <Icon name="fechar" size="md" />
            </button>
          </header>
          {children}
          {actions && (
            <div className={styles.actions}>
              <Button tone="ghost" label="Cancelar" className={styles.cancel} onClick={handleClose} />
              {actions}
            </div>
          )}
        </div>
      )}
    </dialog>
  );
}
