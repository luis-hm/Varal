// Doop: k0kB5dc-Vo / 07 · Detalhe da conta (efJzW9e5vx) + D03 · Contas + Detalhe (cWdVUX2y8H); CU06, CU07;
// RF12, RN06 (404 for hidden bills), RN22, RN30, CA30.
import { Suspense } from "react";
import { ContasPagina } from "@/components/bills/contas-pagina";

export const instant = false;

export default async function Conta({ params }: PageProps<"/contas/[id]">) {
  const { id } = await params;
  return (
    <Suspense>
      <ContasPagina contaId={id} />
    </Suspense>
  );
}
