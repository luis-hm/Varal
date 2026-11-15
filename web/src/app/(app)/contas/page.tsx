// Doop: k0kB5dc-Vo / 03 · Contas (bdiED7Q0I-) + D03 · Contas + Detalhe (cWdVUX2y8H); CU06; RF13, RN12, D2, Q14.
import { Suspense } from "react";
import { ContasPagina } from "@/components/bills/contas-pagina";

export const instant = false;

export default function Contas() {
  return (
    <Suspense>
      <ContasPagina />
    </Suspense>
  );
}
