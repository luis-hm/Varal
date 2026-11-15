// Doop: k0kB5dc-Vo / layout GJDSPaQbio (01 · Entrar) + 7JTmWMAJup (D01 · Entrar); acceptance has no frame (guide varal-ui).
// CU03, RF05; RN24, RN31.
import { Suspense } from "react";
import { AceiteConvite } from "@/components/groups/aceite-convite";

async function Aceite({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return <AceiteConvite token={token} />;
}

export default function Convite({ params }: PageProps<"/c/[token]">) {
  return <Suspense fallback={<p role="status">Abrindo o convite…</p>}><Aceite params={params} /></Suspense>;
}
