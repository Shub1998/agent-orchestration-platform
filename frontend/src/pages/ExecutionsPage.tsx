import { useState, useMemo } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useExecutions, useExecution, useCancelExecution, useApproveExecution, useExecutionLogs, executionKeys } from '@/api/executions'
import { LogStream } from '@/components/executions/LogStream'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ArrowLeft, CheckCircle, XCircle, Clock, Loader2, Play, Coins, Hash, UserCheck, ThumbsUp, ThumbsDown, MessageSquare, Terminal } from 'lucide-react'
import type { Execution, LogEntry } from '@/api/types'

function StatusBadge({ status }: { status: Execution['status'] }) {
  const config: Record<string, { variant: 'secondary' | 'default' | 'outline' | 'destructive'; icon: React.ElementType; label: string; spin?: boolean; className?: string }> = {
    pending: { variant: 'secondary', icon: Clock, label: 'Pending' },
    running: { variant: 'default', icon: Loader2, label: 'Running', spin: true },
    completed: { variant: 'outline', icon: CheckCircle, label: 'Completed', className: 'border-green-400 text-green-700 bg-green-50' },
    failed: { variant: 'destructive', icon: XCircle, label: 'Failed' },
    cancelled: { variant: 'outline', icon: XCircle, label: 'Cancelled' },
    awaiting_approval: { variant: 'outline', icon: UserCheck, label: 'Awaiting Approval', className: 'border-amber-400 text-amber-700 bg-amber-50 animate-pulse' },
  }
  const c = config[status] ?? config.pending
  const Icon = c.icon
  return (
    <Badge variant={c.variant} className={`flex items-center gap-1 shrink-0 ${c.className ?? ''}`}>
      <Icon className={`h-3 w-3 ${c.spin ? 'animate-spin' : ''}`} />
      <span className="hidden sm:inline">{c.label}</span>
    </Badge>
  )
}

