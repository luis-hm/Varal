// Doop: k0kB5dc-Vo / página 04 · Componentes + frames Logo e Ícones. Development-only showcase.
import { notFound } from "next/navigation";
import { Vitrine } from "./vitrine";

export default function ComponentesPage() {
  if (process.env.NODE_ENV === "production") notFound();
  return <Vitrine />;
}
