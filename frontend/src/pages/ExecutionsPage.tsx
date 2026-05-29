import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useExecutions, useExecution, useCancelExecution, useApproveExecution } from '@/api/executions'
import { LogStream } from '@/components/executions/LogStream'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ArrowLeft, CheckCircle, XCircle, Clock, Loader2, Play, Coins, Hash, UserCheck, ThumbsUp, ThumbsDown } from 'lucide-react'
import type { Execution } from '@/api/types'

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
    <Badge variant={c.variant} className={`flex items-center gap-1 ${c.className ?? ''}`}>
      <Icon className={`h-3 w-3 ${c.spin ? 'animate-spin' : ''}`} /> {c.label}
    </Badge>
  )
}

function ApprovalPanel({ executionId }: { executionId: string }) {
  const approve = useApproveExecution()
  const [showRejectDialog, setShowRejectDialog] = useState(false)
  const [rejectComment, setRejectComment] = useState('')

  return (
    <div className="mb-4 p-4 bg-amber-50 border-2 border-amber-400 rounded-xl">
      <div className="flex items-center gap-3 mb-3">
        <div className="h-10 w-10 rounded-full bg-amber-400 flex items-center justify-center flex-shrink-0">
          <UserCheck className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="font-semibold text-amber-900">Human Approval Required</p>
          <p className="text-sm text-amber-700">This workflow is paused and waiting for your decision to continue.</p>
        </div>
      </div>
      <div className="flex gap-3">
        <Button
          className="flex-1 bg-green-600 hover:bg-green-700 text-white"
          disabled={approve.isPending}
          onClick={() => approve.mutate({ id: executionId, decision: 'approve' })}
        >
          {approve.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <ThumbsUp className="h-4 w-4 mr-2" />}
          Approve — Continue
        </Button>
        <Button
          variant="destructive"
          className="flex-1"
          disabled={approve.isPending}
          onClick={() => setShowRejectDialog(true)}
        >
          <ThumbsDown className="h-4 w-4 mr-2" /> Reject — Stop
        </Button>
      </div>

      <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <DialogContent className="max-w-sm">
          <DialogHeader><DialogTitle>Reject workflow?</DialogTitle></DialogHeader>
          <p className="text-sm text-gray-500">Provide an optional reason for rejection:</p>
          <Textarea
            value={rejectComment}
            onChange={e => setRejectComment(e.target.value)}
            placeholder="Reason for rejection..."
            className="h-24"
          />
          <div className="flex gap-3 pt-1">
            <Button
              variant="destructive"
              className="flex-1"
              disabled={approve.isPending}
              onClick={() => {
                approve.mutate({ id: executionId, decision: 'reject', comment: rejectComment })
                setShowRejectDialog(false)
              }}
            >
              Confirm Rejection
            </Button>
            <Button variant="outline" onClick={() => setShowRejectDialog(false)}>Cancel</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function ExecutionDetail({ id }: { id: string }) {
  const { data: execution, isLoading } = useExecution(id)
  const cancelExecution = useCancelExecution()
  const navigate = useNavigate()

  if (isLoading) return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-gray-400" /></div>
  if (!execution) return <div className="p-8 text-gray-400">Execution not found</div>

  const prompt = (execution.trigger_payload as any)?.prompt || 'No prompt'
  const duration = execution.completed_at && execution.started_at
    ? Math.round((new Date(execution.completed_at).getTime() - new Date(execution.started_at).getTime()) / 1000)
    : null

  return (
    <div className="p-6 max-w-full">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/executions')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800">
          <ArrowLeft className="h-4 w-4" /> Executions
        </button>
        <span className="text-gray-300">/</span>
        <h2 className="font-semibold text-gray-900">Execution Detail</h2>
        <StatusBadge status={execution.status} />
      </div>

      <div className="grid grid-cols-5 gap-4 mb-6">
        <div className="bg-white rounded-lg border p-4">
          <p className="text-xs text-gray-500 font-medium">Trigger</p>
          <p className="text-sm font-medium mt-1 truncate" title={prompt}>{prompt.slice(0, 60)}{prompt.length > 60 ? '...' : ''}</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-xs text-gray-500 font-medium">Started</p>
          <p className="text-sm font-medium mt-1">{execution.started_at ? new Date(execution.started_at).toLocaleString() : 'Not started'}</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-xs text-gray-500 font-medium">Duration</p>
          <p className="text-sm font-medium mt-1">{duration != null ? `${duration}s` : '—'}</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-xs text-gray-500 font-medium flex items-center gap-1"><Hash className="h-3 w-3" />Tokens</p>
          <p className="text-sm font-medium mt-1 text-blue-700">
            {execution.total_input_tokens > 0
              ? `${execution.total_input_tokens.toLocaleString()} in / ${execution.total_output_tokens.toLocaleString()} out`
              : '—'}
          </p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-xs text-gray-500 font-medium flex items-center gap-1"><Coins className="h-3 w-3" />Cost</p>
          <p className="text-sm font-medium mt-1 text-green-700">
            {execution.total_cost_usd > 0 ? `$${execution.total_cost_usd.toFixed(4)}` : '—'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="h-[500px]">
          <h3 className="font-semibold text-gray-800 mb-3">Live Log Stream</h3>
          <LogStream executionId={id} />
        </div>
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-800">Output</h3>
            {(execution.status === 'running' || execution.status === 'pending') && (
              <Button variant="destructive" size="sm" onClick={() => cancelExecution.mutate(id)}>Cancel</Button>
            )}
          </div>
          {execution.status === 'awaiting_approval' && <ApprovalPanel executionId={id} />}
          {execution.final_output ? (
            <div className="bg-white rounded-lg border p-4 h-[460px] overflow-y-auto">
              <pre className="text-sm whitespace-pre-wrap text-gray-700">{execution.final_output}</pre>
            </div>
          ) : execution.error_message ? (
            <div className="bg-red-50 rounded-lg border border-red-200 p-4 h-[460px] overflow-y-auto">
              <p className="text-sm text-red-600">{execution.error_message}</p>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-lg border h-[460px] flex items-center justify-center text-gray-400">
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
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Executions</h1>
          <p className="text-gray-500 mt-1">Monitor all workflow runs in real-time</p>
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
        <div className="space-y-3">
          {executions.map(exec => (
            <Link key={exec.id} to={`/executions/${exec.id}`} className="block">
              <div className="flex items-center justify-between p-4 bg-white rounded-xl border hover:border-blue-300 hover:shadow-sm transition-all">
                <div className="flex-1 min-w-0 mr-4">
                  <p className="font-medium text-gray-900 truncate">
                    {((exec.trigger_payload as any)?.prompt || 'No prompt').slice(0, 80)}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {new Date(exec.created_at).toLocaleString()} • {exec.trigger_type} trigger
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
