// No frame in the Doop (guide varal-ui, "Telas sem frame"): list and creation of groups, built with Button, Field,
// the card of 10/D04 and the sheet/modal of 11/M05. CU02, RF04; RN01.
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Folha } from "@/components/ui/folha";
import { Icon } from "@/components/ui/icon";
import type { GrupoLista } from "@/lib/grupos/client";
import { useCriarGrupo, useGrupos } from "@/lib/grupos/hooks";
import { papeis } from "@/lib/grupos/papeis";
import styles from "./grupos-lista.module.css";

export const hrefDoGrupo = (g: { id: string; papel: GrupoLista["papel"] }) => (g.papel === "pagador" ? `/grupos/${g.id}/simples` : `/grupos/${g.id}`);

function detalhe(g: GrupoLista) {
  const papel = `você é ${papeis[g.papel].title.toLowerCase()}`;
  if (g.membros_qtd == null || g.casas_qtd == null) return papel; // the payer sees only the name (RN07)
  return `${g.membros_qtd} ${g.membros_qtd === 1 ? "membro" : "membros"} · ${g.casas_qtd} ${g.casas_qtd === 1 ? "casa" : "casas"} · ${papel}`;
}

export function GruposLista() {
  const grupos = useGrupos();
  const router = useRouter();
  const [criando, setCriando] = useState(false);

  useEffect(() => {
    // "Criar grupo" in the space selector links here with ?criar=1.
    if (new URLSearchParams(window.location.search).has("criar")) {
      setCriando(true); // eslint-disable-line react-hooks/set-state-in-effect -- reads the URL once, after hydration
      router.replace("/grupos");
    }
  }, [router]);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>Grupos</h1>
        <Button label="Criar grupo" icon="mais" onClick={() => setCriando(true)} aria-haspopup="dialog" />
      </header>
      {grupos.isPending ? (
        <p className={styles.muted} role="status">Carregando grupos…</p>
      ) : grupos.error ? (
        <p className={styles.erro} role="alert">{grupos.error.message}</p>
      ) : grupos.data.length ? (
        <ul className={styles.list}>
          {grupos.data.map((g) => (
            <li key={g.id}>
              <Link className={styles.card} href={hrefDoGrupo(g)}>
                <span className={styles.mark}>
                  <Icon name="grupo" size="md" />
                </span>
                <span className={styles.text}>
                  <b>{g.nome}</b>
                  <small>{detalhe(g)}</small>
                </span>
                <Icon name="chevron" size="md" />
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <p className={styles.muted}>Você ainda não participa de nenhum grupo. Crie um para dividir as contas da casa com a família.</p>
      )}
      <CriarGrupoFolha open={criando} onClose={() => setCriando(false)} />
    </div>
  );
}

function CriarGrupoFolha({ open, onClose }: { open: boolean; onClose: () => void }) {
  const router = useRouter();
  const criar = useCriarGrupo();
  const [nome, setNome] = useState("");
  const [casas, setCasas] = useState<string[]>([""]);

  function fechar() {
    setNome("");
    setCasas([""]);
    criar.reset();
    onClose();
  }

  function enviar(event: FormEvent) {
    event.preventDefault();
    if (!nome.trim()) return;
    criar.mutate(
      { nome: nome.trim(), casas: casas.map((c) => c.trim()).filter(Boolean) },
      {
        onSuccess(grupo) {
          fechar();
          router.push(`/grupos/${grupo.id}`);
          router.refresh(); // the space selector reads the groups from /api/me/
        },
      },
    );
  }

  return (
    <Folha
      open={open}
      onClose={fechar}
      title="Criar grupo"
      subtitle="Você será o admin. Dá para convidar as pessoas depois."
      actions={<Button type="submit" form="grupo-form" label={criar.isPending ? "Criando…" : "Criar grupo"} disabled={criar.isPending || !nome.trim()} />}
    >
      <form id="grupo-form" className={styles.form} onSubmit={enviar}>
        <Field label="Nome do grupo" value={nome} onChange={(e) => setNome(e.target.value)} maxLength={150} required autoFocus placeholder="Família Martins" />
        {casas.map((casa, i) => (
          <Field
            key={i}
            label={`Casa ${i + 1}`}
            hint={i === 0 ? "Opcional. Separe as contas por casa, se houver mais de uma." : undefined}
            value={casa}
            maxLength={150}
            placeholder={i === 0 ? "Casa da praia" : undefined}
            onChange={(e) => setCasas(casas.map((c, j) => (j === i ? e.target.value : c)))}
          />
        ))}
        {casas.length < 20 && (
          <button type="button" className={styles.add} onClick={() => setCasas([...casas, ""])}>
            + Adicionar casa
          </button>
        )}
        {criar.error && <p className={styles.erro} role="alert">{criar.error.message}</p>}
      </form>
    </Folha>
  );
}
