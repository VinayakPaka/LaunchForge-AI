/** @type {import('next').NextConfig} */
const nextConfig = {
  // SVG images are now served internally via /api/images/svg (FastAPI backend).
  // No external image hostname needed.
  images: {
    dangerouslyAllowSVG: true,
    contentDispositionType: 'attachment',
    remotePatterns: [],
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
