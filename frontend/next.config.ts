import type { NextConfig } from "next";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  devIndicators: false,
  experimental: {
    workerThreads: true,
  },
  turbopack: {
    root: rootDir,
  },
};

export default nextConfig;
