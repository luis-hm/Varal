// Doop: k0kB5dc-Vo / shell JJvrRugL0_ + SMDsrD8FGT; CU01 (authenticated access).
import { ProtectedShell } from "@/components/auth/protected-shell";

// A protected segment waits for the real session; it cannot validate with anonymous prefetch data.
export const instant = false;

export default function AppLayout({ children }: LayoutProps<"/">) {
  return <ProtectedShell>{children}</ProtectedShell>;
}
