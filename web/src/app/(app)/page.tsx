// Doop: k0kB5dc-Vo / 02 · Início (JJvrRugL0_) + D02 · Início (SMDsrD8FGT): "Em breve" until stage 04.
// The API healthcheck line from stage 00 stays here until then.
"use client";

import { useQuery } from "@tanstack/react-query";
import { EmBreve } from "@/components/layout/em-breve";
import { getHealth } from "@/lib/api";

export default function Home() {
  const { data, isPending, isError } = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const status = isPending ? "verificando…" : isError ? "indisponível" : data.status;
  return (
    <EmBreve title="Início">
      <p role="status">API: {status}</p>
    </EmBreve>
  );
}
