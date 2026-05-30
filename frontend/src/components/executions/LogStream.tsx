import { useEffect, useRef, useMemo } from 'react'
import { useExecutionStore } from '@/stores/executionStore'
import { useExecutionLogs } from '@/api/executions'
import { CheckCircle, XCircle, Loader2, Wrench, Brain, Info, UserCheck, RefreshCw } from 'lucide-react'
import type { LogEntry } from '@/api/types'

const LEVEL_STYLES: Record<string, { color: string; icon: React.ComponentType<any> }> = {
  info:      { color: 'text-gray-300',   icon: Info },
  llm_start: { color: 'text-blue-400',   icon: Brain },
  llm_end:   { color: 'text-green-400',  icon: CheckCircle },
  tool_call: { color: 'text-yellow-400', icon: Wrench },
  error:     { color: 'text-red-400',    icon: XCircle },
  approval:  { color: 'text-amber-400',  icon: UserCheck },
}

const ACTIVE_EXECUTION_STATUSES = new Set(['pending', 'running', 'awaiting_approval'])

function LogLine({ entry }: { entry: LogEntry }) {
  if (entry.type === 'execution_complete') {
    return (
      <div className={`flex items-start gap-2 py-1 ${entry.status === 'completed' ? 'text-green-400' : 'text-red-400'}`}>
        {entry.status === 'completed'
          ? <CheckCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
          : <XCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />}
        <span className="font-semibold">
          {entry.status === 'completed' ? '✓ Workflow completed successfully' : `✗ Workflow failed: ${entry.error}`}
        </span>
      </div>
    )
  }

  if ((entry as any).type === 'ping') return null

  const level = entry.level || 'info'
  const style = LEVEL_STYLES[level] || LEVEL_STYLES.info
  const Icon = style.icon
  const ts = entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : ''

  return (
    <div className={`flex items-start gap-2 py-0.5 ${style.color} hover:bg-gray-800 rounded px-1`}>
      <Icon className="h-3.5 w-3.5 mt-0.5 flex-shrink-0 opacity-70" />
      <span className="text-gray-500 text-xs flex-shrink-0 w-16">{ts}</span>
      {entry.agent_name && (
        <span className="text-xs font-medium text-gray-400 flex-shrink-0 w-28 truncate">[{entry.agent_name}]</span>
      )}
      <span className="flex-1 break-all">{entry.message}</span>
    </div>
  )
}

