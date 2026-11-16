// Doop: k0kB5dc-Vo / 02 · Início (JJvrRugL0_) + D02 · Início (SMDsrD8FGT); CU06; RF13, RN12, RN13, Q9, Q12, Q23.
// Not here until their stage: bell and "Avisos recentes" (09), search (Q13), paid bar and the green "pagas"
// tag (07), "aguardando boleto" card (05/06).
"use client";

import Link from "next/link";
import { espacosDoUsuario, useSessao } from "@/components/layout/app-shell";
import { SeletorEspaco } from "@/components/layout/side-nav";
import { HouseCard } from "@/components/groups/house-card";
import { useResumo } from "@/lib/contas/hooks";
import { mesAno, nomeMes, partesReais, plural, reais, saudacao } from "@/lib/contas/formato";
import { ContaCard } from "./bill-card";
import { useContagem } from "./contagem";
import { ProgressoPagas } from "./progresso-pagas";
import styles from "./inicio.module.css";

export function Inicio() {
  const { user, espaco, escolherEspaco } = useSessao();
  const resumo = useResumo(espaco.id);
  const espacos = espacosDoUsuario(user, espaco.id);
  const primeiroNome = (user.nome || user.email.split("@")[0]).split(/\s+/)[0];

  return (
    <div className={styles.page}>
      <header className={styles.topo}>
        <SeletorEspaco variant="pilula" espaco={espacos.find((e) => e.atual) ?? espacos[0]} espacos={espacos} onEscolher={escolherEspaco} />
      </header>
      <header className={`${styles.ola} ${styles.in}`}>
        {/* Ajuste 29: an e-mail used as name never wraps the greeting. */}
        <h1 title={`${saudacao()}, ${primeiroNome}`}>
          {saudacao()}, {primeiroNome}
        </h1>
        {resumo.data && (
          <p>
            {mesAno(resumo.data.mes).replace(" ", " de ")} · {espaco.nome}
          </p>
        )}
      </header>

      {resumo.error ? (
        <p className={styles.vazio} role="alert">{resumo.error.message}</p>
      ) : !resumo.data ? (
        <p className={styles.vazio} role="status">Carregando contas…</p>
      ) : (
        <>
          <Heroi mes={resumo.data.mes} total={resumo.data.total_centavos} qtd={resumo.data.qtd} pagas={resumo.data.pagas_qtd} vencidas={resumo.data.vencidas_qtd} vencem={resumo.data.vence_qtd} janela={resumo.data.janela_alerta_dias} />
          <div className={styles.grade} data-grupo={espaco.tipo === "grupo" || undefined}>
            <section aria-labelledby="atencao-t">
              <div className={`${styles.sec} ${styles.in} ${styles.d1}`}>
                <h2 id="atencao-t">Precisa de atenção</h2>
                <Link href="/contas">
                  Ver todas<span className={styles.desk}>&nbsp;as contas</span>
                </Link>
              </div>
              {resumo.data.atencao.length ? (
                <ul className={styles.lista}>
                  {resumo.data.atencao.map((c, i) => (
                    <li key={c.id} className={styles.in} style={{ animationDelay: `${0.16 + i * 0.07}s` }}>
                      <ContaCard conta={c} href={`/contas/${c.id}`} />
                    </li>
                  ))}
                </ul>
              ) : (
                <p className={styles.cartao}>Nenhuma conta vencida ou vencendo nos próximos {plural(resumo.data.janela_alerta_dias, "dia", "dias")}.</p>
              )}
            </section>
            {espaco.tipo === "grupo" && (
              <section className={styles.casas} aria-labelledby="casas-t">
                <div className={`${styles.sec} ${styles.in} ${styles.d2}`}>
                  <h2 id="casas-t">Por casa</h2>
                  <Link href={`/grupos/${espaco.id}`}>Grupo</Link>
                </div>
                {resumo.data.por_casa.length ? (
                  <div className={`${styles.houses} ${styles.in} ${styles.d3}`}>
                    {resumo.data.por_casa.map((c) => (
                      <HouseCard key={c.id} label={c.nome} caption={reais(c.total_centavos)} progress={c.qtd ? c.pagas_qtd / c.qtd * 100 : undefined} caption-2={c.qtd ? `${c.pagas_qtd} de ${c.qtd} pagas em ${nomeMes(resumo.data.mes)}` : `0 contas em ${nomeMes(resumo.data.mes)}`} />
                    ))}
                  </div>
                ) : (
                  <p className={styles.cartao}>Nenhuma conta com casa em {nomeMes(resumo.data.mes)}.</p>
                )}
              </section>
            )}
          </div>
        </>
      )}
    </div>
  );
}

type HeroiProps = { mes: string; total: number; qtd: number; pagas: number; vencidas: number; vencem: number; janela: number };

/** Month total (count-up) and the clothesline (swing). Q12/Q23: no paid bar and no "pagas" tag until stage 07. */
function Heroi({ mes, total, qtd, pagas, vencidas, vencem, janela }: HeroiProps) {
  const [inteiro, centavos] = partesReais(useContagem(total));
  const rotulo = `Total de ${nomeMes(mes)}`;
  return (
    <section className={`${styles.hero} ${styles.in}`} aria-label={rotulo}>
      <div className={styles.heroTopo}>
        <p className={styles.rotulo}>{rotulo}</p>
        <span className={styles.qtd}>{plural(qtd, "conta", "contas")}</span>
      </div>
      <p className={styles.valor}>
        <span className={styles.srOnly}>{reais(total)}</span>
        <span aria-hidden="true">
          {inteiro}
          <span className={styles.cent}>{centavos}</span>
        </span>
      </p>
      <ProgressoPagas pagas={pagas} total={qtd} mes={nomeMes(mes)} />
      <div className={styles.varal} role="img" aria-label={`Precisa de atenção: ${plural(vencidas, "vencida", "vencidas")}, ${vencem} ${vencem === 1 ? "vence" : "vencem"} em até ${plural(janela, "dia", "dias")}, ${plural(pagas, "paga", "pagas")}`}>
        <svg className={styles.fio} viewBox="0 0 366 44" preserveAspectRatio="none" aria-hidden="true">
          <path d="M-4 10 Q183 42 370 10" />
        </svg>
        <div className={styles.tags}>
          <span className={styles.tag} data-tom="vencida">
            <i />
            <b>{vencidas}</b>
            <small>{vencidas === 1 ? "vencida" : "vencidas"}</small>
          </span>
          <span className={styles.tag} data-tom="vence">
            <i />
            <b>{vencem}</b>
            <small>
              <span className={styles.mob}>{vencem === 1 ? "vence já" : "vencem já"}</span>
              <span className={styles.desk}>
                {vencem === 1 ? "vence" : "vencem"} em {plural(janela, "dia", "dias")}
              </span>
            </small>
          </span>
          <span className={styles.tag} data-tom="paga"><i /><b>{pagas}</b><small>{pagas === 1 ? "paga" : "pagas"}</small></span>
        </div>
      </div>
    </section>
  );
}
