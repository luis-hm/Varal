// Doop: k0kB5dc-Vo / no Perfil screen in the Doop (D5); stays "Em breve".
import { EmBreve } from "@/components/layout/em-breve";
import { LogoutButton } from "@/components/auth/logout-button";

export const instant = false;

export default function Perfil() {
  return <EmBreve title="Perfil"><LogoutButton /></EmBreve>;
}
