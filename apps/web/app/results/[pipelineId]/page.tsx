'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  CheckCircle, Download, ExternalLink, Code2, Shield, BarChart3,
  Target, Globe, ArrowLeft, Zap, Copy, ChevronDown, ChevronUp
} from 'lucide-react'

/** Extract a display string from a keyword entry that may be a string or object */
function extractKeyword(kw: unknown): string {
  if (typeof kw === 'string') return kw
  if (typeof kw === 'object' && kw !== null) {
    const o = kw as Record<string, unknown>
    return String(o.keyword ?? o.term ?? o.name ?? o.value ?? Object.values(o)[0] ?? '')
  }
  return String(kw)
}

/** Safely render a value that might be a string, number, or object */
function safeStr(val: unknown): string {
  if (val === null || val === undefined) return ''
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

/**
 * Image with graceful fallback.
 * Shows a styled placeholder when the external image URL fails to load
 * (e.g. pollinations.ai service down, CORS, network error).
 */
function AIImage({ src, alt, className }: { src: string; alt: string; className?: string }) {
  const [status, setStatus] = useState<'loading' | 'loaded' | 'error'>('loading')
  return (
    <div className="relative w-full">
      {/* Actual image — hidden until loaded, replaced by placeholder on error */}
      {status !== 'error' && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={src}
          alt={alt}
          className={`w-full object-cover transition-opacity duration-500 ${status === 'loaded' ? 'opacity-100' : 'opacity-0 absolute inset-0'} ${className ?? ''}`}
          loading="lazy"
          onLoad={() => setStatus('loaded')}
          onError={() => setStatus('error')}
        />
      )}
      {/* Skeleton shown while loading */}
      {status === 'loading' && (
        <div className="w-full flex items-center justify-center rounded-lg animate-pulse" style={{ minHeight: 200, background: 'rgba(124,58,237,0.07)', border: '1px dashed rgba(124,58,237,0.2)' }}>
          <div className="text-center">
            <div className="text-3xl mb-2">🎨</div>
            <div className="text-xs text-slate-500">Generating image…</div>
          </div>
        </div>
      )}
      {/* Error placeholder */}
      {status === 'error' && (
        <div className="w-full flex items-center justify-center rounded-lg" style={{ minHeight: 200, background: 'rgba(255,255,255,0.03)', border: '1px dashed rgba(255,255,255,0.1)' }}>
          <div className="text-center px-6">
            <div className="text-3xl mb-2">🖼️</div>
            <div className="text-xs text-slate-500 mb-1">AI-generated image</div>
            <div className="text-[11px] text-slate-600 max-w-xs">{alt}</div>
          </div>
        </div>
      )}
    </div>
  )
}

interface PipelineState {
  pipelineId: string
  ideaText: string
  status: string
  agents: Record<string, { status: string; result?: Record<string, unknown> }>
  createdAt: string
}

function SectionCard({ title, icon, children, defaultOpen = false }: {
  title: string; icon: React.ReactNode; children: React.ReactNode; defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="glass-card overflow-hidden mb-4">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-5 text-left hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'rgba(124,58,237,0.15)', color: '#a855f7', border: '1px solid rgba(124,58,237,0.2)' }}>
            {icon}
          </div>
          <span className="font-semibold text-white">{title}</span>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
      </button>
      {open && (
        <div className="px-5 pb-5" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          <div className="pt-4">{children}</div>
        </div>
      )}
    </div>
  )
}

function copyText(text: string) {
  navigator.clipboard.writeText(text).catch(() => {})
}

