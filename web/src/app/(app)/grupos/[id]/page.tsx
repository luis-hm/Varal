// Doop: k0kB5dc-Vo / SfhuKVOQIF (10 · Grupo) + 5UzCB5yNaI (D04 · Grupo); invite bkv_O9ohNO (11) + 8XSFrkwy2d (M05).
// CU02, CU03, CU04; RF04–RF07.
import { GrupoPagina } from "@/components/groups/grupo-pagina";

export const instant = false;

export default async function Grupo({ params }: PageProps<"/grupos/[id]">) {
  const { id } = await params;
  return <GrupoPagina id={id} />;
}
