'use client'

import { useEffect, useState, useRef, useCallback } from 'react'

export interface AgentStatus {
  agentId: string
  status: 'queued' | 'in_progress' | 'complete' | 'failed'
  startedAt?: string
  completedAt?: string
  result?: Record<string, unknown>
  error?: string
}

export interface PipelineState {
  pipelineId: string
  userId: string
  ideaText: string
  status: 'running' | 'complete' | 'failed' | 'partial'
  agents: Record<string, AgentStatus>
  deployUrl?: string
  packageUrl?: string
  createdAt: string
  completedAt?: string
}

interface UsePipelineSSEResult {
  state: PipelineState | null
  connected: boolean
  error: string | null
}

const RECONNECT_DELAY = 3000
const MAX_RECONNECTS = 5

/**
 * React hook that subscribes to the SSE stream for a given pipeline.
 * Automatically reconnects on disconnect (up to MAX_RECONNECTS times).
 */
export function usePipelineSSE(pipelineId: string | null): UsePipelineSSEResult {
  const [state, setState] = useState<PipelineState | null>(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const reconnectCount = useRef(0)
  const esRef = useRef<EventSource | null>(null)
  const isFinalRef = useRef(false)

  const connect = useCallback(() => {
    if (!pipelineId || isFinalRef.current) return

    const url = `/api/pipeline/${pipelineId}/stream`
    const es = new EventSource(url)
    esRef.current = es

    es.onopen = () => {
      setConnected(true)
      setError(null)
      reconnectCount.current = 0
    }

    es.onmessage = (evt) => {
      try {
        const event = JSON.parse(evt.data)
        if (event.type === 'agent_update') {
          setState(prev => {
            if (!prev) return prev
            return {
              ...prev,
              agents: {
                ...prev.agents,
                [event.payload.agentId]: event.payload,
              },
            }
          })
        } else if (event.type === 'pipeline_complete' || event.type === 'pipeline_failed') {
          setState(event.payload as PipelineState)
          isFinalRef.current = true
          es.close()
          setConnected(false)
        }
      } catch (e) {
        console.error('SSE parse error:', e)
      }
    }

    es.onerror = () => {
      setConnected(false)
      es.close()
      if (!isFinalRef.current && reconnectCount.current < MAX_RECONNECTS) {
        reconnectCount.current += 1
        setTimeout(connect, RECONNECT_DELAY)
      } else if (!isFinalRef.current) {
        setError('Connection lost. Please refresh to retry.')
      }
    }
  }, [pipelineId])

  // Load initial state via HTTP, then connect SSE
  useEffect(() => {
    if (!pipelineId) return
    isFinalRef.current = false

    // Fetch current state first (in case we reconnect mid-pipeline)
    fetch(`/api/pipeline/${pipelineId}/status`)
      .then(r => r.json())
      .then((data: PipelineState) => {
        setState(data)
        if (data.status === 'complete' || data.status === 'failed') {
          isFinalRef.current = true
        } else {
          connect()
        }
      })
      .catch(err => setError(String(err)))

    return () => {
      esRef.current?.close()
    }
  }, [pipelineId, connect])

  return { state, connected, error }
}
