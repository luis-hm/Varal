// Doop: k0kB5dc-Vo / componente Icon (frame Ícones FDDhQEf8T5). Paths copied from the Doop template.
import type { ReactNode } from "react";
import styles from "./icon.module.css";

const paths = {
  varal: (
    <>
      <path d="M2 6.5Q12 12 22 6.5" />
      <rect x="8" y="11.5" width="8" height="10" rx="2" />
      <path d="M12 8.5v4" />
    </>
  ),
  contas: <path d="M9 7h11M9 12h11M9 17h11M4.5 7h.01M4.5 12h.01M4.5 17h.01" />,
  grupo: (
    <>
      <circle cx="9" cy="8" r="3.2" />
      <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" />
      <circle cx="17" cy="9" r="2.5" />
      <path d="M17 14c2.2 0 4 1.8 4 4" />
    </>
  ),
  perfil: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8" />
    </>
  ),
  boleto: (
    <>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M7 9v6M10 9v6M14 9v6M17 9v6" />
    </>
  ),
  pix: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <path d="M14 14h2M20 14v2M14 18v3M18 18h3v3" />
    </>
  ),
  manual: (
    <>
      <path d="M4 20l1-4L16 5l3 3L8 19z" />
      <path d="M13.5 7.5l3 3" />
    </>
  ),
  casa: (
    <>
      <path d="M3.5 11L12 4l8.5 7" />
      <path d="M6 9.5V20h12V9.5" />
      <path d="M10 20v-5h4v5" />
    </>
  ),
  calendario: (
    <>
      <rect x="3" y="5" width="18" height="16" rx="2.5" />
      <path d="M3 10h18M8 3v4M16 3v4" />
    </>
  ),
  repetir: (
    <>
      <path d="M4 12a8 8 0 0 1 13.7-5.6L20 9" />
      <path d="M20 4v5h-5" />
      <path d="M20 12a8 8 0 0 1-13.7 5.6L4 15" />
      <path d="M4 20v-5h5" />
    </>
  ),
  cadeado: (
    <>
      <rect x="5" y="11" width="14" height="10" rx="2.5" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </>
  ),
  sino: (
    <>
      <path d="M6 10a6 6 0 0 1 12 0c0 6 2.5 7.5 2.5 7.5h-17S6 16 6 10z" />
      <path d="M10 20.5a2 2 0 0 0 4 0" />
    </>
  ),
  prendedor: (
    <>
      <rect x="8.5" y="2.5" width="7" height="19" rx="2" />
      <circle cx="12" cy="14" r="1.3" />
      <path d="M12 2.5v8" />
    </>
  ),
  pendente: <circle cx="12" cy="12" r="8.5" />,
  relogio: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  alerta: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7.5v5M12 16.5h.01" />
    </>
  ),
  pago: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M8 12.5l3 3 5-6" />
    </>
  ),
  comprovante: (
    <>
      <path d="M6 3h12v18l-2-1.5-2 1.5-2-1.5-2 1.5-2-1.5-2 1.5z" />
      <path d="M9 11.5l2 2 4-4.5" />
    </>
  ),
  copiar: (
    <>
      <rect x="9" y="9" width="12" height="12" rx="2" />
      <path d="M15 9V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h4" />
    </>
  ),
  camera: (
    <>
      <path d="M3 8a2 2 0 0 1 2-2h2l1.5-2h7L17 6h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <circle cx="12" cy="13" r="3.5" />
    </>
  ),
  pedir: (
    <>
      <path d="M12 15V3M7 8l5-5 5 5" />
      <path d="M5 13v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6" />
    </>
  ),
  mais: <path d="M12 5v14M5 12h14" />,
  filtro: <path d="M3 5h18l-7 8v6l-4 2v-8z" />,
  voltar: <path d="M19 12H5M11 6l-6 6 6 6" />,
  chevron: <path d="M9 6l6 6-6 6" />,
  fechar: <path d="M6 6l12 12M18 6L6 18" />,
  pdf: (
    <>
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5" />
      <path d="M8.5 16.5h7M8.5 13h4" />
    </>
  ),
  baixar: (
    <>
      <path d="M12 4v11M7 10l5 5 5-5" />
      <path d="M5 20h14" />
    </>
  ),
  enviar: (
    <>
      <path d="M12 15V4M7 9l5-5 5 5" />
      <path d="M5 20h14" />
    </>
  ),
} satisfies Record<string, ReactNode>;

export type IconName = keyof typeof paths;
export const iconNames = Object.keys(paths) as IconName[];

const sizes = { sm: 16, md: 20, lg: 24, xl: 32 };

type Props = {
  name: IconName;
  size?: keyof typeof sizes;
  /** Without a label the icon is decorative (aria-hidden); with one it is an image. */
  label?: string;
  className?: string;
};

export function Icon({ name, size = "lg", label, className }: Props) {
  const px = sizes[size];
  return (
    <svg
      viewBox="0 0 24 24"
      width={px}
      height={px}
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      data-name={name}
      className={className ? `${styles.icon} ${className}` : styles.icon}
      {...(label ? { role: "img", "aria-label": label } : { "aria-hidden": true })}
    >
      {paths[name]}
    </svg>
  );
}
