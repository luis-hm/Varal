// Doop: k0kB5dc-Vo / página 04 · Componentes + frames Logo e Ícones. Development-only showcase.
import { notFound } from "next/navigation";
import { ProtectedShell } from "@/components/auth/protected-shell";
import { Vitrine } from "./vitrine";

export const instant = false;

export default function ComponentesPage() {
  // Decide before entering the session's streaming boundary so production sends a real HTTP 404.
  if (process.env.NODE_ENV === "production") notFound();
  return <ProtectedShell><Vitrine /></ProtectedShell>;
}
