// Doop: k0kB5dc-Vo / NoticeRow, 02 · Início + D02 · Início e 04 · Avisos + D06 · Avisos.
"use client";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { Icon } from "@/components/ui/icon";
import { ApiError } from "@/lib/grupos/client";
import type { Notificacao } from "@/lib/notificacoes/client";
import { useLeituraAvisos } from "@/lib/notificacoes/hooks";
import { NoticeRow } from "./notice-row";

function tom(tipo: Notificacao["tipo"]) {
  if (tipo === "pagamento") return "pago";
  if (tipo === "venceu_1" || tipo === "cancelada_rn32") return "vencida";
  if (tipo === "boleto_ausente") return "aguardando";
  if (tipo === "vence_3" || tipo === "vence_hoje") return "vence";
  return "info";
}
function hora(data: string) { return new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Fortaleza", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }).format(new Date(data)); }
export function AvisoLinha({ aviso, onClick, disabled }: { aviso: Notificacao; onClick: () => void; disabled?: boolean }) {
  const tone = tom(aviso.tipo);
  return <NoticeRow title={aviso.titulo} text={aviso.texto} time={hora(aviso.criado_em)} unread={aviso.lido_em ? "no" : "yes"} tone={tone} icon={<Icon name={tone === "pago" ? "pago" : tone === "info" ? "sino" : "alerta"} size="md" />} onClick={onClick} disabled={disabled} />;
}
export function useAbrirAviso(user: string, onNavigate?: () => void) {
  const router = useRouter();
  const leitura = useLeituraAvisos(user);
  const [erro, setErro] = useState("");
  const busy = useRef(false);
  async function abrir(aviso: Notificacao) {
    if (busy.current) return;
    busy.current = true;
    setErro("");
    try {
      // Even a read notice is revalidated immediately before navigation.
      await leitura.um.mutateAsync(aviso.id);
      if (aviso.destino && /^\/contas\/[0-9a-f-]+\/?$/i.test(aviso.destino)) { onNavigate?.(); router.push(aviso.destino); }
    } catch (error) {
      setErro(error instanceof ApiError && error.status === 404 ? "Este aviso não está mais disponível." : "Não foi possível abrir o aviso. Tente novamente.");
    } finally { busy.current = false; }
  }
  return { abrir, erro, leitura };
}
