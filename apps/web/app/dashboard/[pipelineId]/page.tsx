'use client'

import { useParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { usePipelineSSE } from '@/hooks/usePipelineSSE'
import AgentStatusCard from '@/components/AgentStatusCard'
import PipelineProgress from '@/components/PipelineProgress'
import { Zap, ArrowRight, Wifi, WifiOff, Home } from 'lucide-react'

const AGENT_META: Record<string, { name: string; icon: string; description: string }> = {
  idea_validator:    { name: 'Idea Validator',    icon: '🔍', description: 'Market fit + opportunity score' },
  strategy_planner:  { name: 'Strategy Planner',  icon: '📈', description: 'GTM + monetization model' },
  product_architect: { name: 'Product Architect', icon: '🏗️', description: 'Tech stack + system design' },
  code_generator:    { name: 'Code Generator',    icon: '💻', description: 'Full MVP codebase' },
  security_reviewer: { name: 'Security Reviewer', icon: '🛡️', description: 'OWASP Top 10 audit' },
  copywriter:        { name: 'Copywriter',        icon: '✍️', description: 'Landing page + pitch deck' },
  seo_optimizer:     { name: 'SEO Optimizer',     icon: '🔎', description: 'Keywords + search strategy' },
}

const AGENT_ORDER = [
  'idea_validator', 'strategy_planner', 'product_architect',
  'code_generator', 'security_reviewer', 'copywriter', 'seo_optimizer'
]

export default function DashboardPage() {
  const { pipelineId } = useParams<{ pipelineId: string }>()
  const router = useRouter()
  const { state, connected, error } = usePipelineSSE(pipelineId)

  return (
    <div className="min-h-screen" style={{ background: '#07070f' }}>
      {/* Background orbs */}
      <div className="orb w-[500px] h-[500px] -top-40 -right-40" style={{ background: 'rgba(124,58,237,0.12)' }} />
      <div className="orb w-[400px] h-[400px] bottom-0 -left-20" style={{ background: 'rgba(37,99,235,0.10)' }} />

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-5 max-w-5xl mx-auto">
        <button onClick={() => router.push('/')} className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #7c3aed, #2563eb)' }}>
            <Zap className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="font-semibold text-sm text-white">LaunchForge AI</span>
        </button>

        <div className="flex items-center gap-3">
          {/* Connection indicator */}
          <div className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full ${connected ? 'text-green-400' : 'text-slate-500'}`}
            style={{ background: connected ? 'rgba(34,197,94,0.1)' : 'rgba(255,255,255,0.04)', border: `1px solid ${connected ? 'rgba(34,197,94,0.3)' : 'rgba(255,255,255,0.08)'}` }}>
            {connected ? <><Wifi className="w-3 h-3" /> Live</> : <><WifiOff className="w-3 h-3" /> Offline</>}
          </div>
          <button onClick={() => router.push('/')} className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors">
            <Home className="w-3.5 h-3.5" /> Home
          </button>
        </div>
      </nav>

      <main className="relative z-10 max-w-5xl mx-auto px-6 pb-20">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="text-3xl font-black text-white mb-2">
            🚀 Forging your startup
          </h1>
          {state?.ideaText && (
            <p className="text-slate-400 text-sm max-w-2xl">
              Idea: <span className="text-slate-300">"{state.ideaText.slice(0, 120)}{state.ideaText.length > 120 ? '...' : ''}"</span>
            </p>
          )}
          {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
        </motion.div>

        {/* Pipeline Progress */}
        {state && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
            <PipelineProgress
              agents={state.agents || {}}
              pipelineStatus={state.status}
            />
          </motion.div>
        )}

        {/* Agent Cards */}
        <div className="space-y-3">
          {AGENT_ORDER.map((agentId, i) => {
            const meta = AGENT_META[agentId]
            const agentState = state?.agents?.[agentId]
            const status = agentState?.status || 'queued'

            return (
              <motion.div
                key={agentId}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <AgentStatusCard
                  agentId={agentId}
                  name={meta.name}
                  icon={meta.icon}
                  description={meta.description}
                  status={status}
                  startedAt={agentState?.startedAt}
                  completedAt={agentState?.completedAt}
                  result={agentState?.result}
                  error={agentState?.error}
                />
              </motion.div>
            )
          })}
        </div>

        {/* Complete CTA */}
        {state?.status === 'complete' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8"
          >
            <div className="glass-card p-8 text-center" style={{ border: '1px solid rgba(34,197,94,0.3)', background: 'rgba(34,197,94,0.06)' }}>
              <div className="text-5xl mb-4">🎉</div>
              <h2 className="text-2xl font-black text-white mb-2">Your startup package is ready!</h2>
              <p className="text-slate-400 mb-6">All 7 agents completed. View your full launch package now.</p>
              <button
                onClick={() => router.push(`/results/${pipelineId}`)}
                className="btn-brand inline-flex items-center gap-2"
              >
                View Launch Package <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </motion.div>
        )}

        {/* Loading skeleton when no state yet */}
        {!state && !error && (
          <div className="space-y-3">
            {AGENT_ORDER.map(id => (
              <div key={id} className="glass-card p-4 animate-pulse">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-white/5" />
                  <div className="space-y-1.5 flex-1">
                    <div className="h-3 bg-white/5 rounded w-1/4" />
                    <div className="h-2 bg-white/5 rounded w-1/3" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
