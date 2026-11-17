// Doop: k0kB5dc-Vo / 02 · Início (JJvrRugL0_) + D02 · Início (SMDsrD8FGT); CU06; RF13, RN12, RN13, Q4, Q9, Q12, Q23.
import { Inicio } from "@/components/bills/inicio";
import { dadosInicio } from "@/lib/contas/inicio-server";

export const instant = false;

export default async function Home() {
  return <Inicio inicial={await dadosInicio()} />;
}
