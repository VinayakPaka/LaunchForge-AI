import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'LaunchForge AI — Idea to Live Startup in 4 Hours',
  description: '8 specialized AI agents validate your startup idea, generate working MVP code, run a security audit, and create your complete marketing kit — all in under 4 hours.',
  keywords: 'AI startup generator, MVP builder AI, startup idea validator, launch startup fast',
  openGraph: {
    title: 'LaunchForge AI',
    description: 'Turn your startup idea into a launch-ready package with 8 coordinated AI agents.',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased min-h-screen" style={{ background: '#07070f' }}>
        {children}
      </body>
    </html>
  )
}
