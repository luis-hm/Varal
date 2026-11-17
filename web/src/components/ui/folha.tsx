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
  /** A pending write must settle before the dialog can close or be submitted again. */
  busy?: boolean;
  /** Full-screen mobile page when its Doop frame specifies one. */
  mobileFull?: boolean;
  /** Explicit trigger for sheets that replace an asynchronously loaded placeholder. */
  returnFocusTo?: HTMLElement | null;
  restoreFocusOnUnmount?: boolean;
  children: ReactNode;
};

export function Folha({ open, onClose, title, subtitle, actions, size = "auto", busy = false, mobileFull = false, returnFocusTo, restoreFocusOnUnmount = false, children }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const opener = useRef<Element | null>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      opener.current = returnFocusTo ?? document.activeElement;
      // showModal() makes the page inert (focus trap) and gives Esc for free.
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
    } else if (!open && dialog.open) {
      if (typeof dialog.close === "function") dialog.close();
      else dialog.removeAttribute("open");
      // Give focus back to whatever opened the sheet.
      (opener.current as HTMLElement | null)?.focus?.();
    }
  }, [open, returnFocusTo]);

  useEffect(() => () => {
    if (restoreFocusOnUnmount && returnFocusTo?.isConnected) returnFocusTo.focus();
  }, [restoreFocusOnUnmount, returnFocusTo]);

  // Every way out (Esc, backdrop, buttons) asks the parent; the effect above closes the dialog.
  const handleClose = () => { if (!busy) onClose(); };

  return (
    <dialog
      ref={ref}
      className={styles.folha}
      data-size={size}
      data-mobile-full={mobileFull || undefined}
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
          <button type="button" className={styles.handle} aria-label="Fechar" onClick={handleClose} disabled={busy}>
            <span />
          </button>
          <header className={styles.head}>
            {mobileFull && <button type="button" className={styles.back} aria-label="Voltar" onClick={handleClose} disabled={busy}><Icon name="voltar" size="md" /></button>}
            <div>
              <h2 id={titleId} className={styles.title}>{title}</h2>
              {subtitle && <p className={styles.sub}>{subtitle}</p>}
            </div>
            <button type="button" className={styles.close} aria-label="Fechar" onClick={handleClose} disabled={busy}>
              <Icon name="fechar" size="md" />
            </button>
          </header>
          {children}
          {actions && (
            <div className={styles.actions}>
              <Button tone="ghost" label="Cancelar" className={styles.cancel} onClick={handleClose} disabled={busy} />
              {actions}
            </div>
          )}
        </div>
      )}
    </dialog>
  );
}
