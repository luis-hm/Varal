// Doop: k0kB5dc-Vo / mIvLheR2TS (13 · Modo simples) + YTtAtGSyCI (D05) only as reference: "Em breve" until stage 10.
// CU11 (placeholder), RF06 (leave the group, any role); RN07: the payer has no group page.
import { notFound, redirect } from "next/navigation";
import { SairDoGrupo } from "@/components/groups/sair-do-grupo";
import { EmBreve } from "@/components/layout/em-breve";
import { requireUser } from "@/lib/auth/server";

export const instant = false;

export default async function ModoSimples({ params }: PageProps<"/grupos/[id]/simples">) {
  const { id } = await params;
  const grupo = (await requireUser()).grupos.find((g) => g.id === id);
  if (!grupo) notFound();
  if (grupo.papel !== "pagador") redirect(`/grupos/${id}`);
  return (
    <EmBreve title={grupo.nome}>
      <SairDoGrupo grupoId={grupo.id} grupoNome={grupo.nome} />
    </EmBreve>
  );
}
