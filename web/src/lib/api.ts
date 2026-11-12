import type { components } from "@/types/api";

export type Health = components["schemas"]["Health"];

export async function getHealth(): Promise<Health> {
  const res = await fetch("/api/health/");
  if (!res.ok) throw new Error(`health ${res.status}`);
  return res.json();
}
