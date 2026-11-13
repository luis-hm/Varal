// Doop: k0kB5dc-Vo / shell de 02 · Início (JJvrRugL0_, TabBar) + D02 · Início (SMDsrD8FGT, SideNav)
"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { secaoAtiva } from "./secoes";
import { SideNav } from "./side-nav";
import { TabBar } from "./tab-bar";
import styles from "./app-shell.module.css";

// One app: below 1024px the TabBar, from 1024px the fixed 264px SideNav (CSS decides, no JS).
export function AppShell({ children }: { children: ReactNode }) {
  const active = secaoAtiva(usePathname());
  return (
    <div className={styles.shell}>
      <div className={styles.side}>
        <SideNav active={active} />
      </div>
      <main className={styles.main}>{children}</main>
      <div className={styles.bottom}>
        <TabBar active={active === "avisos" ? undefined : active} />
      </div>
    </div>
  );
}
