import path from 'node:path';
import { fileURLToPath } from 'node:url';

const projectRoot = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: projectRoot,
  async rewrites() {
    const apiBase = (
      process.env.GRIDMATCH_API_INTERNAL_URL ??
      'http://127.0.0.1:8000'
    ).replace(/\/$/, '');
    return [
      {
        source: '/api/:path*',
        destination:
          process.env.NODE_ENV === 'development'
            ? `${apiBase}/api/:path*`
            : '/api/'
      },
      {
        source: '/health',
        destination:
          process.env.NODE_ENV === 'development'
            ? `${apiBase}/health`
            : '/api/'
      }
    ];
  }
};

export default nextConfig;
