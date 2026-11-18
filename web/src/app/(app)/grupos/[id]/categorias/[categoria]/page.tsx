// Doop: k0kB5dc-Vo / 03 · Contas (bdiED7Q0I-) + D03 (cWdVUX2y8H) in a category context; COR-11.
import { Suspense } from "react";
import { CategoriaPagina } from "@/components/groups/categoria-pagina";

export const instant = false;

export default async function Categoria({ params }: PageProps<"/grupos/[id]/categorias/[categoria]">) {
  const { id, categoria } = await params;
  return (
    <Suspense>
      <CategoriaPagina grupoId={id} categoriaId={categoria} />
    </Suspense>
  );
}
