"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function criarQueryClient() {
  // Mutations must run immediately and surface network failure; never queue a
  // financial action (or logout cleanup) to resume after reconnecting.
  return new QueryClient({ defaultOptions: { mutations: { networkMode: "always", retry: false } } });
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(criarQueryClient);
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
