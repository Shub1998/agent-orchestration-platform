import { create } from 'zustand'
import type { LogEntry } from '@/api/types'

interface ExecutionStore {
  activeExecutionId: string | null
  logs: LogEntry[]
  status: 'idle' | 'connecting' | 'running' | 'completed' | 'failed'
  ws: WebSocket | null
  setActiveExecution: (id: string | null) => void
  startStream: (executionId: string) => void
  stopStream: () => void
  addLog: (entry: LogEntry) => void
  clearLogs: () => void
}

export const useExecutionStore = create<ExecutionStore>((set, get) => ({
  activeExecutionId: null,
  logs: [],
  status: 'idle',
  ws: null,

  setActiveExecution: (id) => set({ activeExecutionId: id }),

  startStream: (executionId) => {
    // Close existing socket without clearing logs (preserve log history across HITL cycles)
    const existing = get().ws
    if (existing) {
      existing.onclose = null
      existing.close()
    }

    // Keep existing logs if reconnecting for the same execution mid-cycle
    const keepLogs = get().activeExecutionId === executionId ? get().logs : []
    set({ logs: keepLogs, status: 'connecting', activeExecutionId: executionId, ws: null })

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${proto}//${window.location.host}/ws/executions/${executionId}/logs`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => set({ status: 'running' })

    ws.onmessage = (event) => {
      try {
        const data: LogEntry = JSON.parse(event.data)
        if (data.type === 'connected') return
        if (data.type === 'execution_complete') {
          set(state => ({
            logs: [...state.logs, data],
            status: data.status === 'completed' ? 'completed' : 'failed',
          }))
          // Do NOT close the socket — HITL loops may continue and need a new stream
          return
        }
        set(state => ({ logs: [...state.logs, data] }))
      } catch {}
    }

    ws.onerror = () => set({ status: 'failed' })
    ws.onclose = () => {
      const { status } = get()
      // Only override status if the WS dropped unexpectedly (no execution_complete received).
      // Setting 'idle' triggers the LogStream auto-reconnect while execution is still active.
      // If we already received execution_complete (status = 'completed'/'failed'), leave it alone.
      if (status === 'running' || status === 'connecting') set({ status: 'idle' })
    }

    set({ ws })
  },

  stopStream: () => {
    const { ws } = get()
    if (ws) {
      ws.onclose = null
      ws.close()
      set({ ws: null })
    }
  },

  addLog: (entry) => set(state => ({ logs: [...state.logs, entry] })),
  clearLogs: () => set({ logs: [], status: 'idle', activeExecutionId: null }),
}))
