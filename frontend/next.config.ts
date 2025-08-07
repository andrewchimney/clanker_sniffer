
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://orchestrator_api:8000/api/:path*', // Docker service name
      },
    ];
  },
};

module.exports = nextConfig;

