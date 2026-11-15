// Doop: k0kB5dc-Vo / componentes NavItem e SideNav (>= 1024px). Selector menu has no frame (guide varal-ui).
"use client";

import Link from "next/link";
import { useEffect, useId, useRef, useState } from "react";
import { Icon, type IconName } from "@/components/ui/icon";
import { Logo } from "@/components/ui/logo";
import { secoes, type Secao } from "./secoes";
import styles from "./side-nav.module.css";

type NavItemProps = {
  state?: "off" | "on";
  label: string;
  icon: IconName;
  href: string;
  count?: number;
};

export function NavItem({ state = "off", label, icon, href, count }: NavItemProps) {
  return (
    <Link
      className={styles.ni}
      href={href}
      data-state={state}
      aria-current={state === "on" ? "page" : undefined}
    >
      <Icon name={icon} size="md" />
      <span className={styles.lb}>{label}</span>
      {!!count && <span className={styles.ct}>{count}</span>}
    </Link>
  );
}

type Pessoa = { iniciais: string; nome: string; detalhe: string };
export type EspacoOpcao = Pessoa & { href: string; atual?: boolean };

type Props = {
  active?: Secao;
  /** Current space shown in the selector. */
  espaco?: Pessoa;
  /** Menu options: personal space and each group (from /api/me/). Without them the selector is static. */
  espacos?: EspacoOpcao[];
  usuario?: Pessoa;
  avisos?: number;
};

function Seletor({ espaco, espacos }: { espaco: Pessoa; espacos?: EspacoOpcao[] }) {
  const [aberto, setAberto] = useState(false);
  const raiz = useRef<HTMLDivElement>(null);
  const botao = useRef<HTMLButtonElement>(null);
  const menuId = useId();

  useEffect(() => {
    if (!aberto) return;
    const fora = (e: PointerEvent) => !raiz.current?.contains(e.target as Node) && setAberto(false);
    const esc = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      setAberto(false);
      botao.current?.focus();
    };
    document.addEventListener("pointerdown", fora);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("pointerdown", fora);
      document.removeEventListener("keydown", esc);
    };
  }, [aberto]);

  const conteudo = (
    <>
      <span className={styles.av}>{espaco.iniciais}</span>
      <span className={styles.tx}>
        {espaco.nome}
        <small>{espaco.detalhe}</small>
      </span>
      <Icon name="chevron" size="sm" className={styles.down} />
    </>
  );
  if (!espacos) return <button type="button" className={styles.sp}>{conteudo}</button>;
  return (
    <div className={styles.selector} ref={raiz}>
      <button
        ref={botao}
        type="button"
        className={styles.sp}
        aria-expanded={aberto}
        aria-controls={menuId}
        aria-label={`Espaço: ${espaco.nome}. Trocar de espaço`}
        onClick={() => setAberto(!aberto)}
      >
        {conteudo}
      </button>
      <div id={menuId} className={styles.menu} hidden={!aberto}>
        <ul>
          {espacos.map((e) => (
            <li key={e.href}>
              <Link className={styles.opt} href={e.href} onClick={() => setAberto(false)} aria-current={e.atual ? "true" : undefined}>
                <span className={styles.av}>{e.iniciais}</span>
                <span className={styles.tx}>
                  {e.nome}
                  <small>{e.detalhe}</small>
                </span>
              </Link>
            </li>
          ))}
        </ul>
        <Link className={styles.opt} href="/grupos?criar=1" onClick={() => setAberto(false)}>
          <span className={styles.av}><Icon name="mais" size="sm" /></span>
          <span className={styles.tx}>Criar grupo</span>
        </Link>
      </div>
    </div>
  );
}

export function SideNav({ active, espaco, espacos, usuario, avisos }: Props) {
  return (
    <aside className={styles.sn} aria-label="Menu principal">
      <Link className={styles.logo} href="/" aria-label="Varal, início">
        <Logo />
      </Link>
      {espaco && <Seletor espaco={espaco} espacos={espacos} />}
      {/* Nova conta opens in stage 04/06; no action yet. */}
      <button type="button" className={styles.new}>
        <Icon name="mais" size="md" />
        Nova conta
      </button>
      <nav className={styles.nav}>
        {(Object.keys(secoes) as Secao[]).map((s) => (
          <NavItem
            key={s}
            state={s === active ? "on" : "off"}
            count={s === "avisos" ? avisos : undefined}
            {...secoes[s]}
          />
        ))}
      </nav>
      {usuario && (
        <div className={styles.me}>
          <span className={styles.av}>{usuario.iniciais}</span>
          <span className={styles.identity}>
            <b title={usuario.nome}>{usuario.nome}</b>
            <small title={usuario.detalhe}>{usuario.detalhe}</small>
          </span>
        </div>
      )}
    </aside>
  );
}
