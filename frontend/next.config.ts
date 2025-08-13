import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
    // ⛔ Disable Lightning CSS
    optimizeCss: false,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://orchestrator_api:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;

