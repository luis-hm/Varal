// Stored recurrence states and pause reasons shown as people read them (audit: no raw API values on screen).
const ESTADOS: Record<string, string> = { ativa: "Ativa", pausada: "Pausada", encerrada: "Encerrada" };
const MOTIVOS: Record<string, string> = {
  manual: "pausada por alguém do espaço",
  sem_audiencia: "ninguém mais pode ver esta conta; ajuste quem vê para retomar",
};
export const estadoRecorrencia = (estado: string) => ESTADOS[estado] ?? estado;
export const motivoPausa = (motivo: string) => MOTIVOS[motivo] ?? motivo;
