'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, XCircle, Clock, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

interface AgentStatusCardProps {
  agentId: string
  name: string
  icon: string
  description: string
  status: 'queued' | 'in_progress' | 'complete' | 'failed'
  startedAt?: string
  completedAt?: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  result?: any
  error?: string
}

const STATUS_CONFIG = {
  queued: {
    label: 'Queued',
    icon: <Clock className="w-4 h-4" />,
    color: '#64748b',
    bg: 'rgba(100,116,139,0.1)',
    border: 'rgba(100,116,139,0.2)',
  },
  in_progress: {
    label: 'Running',
    icon: <Loader2 className="w-4 h-4 animate-spin" />,
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.1)',
    border: 'rgba(245,158,11,0.3)',
  },
  complete: {
    label: 'Complete',
    icon: <CheckCircle className="w-4 h-4" />,
    color: '#22c55e',
    bg: 'rgba(34,197,94,0.1)',
    border: 'rgba(34,197,94,0.3)',
  },
  failed: {
    label: 'Failed',
    icon: <XCircle className="w-4 h-4" />,
    color: '#ef4444',
    bg: 'rgba(239,68,68,0.1)',
    border: 'rgba(239,68,68,0.3)',
  },
}

function elapsed(start?: string, end?: string): string {
  if (!start) return ''
  const s = new Date(start).getTime()
  const e = end ? new Date(end).getTime() : Date.now()
  const sec = Math.round((e - s) / 1000)
  if (sec < 60) return `${sec}s`
  return `${Math.floor(sec / 60)}m ${sec % 60}s`
}

export default function AgentStatusCard({
  agentId, name, icon, description, status, startedAt, completedAt, result, error
}: AgentStatusCardProps) {
  const [expanded, setExpanded] = useState(false)
  const cfg = STATUS_CONFIG[status]

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-card overflow-hidden"
      style={{
        border: `1px solid ${cfg.border}`,
        boxShadow: status === 'in_progress' ? `0 0 20px ${cfg.bg}` : undefined,
      }}
    >
      {/* Progress indicator for in_progress */}
      {status === 'in_progress' && (
        <div className="h-0.5 w-full progress-bar-fill" />
      )}
      {status === 'complete' && (
        <div className="h-0.5 w-full" style={{ background: '#22c55e' }} />
      )}

      <div className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{icon}</span>
            <div>
              <div className="text-sm font-semibold text-white">{name}</div>
              <div className="text-xs text-slate-500">{description}</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Elapsed time */}
            {startedAt && (
              <span className="text-xs text-slate-600 font-mono">
                {elapsed(startedAt, completedAt)}
              </span>
            )}

            {/* Status badge */}
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
              style={{ background: cfg.bg, border: `1px solid ${cfg.border}`, color: cfg.color }}>
              {cfg.icon}
              {cfg.label}
            </div>

            {/* Expand toggle for complete agents */}
            {(status === 'complete' || status === 'failed') && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-slate-500 hover:text-slate-300 transition-colors"
              >
                {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
            )}
          </div>
        </div>

        {/* Expandable result preview */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="mt-4 pt-4" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                {error ? (
                  <div className="text-xs text-red-400 font-mono">{error}</div>
                ) : result ? (
                  <ResultPreview agentId={agentId} result={result} />
                ) : null}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}

/** Renders a smart preview of the agent result based on its type */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ResultPreview({ agentId, result }: { agentId: string; result: any }) {
  if (agentId === 'idea_validator') {
    return (
      <div className="space-y-2">
        {result.refinedIdea && <p className="text-sm text-slate-300">{String(result.refinedIdea)}</p>}
        {result.marketScore !== undefined && (
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-500">Market Score</span>
            <div className="flex-1 h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.06)' }}>
              <div className="h-full rounded-full" style={{
                width: `${result.marketScore}%`,
                background: `hsl(${Number(result.marketScore) * 1.2}, 80%, 50%)`
              }} />
            </div>
            <span className="text-sm font-bold text-white">{String(result.marketScore)}/100</span>
          </div>
        )}
        {result.recommendation && (
          <div className="text-xs px-2 py-1 rounded" style={{ background: 'rgba(34,197,94,0.1)', color: '#86efac' }}>
            {String(result.recommendation)}
          </div>
        )}
      </div>
    )
  }

  if (agentId === 'security_reviewer') {
    return (
      <div className="space-y-2">
        {result.badge && (
          <div className="text-xs px-2 py-1 rounded inline-block font-mono"
            style={{ background: 'rgba(34,197,94,0.1)', color: '#86efac' }}>
            🛡️ {String(result.badge)}
          </div>
        )}
        {result.overallScore !== undefined && (
          <p className="text-xs text-slate-400">Security Score: <span className="text-white font-bold">{String(result.overallScore)}/100</span></p>
        )}
      </div>
    )
  }

  // Generic: show first 3 string values
  const entries = Object.entries(result).filter(([, v]) => typeof v === 'string').slice(0, 3)
  return (
    <div className="space-y-1">
      {entries.map(([k, v]) => (
        <div key={k} className="text-xs">
          <span className="text-slate-500 capitalize">{k.replace(/([A-Z])/g, ' $1')}: </span>
          <span className="text-slate-300">{String(v).slice(0, 120)}</span>
        </div>
      ))}
    </div>
  )
}
