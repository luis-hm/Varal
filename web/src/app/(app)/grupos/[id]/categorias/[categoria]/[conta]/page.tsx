// Doop: k0kB5dc-Vo / 07 · Detalhe da conta (efJzW9e5vx) + D03 (cWdVUX2y8H) in a category context; COR-11.
import { Suspense } from "react";
import { CategoriaPagina } from "@/components/groups/categoria-pagina";

export const instant = false;

export default async function ContaDaCategoria({ params }: PageProps<"/grupos/[id]/categorias/[categoria]/[conta]">) {
  const { id, categoria, conta } = await params;
  return (
    <Suspense>
      <CategoriaPagina grupoId={id} categoriaId={categoria} contaId={conta} />
    </Suspense>
  );
}
