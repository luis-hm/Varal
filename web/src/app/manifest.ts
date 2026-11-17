import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Varal",
    short_name: "Varal",
    description: "Nenhuma conta vence sem que alguém saiba.",
    start_url: "/",
    scope: "/",
    display: "standalone",
    // Manifest colors must be concrete CSS colors; values match --color-bg and --color-ink.
    background_color: "rgb(246 247 249)",
    theme_color: "rgb(28 37 65)",
    icons: [
      { src: "/icons/varal-192-v1.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/varal-512-v1.png", sizes: "512x512", type: "image/png" },
    ],
  };
}