function ApprovalPanel({
  executionId,
  onDecision,
}: {
  executionId: string
  onDecision: (decision: 'approved' | 'rejected') => void
}) {
  const approve = useApproveExecution()
  const [showRejectDialog, setShowRejectDialog] = useState(false)
  const [rejectComment, setRejectComment] = useState('')
  const [decisionMade, setDecisionMade] = useState<'approved' | 'rejected' | null>(null)
  const [error, setError] = useState('')

  const handleApprove = async () => {
    setError('')
    try {
      await approve.mutateAsync({ id: executionId, decision: 'approve' })
      setDecisionMade('approved')
      onDecision('approved')
    } catch {
      setError('Failed to submit approval. Please try again.')
    }
  }

  const handleReject = async () => {
    setError('')
    try {
      await approve.mutateAsync({ id: executionId, decision: 'reject', comment: rejectComment })
      setDecisionMade('rejected')
      setShowRejectDialog(false)
      onDecision('rejected')
    } catch {
      setError('Failed to submit rejection. Please try again.')
    }
  }

  if (decisionMade) {
    return (
      <div className={`mb-4 p-4 rounded-xl border-2 flex items-center gap-3 ${decisionMade === 'approved' ? 'bg-green-50 border-green-400' : 'bg-orange-50 border-orange-400'}`}>
        <Loader2 className="h-5 w-5 animate-spin text-gray-500 shrink-0" />
        <div>
          <p className="font-semibold text-gray-800">
            {decisionMade === 'approved' ? '✅ Approved — continuing workflow...' : '🔄 Rejected — agent is revising...'}
          </p>
          <p className="text-sm text-gray-500 mt-0.5">
            {decisionMade === 'approved' ? 'The next agent will run shortly.' : 'The agent will incorporate your feedback and re-submit for approval.'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="mb-4 p-4 bg-amber-50 border-2 border-amber-400 rounded-xl">
      <div className="flex items-start gap-3 mb-3">
        <div className="h-10 w-10 rounded-full bg-amber-400 flex items-center justify-center shrink-0 animate-pulse">
          <UserCheck className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="font-semibold text-amber-900">Human Approval Required</p>
          <p className="text-sm text-amber-700">Review the agent output below, then approve to continue or reject with feedback.</p>
        </div>
      </div>

      {error && <p className="text-sm text-red-600 mb-3 bg-red-50 border border-red-200 rounded px-3 py-2">{error}</p>}

      <div className="flex flex-col sm:flex-row gap-2 md:gap-3">
        <Button className="flex-1 bg-green-600 hover:bg-green-700 text-white" disabled={approve.isPending} onClick={handleApprove}>
          {approve.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <ThumbsUp className="h-4 w-4 mr-2" />}
          Approve — Continue
        </Button>
        <Button variant="destructive" className="flex-1" disabled={approve.isPending} onClick={() => setShowRejectDialog(true)}>
          <ThumbsDown className="h-4 w-4 mr-2" /> Reject with Feedback
        </Button>
      </div>

      <Dialog open={showRejectDialog} onOpenChange={v => { if (!approve.isPending) setShowRejectDialog(v) }}>
        <DialogContent className="w-[95vw] max-w-sm">
          <DialogHeader><DialogTitle>Reject &amp; Request Revision</DialogTitle></DialogHeader>
          <p className="text-sm text-gray-500">
            Describe what needs to change — the agent will revise its output and re-submit for your approval.
          </p>
          <Textarea
            value={rejectComment}
            onChange={e => setRejectComment(e.target.value)}
            placeholder="e.g. The research is too brief, please include more detail on X..."
            className="h-28"
            autoFocus
          />
          <div className="flex gap-3 pt-1">
            <Button variant="destructive" className="flex-1" disabled={approve.isPending} onClick={handleReject}>
              {approve.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              {approve.isPending ? 'Submitting...' : 'Confirm Rejection'}
            </Button>
            <Button variant="outline" onClick={() => setShowRejectDialog(false)} disabled={approve.isPending}>
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

const AGENT_COLORS = [
  'bg-blue-100 text-blue-800 border-blue-200',
  'bg-purple-100 text-purple-800 border-purple-200',
  'bg-green-100 text-green-800 border-green-200',
  'bg-orange-100 text-orange-800 border-orange-200',
  'bg-pink-100 text-pink-800 border-pink-200',
]

function MessagesThread({ executionId }: { executionId: string }) {
  const { data: logs = [] } = useExecutionLogs(executionId)

  const messages = useMemo(() => {
    const agentColorMap: Record<string, string> = {}
    let colorIdx = 0
    return (logs as LogEntry[])
      .filter((l: any) => l.level === 'agent_message' && l.agent_name && l.message)
      .map((l: any) => {
        if (!agentColorMap[l.agent_name]) {
          agentColorMap[l.agent_name] = AGENT_COLORS[colorIdx++ % AGENT_COLORS.length]
        }
        return { ...l, colorClass: agentColorMap[l.agent_name] }
      })
  }, [logs])

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 py-12">
        <MessageSquare className="h-10 w-10 mb-3 opacity-40" />
        <p className="text-sm font-medium">No messages yet</p>
        <p className="text-xs mt-1">Agent outputs will appear here as the workflow runs</p>
      </div>
    )
  }

  return (
    <div className="space-y-4 overflow-y-auto h-full pr-1">
      {messages.map((msg: any, i: number) => (
        <div key={i} className="flex gap-3">
          <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold border ${msg.colorClass}`}>
            {msg.agent_name[0].toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-sm font-semibold text-gray-800">{msg.agent_name}</span>
              <span className="text-xs text-gray-400">
                {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : ''}
              </span>
              {(msg.metadata as any)?.truncated && (
                <span className="text-xs text-amber-600 italic">output truncated</span>
              )}
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-3 shadow-sm">
              <pre className="text-xs md:text-sm text-gray-700 whitespace-pre-wrap break-words font-sans">{msg.message}</pre>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

type LogTab = 'logs' | 'messages'

function LogMessagesTabs({ executionId, executionStatus }: { executionId: string; executionStatus?: string }) {
  const [tab, setTab] = useState<LogTab>('logs')
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-1 mb-3 border-b">
        <button
          onClick={() => setTab('logs')}
          className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
            tab === 'logs' ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Terminal className="h-3.5 w-3.5" /> Live Logs
        </button>
        <button
          onClick={() => setTab('messages')}
          className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
            tab === 'messages' ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <MessageSquare className="h-3.5 w-3.5" /> Messages
        </button>
      </div>
      <div className="flex-1 overflow-hidden">
        {tab === 'logs'
          ? <LogStream executionId={executionId} executionStatus={executionStatus} />
          : <MessagesThread executionId={executionId} />}
      </div>
    </div>
  )
}

function ExecutionDetail({ id }: { id: string }) {
  const { data: execution, isLoading } = useExecution(id)
  const cancelExecution = useCancelExecution()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  if (isLoading) return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-gray-400" /></div>
  if (!execution) return <div className="p-8 text-gray-400">Execution not found</div>

  const prompt = (execution.trigger_payload as any)?.prompt || 'No prompt'
  const duration = execution.completed_at && execution.started_at
    ? Math.round((new Date(execution.completed_at).getTime() - new Date(execution.started_at).getTime()) / 1000)
    : null

  const handleDecision = (decision: 'approved' | 'rejected') => {
    if (decision === 'rejected') {
      // Optimistically clear the output so UI shows "waiting" immediately
      // instead of showing the stale previous output while the agent re-runs
      queryClient.setQueryData(executionKeys.detail(id), (old: Execution | undefined) =>
        old ? { ...old, final_output: null, status: 'running' as const } : old
      )
    }
    // Do NOT reconnect the log stream here — the existing WebSocket connection
    // is still subscribed to the pub/sub channel and will naturally receive
    // all subsequent agent logs (Agent 1 retry or Agent 2 continuation).
    // Calling startStream would close the working WS and create a gap where
    // published logs are permanently missed.
  }

  return (
    <div className="p-4 md:p-6 max-w-full">
      {/* Breadcrumb */}
      <div className="flex flex-wrap items-center gap-2 mb-4 md:mb-6">
        <button onClick={() => navigate('/executions')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800">
          <ArrowLeft className="h-4 w-4" /> Executions
        </button>
        <span className="text-gray-300">/</span>
        <h2 className="font-semibold text-gray-900">Execution Detail</h2>
        <StatusBadge status={execution.status} />
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 md:gap-4 mb-4 md:mb-6">
        <div className="bg-white rounded-lg border p-3 md:p-4 col-span-2 md:col-span-1">
          <p className="text-xs text-gray-500 font-medium">Trigger</p>
          <p className="text-xs md:text-sm font-medium mt-1 truncate" title={prompt}>{prompt.slice(0, 60)}{prompt.length > 60 ? '...' : ''}</p>
        </div>
        <div className="bg-white rounded-lg border p-3 md:p-4">
          <p className="text-xs text-gray-500 font-medium">Started</p>
          <p className="text-xs md:text-sm font-medium mt-1">{execution.started_at ? new Date(execution.started_at).toLocaleString() : 'Not started'}</p>
        </div>
        <div className="bg-white rounded-lg border p-3 md:p-4">
          <p className="text-xs text-gray-500 font-medium">Duration</p>
          <p className="text-xs md:text-sm font-medium mt-1">{duration != null ? `${duration}s` : '—'}</p>
        </div>
        <div className="bg-white rounded-lg border p-3 md:p-4">
          <p className="text-xs text-gray-500 font-medium flex items-center gap-1"><Hash className="h-3 w-3" />Tokens</p>
          <p className="text-xs md:text-sm font-medium mt-1 text-blue-700">
            {execution.total_input_tokens > 0
              ? `${execution.total_input_tokens.toLocaleString()} / ${execution.total_output_tokens.toLocaleString()}`
              : '—'}
          </p>
        </div>
        <div className="bg-white rounded-lg border p-3 md:p-4">
          <p className="text-xs text-gray-500 font-medium flex items-center gap-1"><Coins className="h-3 w-3" />Cost</p>
          <p className="text-xs md:text-sm font-medium mt-1 text-green-700">
            {execution.total_cost_usd > 0 ? `$${execution.total_cost_usd.toFixed(4)}` : '—'}
          </p>
        </div>
      </div>

      {/* Log + Output */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        {/* Left: tabbed log/messages panel */}
        <div className="flex flex-col h-[440px] md:h-[540px]">
          <LogMessagesTabs executionId={id} executionStatus={execution.status} />
        </div>

        {/* Right: output / approval */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-800 text-sm md:text-base">
              {execution.status === 'awaiting_approval' ? 'Agent Output (Pending Review)' : 'Output'}
            </h3>
            {(execution.status === 'running' || execution.status === 'pending') && (
              <Button variant="destructive" size="sm" onClick={() => cancelExecution.mutate(id)}>Cancel</Button>
            )}
          </div>

          {/* Approval panel — keyed on final_output so it remounts fresh when a new
              approval cycle starts (new agent output stored after rejection+re-run).
              Without the key, local decisionMade state persists across cycles. */}
          {execution.status === 'awaiting_approval' && (
            <ApprovalPanel
              key={execution.final_output ?? 'empty'}
              executionId={id}
              onDecision={handleDecision}
            />
          )}

          {/* Output box */}
          {execution.final_output ? (
            <div className={`bg-white rounded-lg border p-4 overflow-y-auto flex-1 ${execution.status === 'awaiting_approval' ? 'h-[260px] md:h-[300px] border-amber-200 bg-amber-50/30' : 'h-[340px] md:h-[460px]'}`}>
              {execution.status === 'awaiting_approval' && (
                <p className="text-xs text-amber-600 font-medium mb-2 pb-2 border-b border-amber-200">
                  ↓ Agent output — review before approving
                </p>
              )}
              <pre className="text-xs md:text-sm whitespace-pre-wrap text-gray-700">{execution.final_output}</pre>
            </div>
          ) : execution.error_message ? (
            <div className="bg-red-50 rounded-lg border border-red-200 p-4 h-[340px] md:h-[460px] overflow-y-auto">
              <p className="text-xs md:text-sm text-red-600">{execution.error_message}</p>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-lg border h-[340px] md:h-[460px] flex items-center justify-center text-gray-400">
              <div className="text-center">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                <p className="text-sm">Waiting for output...</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export function ExecutionsPage() {
  const { id } = useParams()
  const { data: executions = [], isLoading } = useExecutions()

  if (id) return <ExecutionDetail id={id} />

  return (
    <div className="p-4 md:p-6 lg:p-8">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-6 md:mb-8">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Executions</h1>
          <p className="text-gray-500 mt-1 text-sm md:text-base">Monitor all workflow runs in real-time</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-gray-400" /></div>
      ) : executions.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <Play className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-medium">No executions yet</h3>
          <p className="text-sm mt-1">Trigger a workflow to see executions here</p>
          <Link to="/workflows"><Button className="mt-4">Go to Workflows</Button></Link>
        </div>
      ) : (
        <div className="space-y-2 md:space-y-3">
          {executions.map(exec => (
            <Link key={exec.id} to={`/executions/${exec.id}`} className="block">
              <div className="flex items-center justify-between p-3 md:p-4 bg-white rounded-xl border hover:border-blue-300 hover:shadow-sm transition-all gap-2">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate text-sm md:text-base">
                    {((exec.trigger_payload as any)?.prompt || 'No prompt').slice(0, 80)}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {new Date(exec.created_at).toLocaleString()} · <span className="hidden sm:inline">{exec.trigger_type} trigger</span>
                  </p>
                </div>
                <StatusBadge status={exec.status} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
