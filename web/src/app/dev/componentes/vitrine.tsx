// Doop: k0kB5dc-Vo / componentes Icon, StatusBadge, Button, Chip, Field, TopBar, TabItem, TabBar, NavItem,
// SideNav, RadioCard, MemberRow, HouseCard, BillCard (Mwqabjlc2s) (página 04 · Componentes), folha/modal de 11/M05 e frame Logo (t4pHch9UDR).
// Sample copy taken from the Doop frames.
"use client";

import { useState } from "react";
import { BillCard } from "@/components/bills/bill-card";
import { StatusBadge, type Status } from "@/components/bills/status-badge";
import { HouseCard } from "@/components/groups/house-card";
import { MemberRow } from "@/components/groups/member-row";
import { SideNav, NavItem } from "@/components/layout/side-nav";
import { TabBar, TabItem } from "@/components/layout/tab-bar";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Field } from "@/components/ui/field";
import { Folha } from "@/components/ui/folha";
import { RadioCard } from "@/components/ui/radio-card";
import { ordemPapeis, papeis } from "@/lib/grupos/papeis";
import { Icon, iconNames } from "@/components/ui/icon";
import { Logo } from "@/components/ui/logo";
import styles from "./vitrine.module.css";

const statuses: Status[] = ["aguardando", "pendente", "vence", "vencida", "paga", "confirmada", "cancelada"];
const tones = ["primary", "secondary", "ghost", "success", "danger"] as const;
const chips = [
  ["Todas", 13],
  ["Vencidas", 2],
  ["Pendentes", 3],
  ["Pagas", 8],
] as const;

