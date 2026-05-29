import { useEffect, useRef } from 'react'
import { useExecutionStore } from '@/stores/executionStore'
import { CheckCircle, XCircle, Loader2, Zap, Wrench, Brain, Info } from 'lucide-react'
import type { LogEntry } from '@/api/types'

const LEVEL_STYLES: Record<string, { color: string; icon: React.ComponentType<any> }> = {
  info: { color: 'text-gray-300', icon: Info },
  llm_start: { color: 'text-blue-400', icon: Brain },
  llm_end: { color: 'text-green-400', icon: CheckCircle },
  tool_call: { color: 'text-yellow-400', icon: Wrench },
  error: { color: 'text-red-400', icon: XCircle },
}

function LogLine({ entry }: { entry: LogEntry }) {
  if (entry.type === 'execution_complete') {
    return (
      <div className={`flex items-start gap-2 py-1 ${entry.status === 'completed' ? 'text-green-400' : 'text-red-400'}`}>
        {entry.status === 'completed' ? <CheckCircle className="h-4 w-4 mt-0.5 flex-shrink-0" /> : <XCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />}
        <span className="font-semibold">
          {entry.status === 'completed' ? '✓ Workflow completed successfully' : `✗ Workflow failed: ${entry.error}`}
        </span>
      </div>
    )
  }

  const level = entry.level || 'info'
  const style = LEVEL_STYLES[level] || LEVEL_STYLES.info
  const Icon = style.icon
  const ts = entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : ''

  return (
    <div className={`flex items-start gap-2 py-0.5 ${style.color} hover:bg-gray-800 rounded px-1`}>
      <Icon className="h-3.5 w-3.5 mt-0.5 flex-shrink-0 opacity-70" />
      <span className="text-gray-500 text-xs flex-shrink-0 w-16">{ts}</span>
      {entry.agent_name && <span className="text-xs font-medium text-gray-400 flex-shrink-0 w-28 truncate">[{entry.agent_name}]</span>}
      <span className="flex-1 break-all">{entry.message}</span>
    </div>
  )
}

interface LogStreamProps {
  executionId: string
}

export function LogStream({ executionId }: LogStreamProps) {
  const { logs, status, startStream } = useExecutionStore()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    startStream(executionId)
  }, [executionId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs.length])

  return (
    <div className="flex flex-col h-full bg-gray-900 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <div className={`h-2 w-2 rounded-full ${status === 'running' ? 'bg-green-400 animate-pulse' : status === 'completed' ? 'bg-green-400' : status === 'failed' ? 'bg-red-400' : 'bg-gray-400'}`} />
          <span className="text-gray-300 text-sm font-mono font-medium">
            {status === 'connecting' ? 'Connecting...' : status === 'running' ? 'Live' : status === 'completed' ? 'Completed' : status === 'failed' ? 'Failed' : 'Idle'}
          </span>
        </div>
        {status === 'running' && <Loader2 className="h-4 w-4 animate-spin text-gray-400" />}
        <span className="text-gray-500 text-xs">{logs.filter(l => l.type === 'log').length} events</span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 log-terminal space-y-0.5">
        {logs.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            {status === 'connecting' ? 'Connecting to execution stream...' : 'Waiting for events...'}
          </div>
        ) : (
          logs.map((entry, i) => <LogLine key={i} entry={entry} />)
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
