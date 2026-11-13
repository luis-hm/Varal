// Doop: k0kB5dc-Vo / componentes NavItem e SideNav (>= 1024px)
import Link from "next/link";
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

type Props = {
  active?: Secao;
  /** Space selector; real data in stages 02–03. */
  espaco?: Pessoa;
  usuario?: Pessoa;
  avisos?: number;
};

export function SideNav({ active, espaco, usuario, avisos }: Props) {
  return (
    <aside className={styles.sn} aria-label="Menu principal">
      <Link className={styles.logo} href="/" aria-label="Varal, início">
        <Logo />
      </Link>
      {espaco && (
        <button type="button" className={styles.sp}>
          <span className={styles.av}>{espaco.iniciais}</span>
          <span className={styles.tx}>
            {espaco.nome}
            <small>{espaco.detalhe}</small>
          </span>
          <Icon name="chevron" size="sm" className={styles.down} />
        </button>
      )}
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
          <span>
            <b>{usuario.nome}</b>
            <small>{usuario.detalhe}</small>
          </span>
        </div>
      )}
    </aside>
  );
}
