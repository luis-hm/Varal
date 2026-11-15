// Doop: k0kB5dc-Vo / JJvrRugL0_ + SMDsrD8FGT: placeholder until stage 04.
// Keep the stage-00 health check in the client, behind the protected server page.
"use client";

import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api";
import { EmBreve } from "./em-breve";

export function HomePlaceholder() {
  const { data, isPending, isError } = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const status = isPending ? "verificando…" : isError ? "indisponível" : data.status;
  return <EmBreve title="Início"><p role="status">API: {status}</p></EmBreve>;
}
