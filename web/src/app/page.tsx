// Etapa 00: technical page with no Doop frame. Replaced by "02 · Início" (JJvrRugL0_) in stage 04.
"use client";

import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api";

export default function Home() {
  const { data, isPending, isError } = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const status = isPending ? "verificando…" : isError ? "indisponível" : data.status;
  return (
    <main>
      <h1>varal</h1>
      <p role="status">API: {status}</p>
    </main>
  );
}
