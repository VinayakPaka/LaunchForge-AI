'use client'

import { motion } from 'framer-motion'
import { Zap } from 'lucide-react'

interface AgentStatus {
  agentId: string
  status: 'queued' | 'in_progress' | 'complete' | 'failed'
}

interface PipelineProgressProps {
  agents: Record<string, AgentStatus>
  pipelineStatus: string
}

const AGENT_ORDER = [
  'idea_validator', 'strategy_planner', 'product_architect',
  'code_generator', 'security_reviewer', 'copywriter', 'seo_optimizer'
]

export default function PipelineProgress({ agents, pipelineStatus }: PipelineProgressProps) {
  const totalAgents = AGENT_ORDER.length
  const completeCount = AGENT_ORDER.filter(id => agents[id]?.status === 'complete').length
  const progressPct = Math.round((completeCount / totalAgents) * 100)

  const statusLabel = pipelineStatus === 'complete'
    ? '✅ All agents complete!'
    : pipelineStatus === 'failed'
    ? '❌ Pipeline failed'
    : `Running · ${completeCount}/${totalAgents} agents complete`

  return (
    <div className="glass-card p-5 mb-6">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #7c3aed, #2563eb)' }}>
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-white text-sm">Agent Pipeline</span>
        </div>
        <span className="text-sm text-slate-400">{statusLabel}</span>
      </div>

      {/* Progress bar */}
      <div className="w-full h-2.5 rounded-full mb-2" style={{ background: 'rgba(255,255,255,0.06)' }}>
        <motion.div
          className="h-full rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${progressPct}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          style={{
            background: pipelineStatus === 'complete'
              ? '#22c55e'
              : pipelineStatus === 'failed'
              ? '#ef4444'
              : 'linear-gradient(90deg, #7c3aed, #2563eb, #06b6d4)',
            backgroundSize: '200% 100%',
          }}
        />
      </div>

      <div className="flex items-center justify-between text-xs text-slate-600">
        <span>{progressPct}% complete</span>
        <span>{completeCount} / {totalAgents} agents done</span>
      </div>
    </div>
  )
}
