'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import IdeaInputForm from '@/components/IdeaInputForm'
import { Zap, Shield, Code2, BarChart3, Rocket, Users, Star, ArrowRight, CheckCircle, LogIn, LogOut } from 'lucide-react'

const AGENTS = [
  { id: 'idea_validator', name: 'Idea Validator', icon: '🔍', desc: 'Market fit + opportunity score' },
  { id: 'strategy_planner', name: 'Strategy Planner', icon: '📈', desc: 'GTM + monetization model' },
  { id: 'product_architect', name: 'Product Architect', icon: '🏗️', desc: 'Tech stack + system design' },
  { id: 'code_generator', name: 'Code Generator', icon: '💻', desc: 'Full MVP codebase' },
  { id: 'security_reviewer', name: 'Security Reviewer', icon: '🛡️', desc: 'OWASP Top 10 audit' },
  { id: 'copywriter', name: 'Copywriter', icon: '✍️', desc: 'Landing page + pitch deck' },
  { id: 'seo_optimizer', name: 'SEO Optimizer', icon: '🔎', desc: 'Keywords + search strategy' },
]

const FEATURES = [
  { icon: <Zap className="w-6 h-6" />, title: 'Instant Validation', desc: 'AI-powered market analysis with a 0–100 opportunity score in seconds.' },
  { icon: <Code2 className="w-6 h-6" />, title: 'Working MVP Code', desc: 'Full-stack Next.js + FastAPI codebase, ready to run and customize.' },
  { icon: <Shield className="w-6 h-6" />, title: 'Security Audited', desc: 'Every MVP gets an automated OWASP Top 10 security review.' },
  { icon: <BarChart3 className="w-6 h-6" />, title: 'GTM Strategy', desc: 'Pricing tiers, launch channels, and 30/60/90-day launch timeline.' },
  { icon: <Rocket className="w-6 h-6" />, title: 'Auto-Deploy', desc: 'One-click deploy to Vercel — get a live URL instantly.' },
  { icon: <Users className="w-6 h-6" />, title: 'Pitch Deck', desc: '10-slide investor-ready pitch deck generated with your brand.' },
]

const TESTIMONIALS = [
  { name: 'Aria Chen', role: 'Solo Founder', avatar: '👩‍💻', quote: 'I went from idea to live MVP in 3 hours. LaunchForge AI is insane.' },
  { name: 'Marcus Davis', role: 'YC Applicant', avatar: '👨‍🚀', quote: 'The pitch deck it generated got me into 3 interviews. 10/10.' },
  { name: 'Priya Sharma', role: 'Indie Hacker', avatar: '🧑‍💼', quote: "It's like having a CTO, marketer, and designer in one AI tool." },
]

