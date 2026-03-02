/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'image.pollinations.ai',
        pathname: '/**',
      },
    ],
  },
  async rewrites() {
    return [
      {
        // Proxy all /api/* calls to the FastAPI backend (internal port 8001)
        source: '/api/:path*',
        destination: 'http://localhost:8001/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig
