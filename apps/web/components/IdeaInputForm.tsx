'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Sparkles, ArrowRight, Lightbulb } from 'lucide-react'

interface IdeaInputFormProps {
  onSubmit: (ideaText: string) => void
  loading: boolean
}

const EXAMPLE_IDEAS = [
  "An AI tutoring platform that adapts lesson difficulty in real-time based on student performance",
  "A marketplace connecting remote workers with coworking spaces on a per-hour basis",
  "A SaaS tool that automatically generates compliance documentation for fintech startups",
]

export default function IdeaInputForm({ onSubmit, loading }: IdeaInputFormProps) {
  const [ideaText, setIdeaText] = useState('')
  const [focused, setFocused] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (ideaText.trim().length < 20) {
      setError('Please describe your idea in at least 20 characters.')
      return
    }
    setError('')
    onSubmit(ideaText.trim())
  }

  const handleExample = (example: string) => {
    setIdeaText(example)
    setError('')
  }

  return (
    <div id="idea-input" className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit}>
        <motion.div
          animate={focused ? { boxShadow: '0 0 0 1px rgba(124,58,237,0.6), 0 0 40px rgba(124,58,237,0.2)' } : {}}
          className="glass-card overflow-hidden"
          style={{ borderRadius: '20px' }}
        >
          {/* Textarea */}
          <div className="relative">
            <div className="absolute top-4 left-4 text-slate-600">
              <Lightbulb className="w-5 h-5" />
            </div>
            <textarea
              value={ideaText}
              onChange={(e) => { setIdeaText(e.target.value); setError('') }}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder="Describe your startup idea... (e.g. An AI platform that helps restaurants reduce food waste by predicting demand based on weather and local events)"
              className="w-full bg-transparent pl-12 pr-4 pt-4 pb-4 text-white placeholder-slate-600 resize-none outline-none text-base leading-relaxed"
              rows={4}
              maxLength={2000}
              disabled={loading}
              style={{ minHeight: '120px' }}
            />
          </div>

          {/* Bottom bar */}
          <div className="flex items-center justify-between px-4 py-3"
            style={{ borderTop: '1px solid rgba(255,255,255,0.06)', background: 'rgba(0,0,0,0.2)' }}>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-600">{ideaText.length}/2000</span>
              {error && <span className="text-xs text-red-400">{error}</span>}
            </div>

            <button
              type="submit"
              disabled={loading || ideaText.trim().length < 20}
              className="btn-brand flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none text-sm px-5 py-2.5"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Launching pipeline...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Generate Startup Package
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </motion.div>
      </form>

      {/* Example ideas */}
      {!loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-4"
        >
          <div className="text-xs text-slate-600 mb-2 text-center">Try an example:</div>
          <div className="flex flex-wrap gap-2 justify-center">
            {EXAMPLE_IDEAS.map((ex, i) => (
              <button
                key={i}
                onClick={() => handleExample(ex)}
                className="text-xs px-3 py-1.5 rounded-full transition-all hover:text-purple-300"
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  color: '#94a3b8',
                  maxWidth: '280px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {ex.length > 60 ? ex.slice(0, 57) + '...' : ex}
              </button>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}