export default function HomePage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [user, setUser] = useState<{name: string; email: string; tier: string} | null>(null)

  useEffect(() => {
    try {
      const stored = localStorage.getItem('lf_user')
      if (stored) setUser(JSON.parse(stored))
    } catch { /* ignore */ }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('lf_token')
    localStorage.removeItem('lf_user')
    setUser(null)
  }

  const handleSubmit = async (ideaText: string) => {
    setLoading(true)
    try {
      const res = await fetch('/api/pipeline/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ideaText, userId: 'anonymous' }),
      })
      if (!res.ok) throw new Error('Failed to start pipeline')
      const data = await res.json()
      router.push(`/dashboard/${data.pipelineId}`)
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden" style={{ background: '#07070f' }}>
      {/* Background orbs */}
      <div className="orb w-[600px] h-[600px] -top-40 -left-40" style={{ background: 'rgba(124,58,237,0.15)' }} />
      <div className="orb w-[500px] h-[500px] top-1/3 -right-40" style={{ background: 'rgba(37,99,235,0.12)' }} />
      <div className="orb w-[400px] h-[400px] bottom-0 left-1/3" style={{ background: 'rgba(6,182,212,0.10)' }} />

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-5 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-2"
        >
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #7c3aed, #2563eb)' }}>
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-lg text-white">LaunchForge AI</span>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-4"
        >
          <span className="text-sm text-slate-400 hidden md:block">For founders who move fast</span>
          {user ? (
            <div className="flex items-center gap-3">
              <div className="text-xs px-2.5 py-1 rounded-full" style={{ background: 'rgba(124,58,237,0.15)', border: '1px solid rgba(124,58,237,0.3)', color: '#a855f7' }}>
                {user.tier.toUpperCase()}
              </div>
              <span className="text-xs text-slate-400 hidden md:block">{user.name}</span>
              <button onClick={handleLogout} className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors">
                <LogOut className="w-3.5 h-3.5" /> Logout
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button onClick={() => router.push('/auth')} className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full text-slate-300 hover:text-white transition-colors"
                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
                <LogIn className="w-3.5 h-3.5" /> Sign in
              </button>
              <div className="flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium"
                style={{ background: 'rgba(124,58,237,0.15)', border: '1px solid rgba(124,58,237,0.3)', color: '#a855f7' }}>
                <Star className="w-3 h-3" /> Beta — Free to try
              </div>
            </div>
          )}
        </motion.div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 text-center px-6 pt-16 pb-12 max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium mb-8"
            style={{ background: 'rgba(124,58,237,0.12)', border: '1px solid rgba(124,58,237,0.25)', color: '#c084fc' }}>
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            8 AI Agents · Live Pipeline · 4-Hour Launch Package
          </div>

          <h1 className="text-5xl md:text-7xl font-black text-white mb-6 leading-tight tracking-tight">
            Your idea →{' '}
            <span className="gradient-text">launch-ready</span>
            <br />startup in 4 hours
          </h1>

          <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-12 leading-relaxed">
            Enter your startup idea. 8 specialized AI agents validate it, build the MVP,
            audit security, write your pitch deck, and create your GTM plan — simultaneously.
          </p>
        </motion.div>

        {/* Idea Input Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.7 }}
        >
          <IdeaInputForm onSubmit={handleSubmit} loading={loading} />
        </motion.div>

        {/* Social proof */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="flex items-center justify-center gap-6 mt-8 text-sm text-slate-500"
        >
          <span className="flex items-center gap-1"><CheckCircle className="w-4 h-4 text-green-500" /> No credit card</span>
          <span className="flex items-center gap-1"><CheckCircle className="w-4 h-4 text-green-500" /> Free to start</span>
          <span className="flex items-center gap-1"><CheckCircle className="w-4 h-4 text-green-500" /> 2 min to first insight</span>
        </motion.div>
      </section>

      {/* Agent Pipeline Visualization */}
      <section className="relative z-10 px-6 py-16 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl font-bold text-white mb-3">8 Agents. One Pipeline.</h2>
          <p className="text-slate-400">Coordinated in parallel for maximum speed.</p>
        </motion.div>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
          {AGENTS.map((agent, i) => (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.07 }}
              className="glass-card glass-card-hover p-4 text-center group cursor-default"
            >
              <div className="text-3xl mb-3">{agent.icon}</div>
              <div className="text-xs font-semibold text-white mb-1">{agent.name}</div>
              <div className="text-xs text-slate-500">{agent.desc}</div>
              <div className="mt-3 w-full h-0.5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                style={{ background: 'linear-gradient(90deg, #7c3aed, #06b6d4)' }} />
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="relative z-10 px-6 py-16 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl font-bold text-white mb-3">
            Everything a founder needs to launch
          </h2>
          <p className="text-slate-400">One input. Complete launch package.</p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="glass-card glass-card-hover p-6"
            >
              <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
                style={{ background: 'rgba(124,58,237,0.15)', color: '#a855f7', border: '1px solid rgba(124,58,237,0.2)' }}>
                {f.icon}
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{f.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Testimonials */}
      <section className="relative z-10 px-6 py-16 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl font-bold text-white mb-3">Founders love it</h2>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-6">
          {TESTIMONIALS.map((t, i) => (
            <motion.div
              key={t.name}
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="glass-card p-6"
            >
              <div className="flex items-center gap-1 mb-4">
                {[...Array(5)].map((_, j) => <Star key={j} className="w-4 h-4 fill-amber-400 text-amber-400" />)}
              </div>
              <p className="text-slate-300 text-sm leading-relaxed mb-4">"{t.quote}"</p>
              <div className="flex items-center gap-3">
                <span className="text-2xl">{t.avatar}</span>
                <div>
                  <div className="text-sm font-semibold text-white">{t.name}</div>
                  <div className="text-xs text-slate-500">{t.role}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 px-6 py-20 max-w-3xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <div className="glass-card p-12" style={{ background: 'rgba(124,58,237,0.08)', border: '1px solid rgba(124,58,237,0.2)' }}>
            <h2 className="text-4xl font-black text-white mb-4">
              Ready to <span className="gradient-text">forge</span> your startup?
            </h2>
            <p className="text-slate-400 mb-8">Join thousands of founders who launched with AI.</p>
            <button
              onClick={() => document.getElementById('idea-input')?.scrollIntoView({ behavior: 'smooth' })}
              className="btn-brand inline-flex items-center gap-2 text-base px-8 py-4"
            >
              Start for free <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t text-center py-8 text-sm text-slate-600"
        style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <p>© 2026 LaunchForge AI · Built on <span className="text-purple-500">Complete.dev</span> · Powered by GPT-5</p>
      </footer>
    </div>
  )
}
