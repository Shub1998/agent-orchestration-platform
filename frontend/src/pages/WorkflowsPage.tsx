import { useState } from 'react'
import { useWorkflows, useWorkflow, useCreateWorkflow, useUpdateWorkflow, useDeleteWorkflow } from '@/api/workflows'
import { WorkflowBuilder } from '@/components/workflows/WorkflowBuilder'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { GitFork, Plus, Trash2, ChevronRight, Loader2, ArrowLeft, Settings, Clock } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Workflow } from '@/api/types'

const CRON_PRESETS = [
  { label: 'Every hour', value: '0 * * * *' },
  { label: 'Every day at 9am', value: '0 9 * * *' },
  { label: 'Every Monday 9am', value: '0 9 * * 1' },
  { label: 'Every 6 hours', value: '0 */6 * * *' },
  { label: 'Custom...', value: 'custom' },
]

function WorkflowSettingsDialog({ workflow, onClose }: { workflow: Workflow; onClose: () => void }) {
  const updateWorkflow = useUpdateWorkflow()
  const [triggerType, setTriggerType] = useState(workflow.trigger_type)
  const [cronPreset, setCronPreset] = useState('custom')
  const [cronValue, setCronValue] = useState((workflow.trigger_config as any)?.cron || '')
  const [telegramChatIds, setTelegramChatIds] = useState(
    ((workflow.trigger_config as any)?.chat_ids || []).join(', ')
  )

  const handleSave = async () => {
    let trigger_config: Record<string, unknown> = {}
    if (triggerType === 'schedule') {
      trigger_config = { cron: cronValue }
    } else if (triggerType === 'telegram') {
      const ids = telegramChatIds.split(',').map((s: string) => parseInt(s.trim())).filter((n: number) => !isNaN(n))
      trigger_config = { chat_ids: ids }
    }
    await updateWorkflow.mutateAsync({ id: workflow.id, trigger_type: triggerType, trigger_config })
    onClose()
  }

  return (
    <div className="space-y-5">
      <div>
        <Label>Trigger Type</Label>
        <Select value={triggerType} onValueChange={setTriggerType}>
          <SelectTrigger className="mt-1">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="manual">Manual (UI / API)</SelectItem>
            <SelectItem value="schedule">Scheduled (Cron)</SelectItem>
            <SelectItem value="telegram">Telegram Message</SelectItem>
            <SelectItem value="webhook">Webhook (POST)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {triggerType === 'schedule' && (
        <div className="space-y-3 p-4 bg-blue-50 rounded-lg border border-blue-100">
          <Label className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" />Schedule</Label>
          <Select value={cronPreset} onValueChange={v => {
            setCronPreset(v)
            if (v !== 'custom') setCronValue(v)
          }}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {CRON_PRESETS.map(p => <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>)}
            </SelectContent>
          </Select>
          <div>
            <Label className="text-xs text-gray-500">Cron expression</Label>
            <Input
              value={cronValue}
              onChange={e => { setCronValue(e.target.value); setCronPreset('custom') }}
              placeholder="0 9 * * *"
              className="font-mono mt-1"
            />
            <p className="text-xs text-gray-400 mt-1">
              Format: minute hour day month weekday — e.g. <code>0 9 * * 1</code> = every Monday 9am
            </p>
          </div>
          <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2">
            ⚠ Scheduled runs require the <code>beat</code> worker service and a non-empty workflow prompt
            set in <code>trigger_config.prompt</code>.
          </div>
        </div>
      )}

      {triggerType === 'telegram' && (
        <div className="space-y-2 p-4 bg-blue-50 rounded-lg border border-blue-100">
          <Label>Allowed Telegram Chat IDs</Label>
          <Input
            value={telegramChatIds}
            onChange={e => setTelegramChatIds(e.target.value)}
            placeholder="123456789, 987654321"
          />
          <p className="text-xs text-gray-400">
            Comma-separated. Leave blank to accept messages from any chat.
            Get your chat ID by sending /start to your bot.
          </p>
        </div>
      )}

      {triggerType === 'webhook' && (
        <div className="p-4 bg-gray-50 rounded-lg border text-sm text-gray-600">
          <p className="font-medium mb-1">Webhook endpoint:</p>
          <code className="bg-gray-100 px-2 py-1 rounded text-xs block">
            POST /api/v1/workflows/{workflow.id}/trigger
          </code>
          <p className="mt-2 text-xs text-gray-400">Body: {`{ "prompt": "your task here" }`}</p>
        </div>
      )}

      <div className="flex gap-3 pt-1">
        <Button onClick={handleSave} disabled={updateWorkflow.isPending} className="flex-1">
          {updateWorkflow.isPending && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
          Save Settings
        </Button>
        <Button variant="outline" onClick={onClose}>Cancel</Button>
      </div>
    </div>
  )
}

function WorkflowDetail({ workflowId }: { workflowId: string }) {
  const { data: workflow, isLoading } = useWorkflow(workflowId)
  const [showSettings, setShowSettings] = useState(false)

  if (isLoading) return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-gray-400" /></div>
  if (!workflow) return <div className="p-8 text-gray-400">Workflow not found</div>

  return (
    <>
      {showSettings && (
        <Dialog open onOpenChange={() => setShowSettings(false)}>
          <DialogContent className="max-w-md">
            <DialogHeader><DialogTitle>Workflow Settings — {workflow.name}</DialogTitle></DialogHeader>
            <WorkflowSettingsDialog workflow={workflow} onClose={() => setShowSettings(false)} />
          </DialogContent>
        </Dialog>
      )}
      <div className="flex items-center justify-between px-4 py-2 border-b bg-gray-50">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Clock className="h-3.5 w-3.5" />
          <span>Trigger: <span className="font-medium text-gray-700 capitalize">{workflow.trigger_type}</span></span>
          {workflow.trigger_type === 'schedule' && (workflow.trigger_config as any)?.cron && (
            <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">{(workflow.trigger_config as any).cron}</code>
          )}
          {workflow.trigger_type === 'telegram' && (
            <span className="text-xs text-blue-600">Telegram</span>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={() => setShowSettings(true)}>
          <Settings className="h-4 w-4 mr-1" /> Settings
        </Button>
      </div>
      <WorkflowBuilder workflow={workflow} />
    </>
  )
}

export function WorkflowsPage() {
  const { data: workflows = [], isLoading } = useWorkflows()
  const createWorkflow = useCreateWorkflow()
  const deleteWorkflow = useDeleteWorkflow()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [createError, setCreateError] = useState('')

  const handleCreate = async () => {
    if (!newName.trim()) return
    setCreateError('')
    try {
      const wf = await createWorkflow.mutateAsync({ name: newName, description: newDesc })
      setShowCreate(false)
      setNewName('')
      setNewDesc('')
      setSelectedId(wf.id)
    } catch (e: unknown) {
      setCreateError(e instanceof Error ? e.message : 'Failed to create workflow')
    }
  }

  if (selectedId) {
    const wf = workflows.find(w => w.id === selectedId)
    return (
      <div className="flex flex-col h-screen">
        <div className="flex items-center gap-3 px-6 py-4 border-b bg-white">
          <button onClick={() => setSelectedId(null)} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800">
            <ArrowLeft className="h-4 w-4" /> Workflows
          </button>
          <span className="text-gray-300">/</span>
          <h2 className="font-semibold text-gray-900">{wf?.name || 'Workflow'}</h2>
          {wf?.template_slug && <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">Template</span>}
        </div>
        <div className="flex-1 overflow-hidden flex flex-col">
          <WorkflowDetail workflowId={selectedId} />
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Workflows</h1>
          <p className="text-gray-500 mt-1">Build and manage agent collaboration workflows</p>
        </div>
        <div className="flex gap-3">
          <Link to="/templates"><Button variant="outline">Browse Templates</Button></Link>
          <Button onClick={() => setShowCreate(true)}><Plus className="h-4 w-4 mr-2" />New Workflow</Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-gray-400" /></div>
      ) : workflows.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <GitFork className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-medium">No workflows yet</h3>
          <p className="text-sm mt-1">Create a workflow or start from a template</p>
          <div className="flex gap-3 justify-center mt-4">
            <Button onClick={() => setShowCreate(true)}>Create Workflow</Button>
            <Link to="/templates"><Button variant="outline">Browse Templates</Button></Link>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {workflows.map(wf => (
            <div key={wf.id} className="flex items-center justify-between p-4 bg-white rounded-xl border hover:border-blue-300 hover:shadow-sm transition-all cursor-pointer group"
              onClick={() => setSelectedId(wf.id)}>
              <div className="flex items-center gap-4">
                <div className="p-2.5 bg-purple-100 rounded-lg">
                  <GitFork className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-900">{wf.name}</h3>
                    {wf.template_slug && <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">From template</span>}
                    <span className={`h-2 w-2 rounded-full ${wf.is_active ? 'bg-green-400' : 'bg-gray-300'}`} />
                  </div>
                  <p className="text-sm text-gray-500 flex items-center gap-2">
                    {wf.description || 'No description'}
                    <span>•</span>
                    <span className="capitalize flex items-center gap-1">
                      {wf.trigger_type === 'schedule' && <Clock className="h-3 w-3" />}
                      {wf.trigger_type}
                    </span>
                    {wf.trigger_type === 'schedule' && (wf.trigger_config as any)?.cron && (
                      <code className="bg-gray-100 px-1 py-0.5 rounded text-xs">{(wf.trigger_config as any).cron}</code>
                    )}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button variant="ghost" size="icon" onClick={(e) => { e.stopPropagation(); deleteWorkflow.mutate(wf.id) }} className="h-8 w-8 text-red-400 hover:text-red-600">
                  <Trash2 className="h-4 w-4" />
                </Button>
                <ChevronRight className="h-5 w-5 text-gray-400" />
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={showCreate} onOpenChange={v => { setShowCreate(v); setCreateError('') }}>
        <DialogContent className="max-w-md">
          <DialogHeader><DialogTitle>Create New Workflow</DialogTitle></DialogHeader>
          <div className="space-y-4">
            {createError && <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-2 text-sm">{createError}</div>}
            <div>
              <Label>Name *</Label>
              <Input value={newName} onChange={e => setNewName(e.target.value)} placeholder="My Research Workflow" autoFocus />
            </div>
            <div>
              <Label>Description</Label>
              <Input value={newDesc} onChange={e => setNewDesc(e.target.value)} placeholder="What does this workflow do?" />
            </div>
            <div className="flex gap-3">
              <Button onClick={handleCreate} disabled={!newName.trim() || createWorkflow.isPending} className="flex-1">
                {createWorkflow.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Create Workflow
              </Button>
              <Button variant="outline" onClick={() => { setShowCreate(false); setCreateError('') }}>Cancel</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
