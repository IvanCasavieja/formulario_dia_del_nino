import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // /shared (validationConstants.json - the single source of truth also read by the
  // backend) lives one level above this package, outside Turbopack's auto-detected
  // project root (frontend/, where package-lock.json is). Widening the root to the
  // monorepo root is what lets lib/validationConstants.ts import it directly instead
  // of hand-copying values that could silently drift from the backend's copy.
  turbopack: {
    root: path.join(__dirname, ".."),
  },
};

export default nextConfig;
