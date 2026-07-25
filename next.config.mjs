import path from 'node:path';
import { fileURLToPath } from 'node:url';

const projectRoot = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: projectRoot,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination:
          process.env.NODE_ENV === 'development'
            ? `${(
                process.env.GRIDMATCH_API_INTERNAL_URL ??
                'http://127.0.0.1:8000'
              ).replace(/\/$/, '')}/api/:path*`
            : '/api/'
      }
    ];
  }
};

export default nextConfig;