export default function ResultsPage() {
  const { pipelineId } = useParams<{ pipelineId: string }>()
  const router = useRouter()
  const [pipeline, setPipeline] = useState<PipelineState | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!pipelineId) return
    fetch(`/api/pipeline/${pipelineId}/status`)
      .then(r => r.json())
      .then(data => { setPipeline(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [pipelineId])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#07070f' }}>
        <div className="flex items-center gap-3 text-slate-400">
          <div className="w-5 h-5 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
          Loading results...
        </div>
      </div>
    )
  }

  if (!pipeline) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4" style={{ background: '#07070f' }}>
        <p className="text-slate-400">Pipeline not found.</p>
        <button onClick={() => router.push('/')} className="btn-brand">Start New</button>
      </div>
    )
  }

  const agents = pipeline.agents || {}
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const v: any = agents.idea_validator?.result || {}
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const s: any = agents.strategy_planner?.result || {}
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const a: any = agents.product_architect?.result || {}
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const c: any = agents.code_generator?.result || {}
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const sec: any = agents.security_reviewer?.result || {}
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const copy: any = agents.copywriter?.result || {}
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const seo: any = agents.seo_optimizer?.result || {}

  const completeCount = Object.values(agents).filter(ag => ag.status === 'complete').length

  return (
    <div className="min-h-screen" style={{ background: '#07070f' }}>
      <div className="orb w-[500px] h-[500px] -top-40 -right-40" style={{ background: 'rgba(124,58,237,0.12)' }} />

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-5 max-w-5xl mx-auto">
        <button onClick={() => router.push('/')} className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #7c3aed, #2563eb)' }}>
            <Zap className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="font-semibold text-sm text-white">LaunchForge AI</span>
        </button>
        <button
          onClick={() => router.push(`/dashboard/${pipelineId}`)}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Pipeline
        </button>
      </nav>

      <main className="relative z-10 max-w-5xl mx-auto px-6 pb-20">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <CheckCircle className="w-7 h-7 text-green-400" />
            <h1 className="text-3xl font-black text-white">Launch Package Ready</h1>
          </div>
          <p className="text-slate-400 text-sm">
            {completeCount}/7 agents completed · Idea: "{pipeline.ideaText.slice(0, 100)}..."
          </p>
        </motion.div>

        {/* Summary badges */}
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8"
        >
          {[
            { label: 'Market Score', value: v.marketScore ? `${v.marketScore}/100` : '—', color: '#22c55e' },
            { label: 'Security Score', value: sec.overallScore ? `${sec.overallScore}/100` : '—', color: '#3b82f6' },
            { label: 'Tech Stack', value: (() => { const raw = (a.recommendedStack as { frontend?: string })?.frontend || 'Next.js'; return raw.split(/[\s,.(]/)[0].slice(0, 14) })(), color: '#a855f7' },
            { label: 'GTM Channels', value: Array.isArray(s.targetChannels) ? `${(s.targetChannels as string[]).length} channels` : '4 channels', color: '#f59e0b' },
          ].map(b => (
            <div key={b.label} className="glass-card p-4 text-center">
              <div className="text-2xl font-black mb-1" style={{ color: b.color }}>{b.value}</div>
              <div className="text-xs text-slate-500">{b.label}</div>
            </div>
          ))}
        </motion.div>

        {/* Sections */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>

          {/* Validation Report */}
          <SectionCard title="Business Validation Report" icon={<Target className="w-5 h-5" />} defaultOpen>
            <div className="space-y-3">
              {v.refinedIdea && <p className="text-slate-300 text-sm">{String(v.refinedIdea)}</p>}
              <div className="grid md:grid-cols-3 gap-3 text-sm">
                {v.tam && <div className="glass-card p-3"><div className="text-xs text-slate-500 mb-1">TAM</div><div className="font-bold text-white">{String(v.tam)}</div></div>}
                {v.sam && <div className="glass-card p-3"><div className="text-xs text-slate-500 mb-1">SAM</div><div className="font-bold text-white">{String(v.sam)}</div></div>}
                {v.som && <div className="glass-card p-3"><div className="text-xs text-slate-500 mb-1">SOM</div><div className="font-bold text-white">{String(v.som)}</div></div>}
              </div>
              {v.recommendation && (
                <div className="text-sm px-3 py-2 rounded-lg" style={{ background: 'rgba(34,197,94,0.1)', color: '#86efac', border: '1px solid rgba(34,197,94,0.2)' }}>
                  {String(v.recommendation)}
                </div>
              )}
              {Array.isArray(v.competitors) && (
                <div>
                  <div className="text-xs text-slate-500 mb-2">Competitors</div>
                  <div className="flex flex-wrap gap-2">
                    {(v.competitors as string[]).map((c: string) => (
                      <span key={c} className="text-xs px-2 py-1 rounded" style={{ background: 'rgba(255,255,255,0.05)', color: '#94a3b8' }}>{c}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </SectionCard>

          {/* Strategy */}
          <SectionCard title="Go-to-Market Strategy" icon={<BarChart3 className="w-5 h-5" />}>
            <div className="space-y-3 text-sm">
              {s.monetizationModel && <p className="text-slate-300"><span className="text-slate-500">Model: </span>{String(s.monetizationModel)}</p>}
              {s.competitivePositioning && <p className="text-slate-300"><span className="text-slate-500">Positioning: </span>{String(s.competitivePositioning)}</p>}
              {Array.isArray(s.targetChannels) && (
                <div>
                  <div className="text-xs text-slate-500 mb-2">Launch Channels</div>
                  <div className="flex flex-wrap gap-2">
                    {(s.targetChannels as string[]).map((ch: string) => (
                      <span key={ch} className="text-xs px-2.5 py-1 rounded-full" style={{ background: 'rgba(124,58,237,0.15)', color: '#c084fc', border: '1px solid rgba(124,58,237,0.2)' }}>{ch}</span>
                    ))}
                  </div>
                </div>
              )}
              {s.pricingTiers && typeof s.pricingTiers === 'object' && (
                <div>
                  <div className="text-xs text-slate-500 mb-2">Pricing Tiers</div>
                  <div className="grid grid-cols-3 gap-2">
                    {Object.entries(s.pricingTiers as Record<string, string>).map(([tier, price]) => (
                      <div key={tier} className="glass-card p-3 text-center">
                        <div className="text-xs text-slate-500 capitalize mb-1">{tier}</div>
                        <div className="font-bold text-white text-sm">{price}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </SectionCard>

          {/* Architecture */}
          <SectionCard title="Technical Architecture" icon={<Code2 className="w-5 h-5" />}>
            <div className="space-y-3 text-sm">
              {a.systemDesign && <p className="text-slate-300">{String(a.systemDesign)}</p>}
              {a.recommendedStack && typeof a.recommendedStack === 'object' && (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {Object.entries(a.recommendedStack as Record<string, string>).map(([k, v]) => (
                    <div key={k} className="glass-card p-2.5">
                      <div className="text-xs text-slate-500 capitalize mb-0.5">{k}</div>
                      <div className="text-xs font-semibold text-white">{v}</div>
                    </div>
                  ))}
                </div>
              )}
              {Array.isArray(a.apiEndpoints) && (
                <div>
                  <div className="text-xs text-slate-500 mb-2">Key API Endpoints</div>
                  <div className="space-y-1">
                    {(a.apiEndpoints as Array<{method: string; path: string; description: string}>).slice(0, 4).map((ep, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs font-mono">
                        <span className="px-1.5 py-0.5 rounded text-xs font-bold" style={{ background: 'rgba(37,99,235,0.2)', color: '#60a5fa' }}>{ep.method}</span>
                        <span className="text-green-400">{ep.path}</span>
                        <span className="text-slate-500">{ep.description}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </SectionCard>

          {/* MVP Code */}
          <SectionCard title="Generated MVP Code" icon={<Code2 className="w-5 h-5" />}>
            <div className="space-y-3">
              {c.readmeSummary && <p className="text-slate-300 text-sm">{String(c.readmeSummary)}</p>}
              {c.techStack && <p className="text-xs text-slate-400">Stack: <span className="text-purple-300">{String(c.techStack)}</span></p>}
              {Array.isArray(c.files) && (
                <div className="space-y-2">
                  {(c.files as Array<{path: string; description: string; content: string}>).slice(0, 3).map((f, i) => (
                    <div key={i} className="code-block">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-blue-400">{f.path}</span>
                        <button onClick={() => copyText(f.content)} className="text-slate-600 hover:text-slate-400 transition-colors">
                          <Copy className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <div className="text-slate-500 text-xs mb-1"># {f.description}</div>
                      <div className="text-green-400 text-xs">{f.content.slice(0, 300)}{f.content.length > 300 ? '\n...' : ''}</div>
                    </div>
                  ))}
                </div>
              )}
              {Array.isArray(c.setupInstructions) && (
                <div>
                  <div className="text-xs text-slate-500 mb-2">Setup Instructions</div>
                  <ol className="space-y-1">
                    {(c.setupInstructions as string[]).map((step, i) => (
                      <li key={i} className="text-xs text-slate-400 flex gap-2">
                        <span className="text-purple-400 font-mono">{i + 1}.</span> {step}
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          </SectionCard>

          {/* Security Report */}
          <SectionCard title="Security Audit Report" icon={<Shield className="w-5 h-5" />}>
            <div className="space-y-3">
              {sec.badge && (
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-semibold"
                  style={{ background: 'rgba(34,197,94,0.1)', color: '#22c55e', border: '1px solid rgba(34,197,94,0.3)' }}>
                  🛡️ {String(sec.badge)}
                </div>
              )}
              {Array.isArray(sec.owaspAudit) && (
                <div className="space-y-2">
                  {(sec.owaspAudit as Array<{id: string; name: string; status: string; severity: string; fix?: string}>).map((item) => (
                    <div key={item.id} className="flex items-start gap-3 text-xs p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
                      <span className={`font-mono px-1 rounded text-xs ${item.status === 'PASS' ? 'text-green-400' : item.status === 'WARN' ? 'text-amber-400' : 'text-red-400'}`}>
                        {item.status}
                      </span>
                      <div>
                        <span className="text-slate-300 font-semibold">{item.id}: {item.name}</span>
                        {item.fix && <p className="text-slate-500 mt-0.5">{item.fix}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {Array.isArray(sec.recommendations) && (
                <ul className="space-y-1">
                  {(sec.recommendations as string[]).map((r, i) => (
                    <li key={i} className="text-xs text-slate-400 flex gap-2">
                      <CheckCircle className="w-3 h-3 text-blue-400 mt-0.5 flex-shrink-0" /> {r}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </SectionCard>

          {/* Marketing Kit */}
          <SectionCard title="Marketing & Launch Kit" icon={<Globe className="w-5 h-5" />}>
            <div className="space-y-4">
              {/* Hero Image */}
              {copy.heroImage && typeof copy.heroImage === 'string' && (
                <div className="rounded-xl overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.08)' }}>
                  <AIImage src={copy.heroImage} alt="Hero section image" />
                </div>
              )}
              {Array.isArray(copy.taglines) && (
                <div>
                  <div className="text-xs text-slate-500 mb-2">Tagline Options</div>
                  <div className="space-y-2">
                    {(copy.taglines as string[]).map((t, i) => (
                      <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg" style={{ background: 'rgba(124,58,237,0.08)', border: '1px solid rgba(124,58,237,0.15)' }}>
                        <span className="text-sm text-white">{t}</span>
                        <button onClick={() => copyText(t)} className="text-slate-600 hover:text-purple-400 transition-colors ml-2">
                          <Copy className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {copy.heroSection && typeof copy.heroSection === 'object' && (
                <div className="space-y-2 text-sm">
                  <div className="text-xs text-slate-500">Hero Section</div>
                  {Object.entries(copy.heroSection as Record<string, string>).map(([k, v]) => (
                    <p key={k} className="text-slate-300"><span className="text-slate-500 capitalize">{k}: </span>{v}</p>
                  ))}
                </div>
              )}
              {copy.productHuntTagline && (
                <p className="text-xs text-slate-400">
                  <span className="text-slate-500">Product Hunt: </span>
                  <span className="text-amber-300 font-medium">{String(copy.productHuntTagline)}</span>
                </p>
              )}
              {/* OG / Social Sharing Image */}
              {copy.ogImage && typeof copy.ogImage === 'string' && (
                <div>
                  <div className="text-xs text-slate-500 mb-2">Social Sharing Preview (OG Image)</div>
                  <div className="rounded-xl overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.08)' }}>
                    <AIImage src={copy.ogImage} alt="OG social sharing image" />
                  </div>
                </div>
              )}
              {/* Pitch Deck with slide images */}
              {Array.isArray(copy.pitchDeck) && (copy.pitchDeck as Array<{slide: number; title: string; content: string; slideImage?: string; speakerNote?: string}>).length > 0 && (
                <div>
                  <div className="text-xs text-slate-500 mb-3">Pitch Deck ({(copy.pitchDeck as unknown[]).length} slides)</div>
                  <div className="space-y-4">
                    {(copy.pitchDeck as Array<{slide: number; title: string; content: string; slideImage?: string; speakerNote?: string}>).map((slide) => (
                      <div key={slide.slide} className="rounded-xl overflow-hidden" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>
                        {slide.slideImage && (
                          <AIImage src={slide.slideImage} alt={`Slide ${slide.slide}: ${slide.title}`} />
                        )}
                        <div className="p-3">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-mono px-1.5 py-0.5 rounded" style={{ background: 'rgba(124,58,237,0.2)', color: '#c084fc' }}>
                              {slide.slide}
                            </span>
                            <span className="text-sm font-semibold text-white">{slide.title}</span>
                          </div>
                          <p className="text-xs text-slate-400">{slide.content}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </SectionCard>

          {/* SEO */}
          <SectionCard title="SEO Strategy" icon={<Globe className="w-5 h-5" />}>
            <div className="space-y-3">
              {seo.metaTags && typeof seo.metaTags === 'object' && (
                <div className="space-y-2 text-xs">
                  {Object.entries(seo.metaTags as Record<string, unknown>).map(([k, v]) => (
                    <div key={k} className="flex gap-2">
                      <span className="text-slate-500 w-24 flex-shrink-0 capitalize">{k}:</span>
                      <span className="text-slate-300">{safeStr(v)}</span>
                    </div>
                  ))}
                </div>
              )}
              {Array.isArray(seo.primaryKeywords) && (
                <div>
                  <div className="text-xs text-slate-500 mb-2">Primary Keywords</div>
                  <div className="flex flex-wrap gap-2">
                    {(seo.primaryKeywords as unknown[]).map((kw, i) => {
                      const label = extractKeyword(kw)
                      const vol = typeof kw === 'object' && kw !== null ? (kw as Record<string,unknown>).estimatedVolume : null
                      return (
                        <span key={i} className="text-xs px-2 py-1 rounded-full flex items-center gap-1" style={{ background: 'rgba(6,182,212,0.1)', color: '#67e8f9', border: '1px solid rgba(6,182,212,0.2)' }}>
                          {label}{vol ? <span className="opacity-60 text-[10px]">· {safeStr(vol)}</span> : null}
                        </span>
                      )
                    })}
                  </div>
                </div>
              )}
              {Array.isArray(seo.longTailKeywords) && (
                <div>
                  <div className="text-xs text-slate-500 mb-2">Long-tail Keywords</div>
                  <div className="flex flex-wrap gap-2">
                    {(seo.longTailKeywords as unknown[]).map((kw, i) => (
                      <span key={i} className="text-xs px-2 py-1 rounded-full" style={{ background: 'rgba(124,58,237,0.1)', color: '#c084fc', border: '1px solid rgba(124,58,237,0.2)' }}>
                        {extractKeyword(kw)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {Array.isArray(seo.contentStrategy) && (
                <div>
                  <div className="text-xs text-slate-500 mb-2">Content Strategy</div>
                  <ul className="space-y-1">
                    {(seo.contentStrategy as unknown[]).map((item, i) => (
                      <li key={i} className="text-xs text-slate-400 flex gap-2">
                        <span className="text-cyan-400">›</span> {safeStr(item)}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {seo.estimatedMonthlySearchVolume && (
                <p className="text-xs text-slate-400">
                  <span className="text-slate-500">Est. Monthly Search Volume: </span>
                  <span className="text-cyan-300 font-medium">{safeStr(seo.estimatedMonthlySearchVolume)}</span>
                </p>
              )}
            </div>
          </SectionCard>

          {/* Download actions */}
          <div className="glass-card p-6 mt-6" style={{ border: '1px solid rgba(124,58,237,0.2)', background: 'rgba(124,58,237,0.06)' }}>
            <h3 className="font-semibold text-white mb-4">📦 Your Launch Package</h3>
            <div className="flex flex-wrap gap-3">
              <a
                href={`/api/pipeline/${pipelineId}/download`}
                download
                className="btn-brand flex items-center gap-2 text-sm"
              >
                <Download className="w-4 h-4" /> Download ZIP
              </a>
              <button className="flex items-center gap-2 text-sm px-4 py-2.5 rounded-xl font-semibold transition-all hover:bg-white/10"
                style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: '#e2e8f0' }}>
                <ExternalLink className="w-4 h-4" /> Deploy to Vercel
              </button>
              <button
                onClick={() => router.push('/')}
                className="flex items-center gap-2 text-sm px-4 py-2.5 rounded-xl font-semibold transition-all hover:bg-white/10"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#94a3b8' }}>
                <Zap className="w-4 h-4" /> New Idea
              </button>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  )
}