export function Vitrine() {
  const [chip, setChip] = useState("Vencidas");
  const [papel, setPapel] = useState<(typeof ordemPapeis)[number]>("pagador");
  const [folha, setFolha] = useState(false);
  return (
    <div className={styles.page}>
      <TopBar title="Componentes" backHref="/" />

      <section className={styles.sec}>
        <h2>Logo</h2>
        <div className={styles.row}>
          <Logo />
          <Logo variant="simbolo" size={120} />
        </div>
      </section>

      <section className={styles.sec}>
        <h2>Icon</h2>
        <ul className={styles.icons}>
          {iconNames.map((name) => (
            <li key={name}>
              <Icon name={name} />
              <span>{name}</span>
            </li>
          ))}
        </ul>
        <div className={styles.row}>
          <Icon name="sino" size="sm" />
          <Icon name="sino" size="md" />
          <Icon name="sino" size="lg" />
          <Icon name="sino" size="xl" />
        </div>
      </section>

      <section className={styles.sec}>
        <h2>StatusBadge</h2>
        <div className={styles.row}>
          {statuses.map((s) => (
            <StatusBadge key={s} status={s} />
          ))}
        </div>
      </section>

      <section className={styles.sec}>
        <h2>Button</h2>
        <div className={styles.row}>
          {tones.map((tone) => (
            <Button key={tone} tone={tone} label="Copiar código" />
          ))}
          <Button tone="ghost" icon="copiar" label="Copiar código" />
          <Button tone="secondary" icon="baixar" aria-label="Baixar PDF" />
        </div>
        <Button width="full" label="Entrar" />
      </section>

      <section className={styles.sec}>
        <h2>Chip</h2>
        <div className={styles.row}>
          {chips.map(([label, count]) => (
            <Chip
              key={label}
              label={label}
              count={count}
              state={chip === label ? "on" : "off"}
              onClick={() => setChip(label)}
            />
          ))}
        </div>
      </section>

      <section className={styles.sec}>
        <h2>Field</h2>
        <div className={styles.fields}>
          <Field label="E-mail" placeholder="voce@email.com" />
          <Field label="Beneficiário" defaultValue="Enel Distribuição Ceará" />
          <Field
            label="Valor"
            defaultValue="R$ 287,43"
            hint="Lido do código de barras"
            filled
            trailing={<Icon name="pago" size="md" />}
          />
          <Field label="Código" defaultValue="8366000000 2" error="Código incompleto: faltam dígitos" />
        </div>
      </section>

      <section className={styles.sec}>
        <h2>TopBar</h2>
        <div className={styles.box}>
          <TopBar
            title="Avisos"
            backHref="/"
            action={
              <button type="button" aria-label="Filtrar avisos">
                <Icon name="filtro" size="md" />
              </button>
            }
          />
        </div>
      </section>

      <section className={styles.sec}>
        <h2>TabItem e TabBar</h2>
        <div className={styles.row}>
          <div className={styles.tabitem}>
            <TabItem state="off" label="Início" icon="varal" href="/" />
          </div>
          <div className={styles.tabitem}>
            <TabItem state="on" label="Início" icon="varal" href="/" />
          </div>
        </div>
        {(["inicio", "contas", "grupos", "perfil"] as const).map((a) => (
          <div key={a} className={styles.tabbar}>
            <TabBar active={a} />
          </div>
        ))}
      </section>

      <section className={styles.sec}>
        <h2>NavItem e SideNav</h2>
        <div className={styles.navitems}>
          <NavItem label="Início" icon="varal" href="/" />
          <NavItem state="on" label="Início" icon="varal" href="/" />
          <NavItem label="Avisos" icon="sino" href="/avisos" count={3} />
        </div>
        <div className={styles.sidenav}>
          <SideNav
            active="inicio"
            avisos={3}
            espaco={{ iniciais: "FM", nome: "Família Martins", detalhe: "Grupo · 4 membros" }}
            usuario={{ iniciais: "LM", nome: "Luis Martins", detalhe: "luis@email.com" }}
          />
        </div>
      </section>

      <section className={styles.sec}>
        <h2>RadioCard</h2>
        <div role="radiogroup" aria-label="Papel" className={styles.fields}>
          {ordemPapeis.map((p) => (
            <RadioCard key={p} name="vitrine-papel" value={p} state={p === papel ? "on" : "off"} onChange={() => setPapel(p)} {...papeis[p]} />
          ))}
        </div>
      </section>

      <section className={styles.sec}>
        <h2>MemberRow</h2>
        <div className={styles.box}>
          <MemberRow role="admin" initials="LM" name="Luis (você)" detail="Criou o grupo" />
          <MemberRow role="admin" initials="RM" name="Pai" detail="Paga 7 contas" />
          <MemberRow role="pagador" initials="LB" name="Mãe" detail="Paga 4 contas · modo simples" />
          <MemberRow role="observador" initials="AN" name="Ana" detail="Só acompanha" />
          <MemberRow role="membro" initials="JS" name="João" onClick={() => setFolha(true)} />
        </div>
      </section>

      <section className={styles.sec}>
        <h2>HouseCard</h2>
        <div className={styles.row}>
          <HouseCard label="Casa 1" caption="R$ 1.479,60" caption-2="4 contas em novembro" />
          <HouseCard label="Casa 2" caption="R$ 0,00" caption-2="0 contas em novembro" onClick={() => setFolha(true)} />
        </div>
      </section>

      <section className={styles.sec}>
        <h2>BillCard</h2>
        <ul className={styles.fields}>
          {statuses.map((s, i) => (
            <li key={s}>
              <BillCard
                title={["Energia · Enel", "Internet", "Água · Cagece", "Condomínio", "Gás", "Escola", "Seguro"][i]}
                meta={s === "vencida" ? "Venceu 08/11 · Pai paga" : "Vence 14/11 · Mãe paga"}
                value={["R$ 189,90", "R$ 119,90", "R$ 84,35", "R$ 620,00", "R$ 95,00", "R$ 1.250,00", "R$ 210,40"][i]}
                icon={<Icon name={i % 2 ? "manual" : "casa"} size="md" />}
                status={<StatusBadge status={s} />}
                href="#"
                selected={s === "vence"}
                cancelled={s === "cancelada"}
              />
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.sec}>
        <h2>Folha / modal</h2>
        <div className={styles.row}>
          <Button tone="secondary" label="Abrir folha" onClick={() => setFolha(true)} />
        </div>
        <Folha open={folha} onClose={() => setFolha(false)} title="Convidar para o grupo" subtitle="Família Martins · escolha o que a pessoa poderá fazer" actions={<Button label="Compartilhar convite" icon="pedir" width="full" onClick={() => setFolha(false)} />}>
          <p>Folha abaixo de 1024px (sheet-up), modal centralizado a partir de 1024px (modal-pop).</p>
        </Folha>
      </section>
    </div>
  );
}
