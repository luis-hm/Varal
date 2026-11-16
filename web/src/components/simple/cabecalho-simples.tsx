// Doop: k0kB5dc-Vo / 13 · Modo simples (mIvLheR2TS) + D05 (YTtAtGSyCI); Q10-11.
import Link from "next/link";
import type { ReactNode } from "react";
import { Logo } from "@/components/ui/logo";
import styles from "./simples.module.css";

type Props = { nome: string; grupo: string; sair: ReactNode };
export function CabecalhoSimples({ nome, grupo, sair }: Props) {
  return <header className={styles.cabecalho}>
    <span className={styles.marca} aria-label="Varal"><Logo /></span>
    <p className={styles.identidade}><span>{nome}</span><span aria-hidden="true"> · </span><span>{grupo}</span></p>
    <nav className={styles.navegacao} aria-label="Navegação do modo simples">
      <Link href="/grupos">Grupos</Link>
      {sair}
    </nav>
  </header>;
}
