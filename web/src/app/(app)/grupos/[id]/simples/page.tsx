// Doop: k0kB5dc-Vo / 13 · Modo simples (mIvLheR2TS) + D05 (YTtAtGSyCI); CU11, Q10-11.
import { redirect } from "next/navigation";
import { ContasSimples } from "@/components/simple/contas-simples";
import { requireUser } from "@/lib/auth/server";
export const instant = false;
export default async function ModoSimples({ params, searchParams }: PageProps<"/grupos/[id]/simples">) {
  const { id } = await params;
  const user = await requireUser();
  const grupo = user.grupos.find((g) => g.id === id);
  if (!grupo) redirect("/grupos");
  if (grupo.papel !== "pagador") redirect(`/grupos/${id}`);
  const filtros = await searchParams;
  return <ContasSimples key={`${user.id}:${grupo.id}:${filtros.pagas === "1"}`} grupoId={grupo.id} grupoNome={grupo.nome} nome={user.nome || user.email.split("@")[0]} inicialPagas={filtros.pagas === "1"} />;
}
