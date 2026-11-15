// Doop: k0kB5dc-Vo / componentes TabItem e TabBar (< 1024px)
import Link from "next/link";
import { Icon, type IconName } from "@/components/ui/icon";
import { secoes } from "./secoes";
import styles from "./tab-bar.module.css";

type TabItemProps = { state?: "off" | "on"; label: string; icon: IconName; href: string };

export function TabItem({ state = "off", label, icon, href }: TabItemProps) {
  return (
    <Link
      className={styles.tab}
      href={href}
      data-state={state}
      aria-current={state === "on" ? "page" : undefined}
    >
      <Icon name={icon} size="md" />
      {label}
      <span className={styles.dot} />
    </Link>
  );
}

const left = ["inicio", "contas"] as const;
const right = ["grupos", "perfil"] as const;
type TabBarActive = (typeof left)[number] | (typeof right)[number];

export function TabBar({ active, onNovaConta }: { active?: TabBarActive; onNovaConta?: () => void }) {
  const item = (s: TabBarActive) => (
    <TabItem key={s} state={s === active ? "on" : "off"} {...secoes[s]} />
  );
  return (
    <nav className={styles.tb} aria-label="Navegação principal">
      {left.map(item)}
      <button type="button" className={styles.fab} aria-label="Nova conta" aria-haspopup="dialog" onClick={onNovaConta}>
        <Icon name="mais" />
      </button>
      {right.map(item)}
    </nav>
  );
}