export function LogStream({ executionId, executionStatus }: { executionId: string; executionStatus?: string }) {
  const { logs, status, startStream } = useExecutionStore()
  const bottomRef = useRef<HTMLDivElement>(null)

  const isActive = executionStatus === 'running' || executionStatus === 'pending' || executionStatus === 'awaiting_approval'

  // REST logs: poll every 2s while execution is active (catches events missed by WS pub/sub race).
  // Falls back to a one-shot fetch once terminal.
  const { data: restLogs, refetch: refetchRestLogs } = useExecutionLogs(executionId, isActive ? 2000 : false)

  useEffect(() => {
    const isTerminal = executionStatus === 'completed' || executionStatus === 'failed' || executionStatus === 'cancelled'
    // Don't start a WS stream for already-finished executions
    if (!isTerminal) {
      startStream(executionId)
    }
  }, [executionId])

  // Auto-reconnect: only if WS dropped unexpectedly (failed/idle) while execution is still active.
  // Do NOT reconnect when status = 'completed' — the WS properly received execution_complete and
  // React Query just hasn't polled the updated executionStatus yet (2s lag). Reconnecting here
  // causes a status-oscillation loop (completed → reconnect → running → completed → …).
  useEffect(() => {
    const wsDropped = status === 'failed' || status === 'idle'
    const executionIsActive = executionStatus ? ACTIVE_EXECUTION_STATUSES.has(executionStatus) : false
    if (!wsDropped || !executionIsActive) return

    const timer = setTimeout(() => {
      refetchRestLogs()
      startStream(executionId)
    }, 2000)
    return () => clearTimeout(timer)
  }, [status, executionStatus, executionId])

  // Re-fetch REST logs on WS connect (catches any gap before subscription)
  // and on WS completion (catches Agent 2+ logs published just before execution_complete).
  useEffect(() => {
    if (status === 'running' || status === 'completed' || status === 'failed') {
      refetchRestLogs()
    }
  }, [status])

  // Final fetch when React Query confirms the execution is terminal — covers the
  // case where the WS never received execution_complete (e.g. was dead at that moment).
  useEffect(() => {
    if (executionStatus === 'completed' || executionStatus === 'failed' || executionStatus === 'cancelled') {
      refetchRestLogs()
    }
  }, [executionStatus])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs.length, restLogs])

  // Merge WS live logs + REST persisted logs, deduplicated by timestamp+message.
  // Three cases handled:
  //   1. Completed execution  → WS has nothing, REST has everything
  //   2. WS gap during HITL   → REST fills in messages missed while WS was down
  //   3. Normal live stream   → WS logs dominate, REST adds nothing new
  //
  // WS logs are filtered to this executionId first: on first render the Zustand
  // store may still hold logs from the previously viewed execution (startStream
  // runs asynchronously), which would otherwise contaminate the merge.
  const displayLogs = useMemo(() => {
    const rest: LogEntry[] = (restLogs || []).map((l: any) => ({ type: 'log' as const, ...l }))

    // Only keep WS logs that belong to this execution
    const wsLogs = logs.filter(l => !l.execution_id || l.execution_id === executionId)

    if (rest.length === 0) return wsLogs
    if (wsLogs.length === 0) return rest

    const wsFingerprints = new Set(
      wsLogs.filter(l => l.type === 'log').map(l => `${l.timestamp}|${l.message}`)
    )
    const restOnly = rest.filter(l => !wsFingerprints.has(`${l.timestamp}|${l.message}`))
    if (restOnly.length === 0) return wsLogs

    return [...restOnly, ...wsLogs].sort((a, b) =>
      (a.timestamp || '').localeCompare(b.timestamp || '')
    )
  }, [logs, restLogs, executionId])

  const isTerminal = executionStatus === 'completed' || executionStatus === 'failed' || executionStatus === 'cancelled'
  const displayStatus = isTerminal && logs.length === 0 ? (executionStatus === 'completed' ? 'completed' : 'failed') : status
  const eventCount = displayLogs.filter(l => l.type === 'log').length

  return (
    <div className="flex flex-col h-full bg-gray-900 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <div className={`h-2 w-2 rounded-full ${
            displayStatus === 'running'    ? 'bg-green-400 animate-pulse' :
            displayStatus === 'completed'  ? 'bg-green-400' :
            displayStatus === 'failed'     ? 'bg-red-400' :
            'bg-amber-400 animate-pulse'
          }`} />
          <span className="text-gray-300 text-sm font-mono font-medium">
            {displayStatus === 'connecting'  ? 'Connecting...' :
             displayStatus === 'running'     ? 'Live' :
             displayStatus === 'completed'   ? 'Completed' :
             displayStatus === 'failed'      ? 'Failed' : 'Idle'}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {(displayStatus === 'running') && <Loader2 className="h-4 w-4 animate-spin text-gray-400" />}
          {(displayStatus === 'completed' || displayStatus === 'failed') && (
            <button
              onClick={() => { refetchRestLogs(); if (!isTerminal) startStream(executionId) }}
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200"
              title="Refresh logs"
            >
              <RefreshCw className="h-3 w-3" /> Refresh
            </button>
          )}
          <span className="text-gray-500 text-xs">{eventCount} events</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-0.5 font-mono text-xs">
        {displayLogs.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            {displayStatus === 'connecting' ? 'Connecting to execution stream...' : 'Waiting for events...'}
          </div>
        ) : (
          displayLogs.map((entry, i) => <LogLine key={i} entry={entry} />)
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
