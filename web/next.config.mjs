/** @type {import('next').NextConfig} */

// The wheel serves this export from the site root, so the default base path is
// empty. A GitHub project site serves it from /<repo>/ instead, so the Pages
// workflow sets NEXT_PUBLIC_BASE_PATH and gets a second, separate build. Never
// copy a base-path build into memory_arena/static/: every wheel asset would 404.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const nextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  ...(basePath ? { basePath, assetPrefix: basePath } : {}),
};

export default nextConfig;
