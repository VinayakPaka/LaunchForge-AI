'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Zap, Mail, Lock, User, ArrowRight, Eye, EyeOff, Shield, Check } from 'lucide-react'

/**
 * Stores the short-lived access token in memory (sessionStorage).
 * The HttpOnly refresh token cookie is managed entirely by the browser
 * and is never accessible to JavaScript — this is intentional.
 */
function saveSession(accessToken: string, user: object) {
  // sessionStorage: cleared when tab closes. Safer than localStorage.
  sessionStorage.setItem('lf_access_token', accessToken)
  sessionStorage.setItem('lf_user', JSON.stringify(user))
}

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null
  return sessionStorage.getItem('lf_access_token')
}

export function clearSession() {
  sessionStorage.removeItem('lf_access_token')
  sessionStorage.removeItem('lf_user')
}

const INPUT_CLASS =
  'w-full pl-10 pr-4 py-3 rounded-xl text-sm text-white placeholder-slate-600 outline-none transition-all focus:ring-1 focus:ring-purple-500/50'
const INPUT_STYLE = {
  background: 'rgba(255,255,255,0.05)',
  border: '1px solid rgba(255,255,255,0.08)',
}

export default function AuthPage() {
  const router = useRouter()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [form, setForm] = useState({ email: '', password: '', name: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPwd, setShowPwd] = useState(false)

  // Live password-strength hints (register mode)
  const pwChecks = {
    length:    form.password.length >= 8,
    uppercase: /[A-Z]/.test(form.password),
    digit:     /[0-9]/.test(form.password),
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/register'
      const body = mode === 'login'
        ? { email: form.email, password: form.password }
        : { email: form.email, password: form.password, name: form.name || 'Founder' }

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',   // allow browser to receive HttpOnly refresh cookie
        body: JSON.stringify(body),
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(
          typeof data.detail === 'string'
            ? data.detail
            : JSON.stringify(data.detail) || 'Authentication failed'
        )
      }

      // Store access token in sessionStorage (NOT localStorage)
      // The refresh token is automatically stored as HttpOnly cookie by the browser
      saveSession(data.access_token, data.user)
      router.push('/')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: '#07070f' }}>
      <div className="orb w-[500px] h-[500px] -top-40 -left-40" style={{ background: 'rgba(124,58,237,0.15)' }} />
      <div className="orb w-[400px] h-[400px] bottom-0 -right-20" style={{ background: 'rgba(37,99,235,0.12)' }} />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <button onClick={() => router.push('/')} className="inline-flex items-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #7c3aed, #2563eb)' }}>
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-xl text-white">LaunchForge AI</span>
          </button>
          <h1 className="text-2xl font-black text-white">
            {mode === 'login' ? 'Welcome back' : 'Create your account'}
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            {mode === 'login'
              ? 'Sign in to access your launch packages'
              : 'Start forging your startup today — free forever'}
          </p>
        </div>

        {/* Card */}
        <div className="glass-card p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name (register only) */}
            {mode === 'register' && (
              <div className="relative">
                <User className="absolute left-3 top-3.5 w-4 h-4 text-slate-500" />
                <input
                  type="text" placeholder="Your name" value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  className={INPUT_CLASS} style={INPUT_STYLE}
                />
              </div>
            )}

            {/* Email */}
            <div className="relative">
              <Mail className="absolute left-3 top-3.5 w-4 h-4 text-slate-500" />
              <input
                type="email" placeholder="Email address" value={form.email} required
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                className={INPUT_CLASS} style={INPUT_STYLE}
                autoComplete={mode === 'login' ? 'username' : 'email'}
              />
            </div>

            {/* Password */}
            <div className="relative">
              <Lock className="absolute left-3 top-3.5 w-4 h-4 text-slate-500" />
              <input
                type={showPwd ? 'text' : 'password'}
                placeholder={mode === 'register' ? 'Password (8+ chars, 1 uppercase, 1 number)' : 'Password'}
                value={form.password} required minLength={8}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                className={`${INPUT_CLASS} pr-10`} style={INPUT_STYLE}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              />
              <button type="button" onClick={() => setShowPwd(!showPwd)}
                className="absolute right-3 top-3.5 text-slate-500 hover:text-slate-300 transition-colors">
                {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {/* Password strength hints (register only) */}
            {mode === 'register' && form.password.length > 0 && (
              <div className="flex gap-3 text-xs">
                {[
                  { label: '8+ chars',   ok: pwChecks.length    },
                  { label: 'Uppercase',  ok: pwChecks.uppercase },
                  { label: 'Number',     ok: pwChecks.digit     },
                ].map(({ label, ok }) => (
                  <span key={label} className={`flex items-center gap-1 transition-colors ${ok ? 'text-green-400' : 'text-slate-600'}`}>
                    <Check className="w-3 h-3" /> {label}
                  </span>
                ))}
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="text-red-400 text-sm px-3 py-2.5 rounded-xl flex items-start gap-2"
                style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
                <span className="mt-0.5 shrink-0">⚠</span>
                <span>{error}</span>
              </div>
            )}

            {/* Submit */}
            <button type="submit" disabled={loading}
              className="btn-brand w-full flex items-center justify-center gap-2 py-3 mt-2">
              {loading
                ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Authenticating...</>
                : <>{mode === 'login' ? 'Sign In' : 'Create Account'} <ArrowRight className="w-4 h-4" /></>}
            </button>
          </form>

          {/* Toggle mode */}
          <div className="mt-6 pt-6 text-center" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            <p className="text-slate-500 text-sm">
              {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}
              {' '}
              <button onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); setForm({ email: '', password: '', name: '' }) }}
                className="text-purple-400 hover:text-purple-300 font-medium transition-colors">
                {mode === 'login' ? 'Sign up free' : 'Sign in'}
              </button>
            </p>
          </div>
        </div>

        {/* Security badge */}
        <div className="mt-4 flex items-center justify-center gap-2 text-xs text-slate-600">
          <Shield className="w-3 h-3" />
          <span>RS256 JWT · Argon2id · HttpOnly cookies · No passwords stored in plain text</span>
        </div>

        <p className="text-center text-xs text-slate-700 mt-2">
          By continuing, you agree to LaunchForge AI Terms &amp; Privacy Policy
        </p>
      </motion.div>
    </div>
  )
}
