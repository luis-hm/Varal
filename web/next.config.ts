import type { NextConfig } from "next";

const apiUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // Django routes end in "/"; keep the slash so the proxy does not bounce between redirects.
  skipTrailingSlashRedirect: true,
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
