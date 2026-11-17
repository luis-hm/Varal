import type { NextConfig } from "next";

const apiUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // Django routes end in "/"; keep the slash so the proxy does not bounce between redirects.
  skipTrailingSlashRedirect: true,
  // RN31: invite tokens are bearer credentials; keep them out of the dev request log.
  logging: { incomingRequests: { ignore: [/\/c\//, /\/api\/convites\//, /\/confirmar-email\//, /\/api\/auth\/browser\/v1\/auth\/email\/verify/, /\/entrar\/retorno/, /\/api\/auth\/google\/tickets\//] } },
  async headers() {
    return [
      { source: "/:path*", headers: [{ key: "X-Frame-Options", value: "DENY" }] },
      // Pages that may carry an invite token in the URL never send it as Referer.
      { source: "/c/:path*", headers: [{ key: "Referrer-Policy", value: "no-referrer" }] },
      { source: "/(entrar|criar-conta)/:path*", headers: [{ key: "Referrer-Policy", value: "no-referrer" }] },
      { source: "/entrar/retorno", headers: [{ key: "Cache-Control", value: "private, no-store" }, { key: "Referrer-Policy", value: "no-referrer" }] },
      { source: "/confirmar-email/:path*", headers: [{ key: "Referrer-Policy", value: "no-referrer" }, { key: "Cache-Control", value: "private, no-store" }] },
      ...["/", "/contas/:path*", "/grupos/:path*", "/avisos/:path*", "/perfil/:path*"].map((source) => ({ source, headers: [{ key: "Cache-Control", value: "private, no-store" }] })),
    ];
  },
  // Same-origin /api keeps the auth cookies first-party (allauth headless, stage 02).
  async rewrites() {
    return [
      // allauth's native endpoints have no trailing slash; preserve method, body and cookies.
      { source: "/api/auth/:path*", destination: `${apiUrl}/api/auth/:path*` },
      { source: "/api/:path*/", destination: `${apiUrl}/api/:path*/` },
    ];
  },
};

export default nextConfig;
