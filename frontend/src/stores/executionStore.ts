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
    get().stopStream()
    set({ logs: [], status: 'connecting', activeExecutionId: executionId })

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/executions/${executionId}/logs`
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
          ws.close()
          return
        }
        set(state => ({ logs: [...state.logs, data] }))
      } catch {}
    }

    ws.onerror = () => set({ status: 'failed' })
    ws.onclose = () => {
      const { status } = get()
      if (status === 'running' || status === 'connecting') set({ status: 'completed' })
    }

    set({ ws })
  },

  stopStream: () => {
    const { ws } = get()
    if (ws) { ws.close(); set({ ws: null }) }
  },

  addLog: (entry) => set(state => ({ logs: [...state.logs, entry] })),
  clearLogs: () => set({ logs: [], status: 'idle', activeExecutionId: null }),
}))
