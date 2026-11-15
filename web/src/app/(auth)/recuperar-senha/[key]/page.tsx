// Doop: k0kB5dc-Vo / GJDSPaQbio + 7JTmWMAJup; CU01. New-password state approved in chat.
import { Suspense } from "react";
import { AuthForm } from "@/components/auth/auth-form";

async function ResetForm({ params }: { params: Promise<{ key: string }> }) {
  const { key } = await params;
  return <AuthForm mode="reset" resetKey={key} />;
}

export default function NovaSenha({ params }: { params: Promise<{ key: string }> }) {
  return <Suspense fallback={<p role="status">Conferindo o link…</p>}><ResetForm params={params} /></Suspense>;
}
