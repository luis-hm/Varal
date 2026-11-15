// Doop: k0kB5dc-Vo / mIvLheR2TS (13 · Modo simples) + YTtAtGSyCI (D05) as reference until stage 10.
// CU11 (Q5: the payer's bills, read only), RF06 (leave the group, any role); RN07: the payer has no group page.
import { notFound, redirect } from "next/navigation";
import { ContasPagador } from "@/components/bills/contas-pagador";
import { SairDoGrupo } from "@/components/groups/sair-do-grupo";
import { TopBar } from "@/components/layout/top-bar";
import { requireUser } from "@/lib/auth/server";
import styles from "./simples.module.css";

export const instant = false;

export default async function ModoSimples({ params }: PageProps<"/grupos/[id]/simples">) {
  const { id } = await params;
  const grupo = (await requireUser()).grupos.find((g) => g.id === id);
  if (!grupo) notFound();
  if (grupo.papel !== "pagador") redirect(`/grupos/${id}`);
  return (
    <>
      <TopBar title={grupo.nome} />
      <div className={styles.body}>
        <ContasPagador grupoId={grupo.id} />
        <SairDoGrupo grupoId={grupo.id} grupoNome={grupo.nome} />
      </div>
    </>
  );
}
