// Doop: k0kB5dc-Vo / GJDSPaQbio (01 · Entrar) + 7JTmWMAJup (D01 · Entrar); CU01.
import type { ReactNode } from "react";
import { Icon } from "@/components/ui/icon";
import styles from "./auth.module.css";

export function AuthFrame({ children }: { children: ReactNode }) {
  return (
    <main className={styles.frame}>
      <section className={styles.brand} aria-label="Varal">
        <div className={styles.clothesline} role="img" aria-label="Três contas penduradas num varal">
          <svg className={styles.rope} viewBox="0 0 720 90" preserveAspectRatio="none" aria-hidden="true">
            <path className={styles.mobileRope} d="M-11.077 18 Q360 87 731.077 18" vectorEffect="non-scaling-stroke" />
            <path className={styles.desktopRope} d="M-10 14 Q360 90 730 14" vectorEffect="non-scaling-stroke" />
          </svg>
          <div className={`${styles.tag} ${styles.red}`}><span /><i /></div>
          <div className={`${styles.tag} ${styles.amber}`}><span /><i /></div>
          <div className={`${styles.tag} ${styles.green}`}><span /><i /></div>
        </div>
        <div className={styles.brandCopy}>
          <p className={styles.wordmark}>varal</p>
          <p className={styles.tagline}>As contas da família, à vista de todo mundo.</p>
          <div className={styles.benefits}>
            <p><span><Icon name="enviar" size="sm" /></span>Envie o PDF do boleto e o resto se preenche.</p>
            <p><span><Icon name="sino" size="sm" /></span>Avisos antes e depois do vencimento.</p>
            <p><span><Icon name="cadeado" size="sm" /></span>Suas contas pessoais nunca aparecem no grupo.</p>
          </div>
        </div>
      </section>
      <section className={styles.sheet} aria-label="Acesso à conta">
        <div className={styles.content}>{children}</div>
      </section>
    </main>
  );
}
