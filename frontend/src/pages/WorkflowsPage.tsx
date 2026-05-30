import { useState, useEffect } from 'react'
import { useWorkflows, useWorkflow, useCreateWorkflow, useUpdateWorkflow, useDeleteWorkflow } from '@/api/workflows'
import { useTemplates, useInstantiateTemplate } from '@/api/templates'
import { WorkflowBuilder } from '@/components/workflows/WorkflowBuilder'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { GitFork, Plus, Trash2, ChevronRight, Loader2, ArrowLeft, Settings, Clock, Info, MousePointer2, Share2, Bot, CheckCircle2, PlayCircle, LayoutTemplate, Search, Zap } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import type { Workflow, Template } from '@/api/types'

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
          <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
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
            <Input value={cronValue} onChange={e => { setCronValue(e.target.value); setCronPreset('custom') }}
              placeholder="0 9 * * *" className="font-mono mt-1" />
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
          <Input value={telegramChatIds} onChange={e => setTelegramChatIds(e.target.value)} placeholder="123456789, 987654321" />
          <p className="text-xs text-gray-400">
            Comma-separated. Leave blank to accept messages from any chat.
            Get your chat ID by sending /start to your bot.
          </p>
        </div>
      )}

      {triggerType === 'webhook' && (
        <div className="p-4 bg-gray-50 rounded-lg border text-sm text-gray-600">
          <p className="font-medium mb-1">Webhook endpoint:</p>
          <code className="bg-gray-100 px-2 py-1 rounded text-xs block break-all">
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
  const [showBuilderInfo, setShowBuilderInfo] = useState(false)

  if (isLoading) return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-gray-400" /></div>
  if (!workflow) return <div className="p-8 text-gray-400">Workflow not found</div>

  return (
    <>
      {showSettings && (
        <Dialog open onOpenChange={() => setShowSettings(false)}>
          <DialogContent className="w-[95vw] max-w-md">
            <DialogHeader><DialogTitle>Workflow Settings — {workflow.name}</DialogTitle></DialogHeader>
            <WorkflowSettingsDialog workflow={workflow} onClose={() => setShowSettings(false)} />
          </DialogContent>
        </Dialog>
      )}

      {/* Builder instructions dialog */}
      <Dialog open={showBuilderInfo} onOpenChange={setShowBuilderInfo}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Share2 className="h-5 w-5 text-purple-500" />
              How to Build a Workflow
            </DialogTitle>
          </DialogHeader>
          <div className="py-2 space-y-5">
            <p className="text-sm text-gray-500">
              The canvas is a visual flow editor. Nodes represent steps; edges are the connections between them. Drag, drop, and connect to design your agent pipeline.
            </p>
            <ol className="space-y-4">
              {[
                {
                  icon: Bot,
                  color: 'bg-blue-100 text-blue-600',
                  title: 'Create agents first',
                  body: 'Go to the Agents page and create the AI agents you want to use. Each agent has its own model, system prompt, and tools. Come back here once they\'re ready.',
                },
                {
                  icon: MousePointer2,
                  color: 'bg-purple-100 text-purple-600',
                  title: 'Drag agents onto the canvas',
                  body: 'Open the left panel (or right-click the canvas) and drag an Agent node onto the canvas. The node will show the agent\'s name. You can also add Approval nodes for human-in-the-loop gates.',
                },
                {
                  icon: Share2,
                  color: 'bg-green-100 text-green-600',
                  title: 'Connect the nodes',
                  body: 'Hover the edge of any node to reveal a connection handle (circle). Drag from that handle to another node to create an edge. The flow always starts at Start and ends at End.',
                },
                {
                  icon: CheckCircle2,
                  color: 'bg-orange-100 text-orange-600',
                  title: 'Save your layout',
                  body: 'Click the Save button in the canvas toolbar after each change. Unsaved changes are lost on navigation.',
                },
                {
                  icon: PlayCircle,
                  color: 'bg-teal-100 text-teal-600',
                  title: 'Run the workflow',
                  body: 'Use the Run button at the top of the canvas or go to the Executions page. Enter a prompt as the starting input and watch the agents collaborate in real-time.',
                },
              ].map((step, i) => {
                const StepIcon = step.icon
                return (
                  <li key={i} className="flex gap-3">
                    <div className={`mt-0.5 shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${step.color}`}>
                      <StepIcon className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-gray-800">
                        <span className="text-gray-400 mr-1.5">{i + 1}.</span>{step.title}
                      </p>
                      <p className="text-sm text-gray-500 mt-0.5">{step.body}</p>
                    </div>
                  </li>
                )
              })}
            </ol>
            <div className="rounded-lg bg-purple-50 border border-purple-100 px-4 py-3 text-sm text-purple-700 space-y-2">
              <p className="font-semibold">Node types:</p>
              <ul className="space-y-2 text-purple-700">
                <li className="flex gap-2">
                  <span className="shrink-0">▶</span>
                  <span><strong>Start</strong> — entry point that receives the initial prompt and passes it into the pipeline.</span>
                </li>
                <li className="flex gap-2">
                  <span className="shrink-0">🤖</span>
                  <span><strong>Agent</strong> — runs an AI agent. Its output becomes the input for the next node.</span>
                </li>
                <li className="flex gap-2">
                  <span className="shrink-0">🔀</span>
                  <div>
                    <span><strong>Router</strong> — branches the flow based on the content of the previous output. Add a Router node, then draw multiple edges out of it. Click any outgoing edge label to set a <em>keyword condition</em> — if that keyword appears in the upstream output the flow follows that branch. Leave an edge blank to make it the fallback (always followed if no keyword matched).</span>
                    <p className="mt-1 text-purple-600 text-xs">Example: an Agent classifies a support ticket as "billing" or "technical" → a Router sends it to the right specialist agent based on which word appears in the output.</p>
                  </div>
                </li>
                <li className="flex gap-2">
                  <span className="shrink-0">✋</span>
                  <span><strong>Approval</strong> — pauses execution and waits for a human to approve or reject. If rejected, the previous agent retries with your feedback.</span>
                </li>
                <li className="flex gap-2">
                  <span className="shrink-0">⏹</span>
                  <span><strong>End</strong> — marks the workflow as complete and captures the final output.</span>
                </li>
              </ul>
            </div>
          </div>
          <div className="flex justify-end pt-2">
            <Button variant="outline" onClick={() => setShowBuilderInfo(false)}>Got it</Button>
          </div>
        </DialogContent>
      </Dialog>

      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2 border-b bg-gray-50">
        <div className="flex flex-wrap items-center gap-2 text-sm text-gray-500">
          <Clock className="h-3.5 w-3.5 shrink-0" />
          <span>Trigger: <span className="font-medium text-gray-700 capitalize">{workflow.trigger_type}</span></span>
          {workflow.trigger_type === 'schedule' && (workflow.trigger_config as any)?.cron && (
            <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">{(workflow.trigger_config as any).cron}</code>
          )}
          {workflow.trigger_type === 'telegram' && (
            <span className="text-xs text-blue-600">Telegram</span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowBuilderInfo(true)}
            className="p-2 rounded-full text-gray-400 hover:text-purple-500 hover:bg-purple-50 transition-colors"
            title="How to build a workflow"
          >
            <Info className="h-4 w-4" />
          </button>
          <Button variant="ghost" size="sm" onClick={() => setShowSettings(true)}>
            <Settings className="h-4 w-4 mr-1" /> Settings
          </Button>
        </div>
      </div>
      <WorkflowBuilder workflow={workflow} />
    </>
  )
}

export function WorkflowsPage() {
  const { data: workflows = [], isLoading } = useWorkflows()
  const { data: templates = [] } = useTemplates()
  const createWorkflow = useCreateWorkflow()
  const deleteWorkflow = useDeleteWorkflow()
  const instantiate = useInstantiateTemplate()
  const location = useLocation()

  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [createTab, setCreateTab] = useState<'scratch' | 'template'>('scratch')
  const [showInfo, setShowInfo] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [createError, setCreateError] = useState('')
  const [templateSearch, setTemplateSearch] = useState('')

  // Auto-select a workflow navigated here from TemplatesPage
  useEffect(() => {
    const state = location.state as { selectedWorkflowId?: string } | null
    if (state?.selectedWorkflowId) {
      setSelectedId(state.selectedWorkflowId)
      window.history.replaceState({}, '')
    }
  }, [location.state])

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

  const handleInstantiateFromDialog = async (slug: string) => {
    setCreateError('')
    try {
      const result = await instantiate.mutateAsync(slug) as { workflow_id?: string }
      setShowCreate(false)
      if (result?.workflow_id) setSelectedId(result.workflow_id)
    } catch (e: unknown) {
      setCreateError(e instanceof Error ? e.message : 'Failed to create from template')
    }
  }

  const filteredTemplates = templates.filter((t: Template) => {
    const q = templateSearch.toLowerCase()
    return !q || t.name.toLowerCase().includes(q) || t.description.toLowerCase().includes(q)
  })

  if (selectedId) {
    const wf = workflows.find(w => w.id === selectedId)
    return (
      <div className="flex flex-col h-screen">
        <div className="flex items-center gap-2 md:gap-3 px-4 md:px-6 py-3 md:py-4 border-b bg-white">
          <button onClick={() => setSelectedId(null)} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 shrink-0">
            <ArrowLeft className="h-4 w-4" /> <span className="hidden sm:inline">Workflows</span>
          </button>
          <span className="text-gray-300">/</span>
          <h2 className="font-semibold text-gray-900 truncate">{wf?.name || 'Workflow'}</h2>
          {wf?.template_slug && <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs shrink-0">Template</span>}
        </div>
        <div className="flex-1 overflow-hidden flex flex-col">
          <WorkflowDetail workflowId={selectedId} />
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 md:p-6 lg:p-8">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-6 md:mb-8">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Workflows</h1>
          <p className="text-gray-500 mt-1 text-sm md:text-base">Build and manage agent collaboration workflows</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 md:gap-3 shrink-0">
          <Link to="/templates"><Button variant="outline" size="sm" className="md:size-default">Browse Templates</Button></Link>
          <button
            onClick={() => setShowInfo(true)}
            className="p-2 rounded-full text-gray-400 hover:text-blue-500 hover:bg-blue-50 transition-colors"
            title="How to create a workflow"
          >
            <Info className="h-5 w-5" />
          </button>
          <Button onClick={() => setShowCreate(true)} size="sm" className="md:size-default"><Plus className="h-4 w-4 mr-1 md:mr-2" />New Workflow</Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-gray-400" /></div>
      ) : workflows.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <GitFork className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-medium">No workflows yet</h3>
          <p className="text-sm mt-1">Create a workflow or start from a template</p>
          <div className="flex flex-wrap gap-3 justify-center mt-4">
            <Button onClick={() => setShowCreate(true)}>Create Workflow</Button>
            <Link to="/templates"><Button variant="outline">Browse Templates</Button></Link>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {workflows.map(wf => (
            <div key={wf.id}
              className="flex items-center justify-between p-3 md:p-4 bg-white rounded-xl border hover:border-blue-300 hover:shadow-sm transition-all cursor-pointer group gap-3"
              onClick={() => setSelectedId(wf.id)}>
              <div className="flex items-center gap-3 min-w-0">
                <div className="p-2 md:p-2.5 bg-purple-100 rounded-lg shrink-0">
                  <GitFork className="h-4 w-4 md:h-5 md:w-5 text-purple-600" />
                </div>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-1.5 md:gap-2">
                    <h3 className="font-semibold text-gray-900 truncate">{wf.name}</h3>
                    {wf.template_slug && <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs shrink-0">From template</span>}
                    <span className={`h-2 w-2 shrink-0 rounded-full ${wf.is_active ? 'bg-green-400' : 'bg-gray-300'}`} />
                  </div>
                  <p className="text-xs md:text-sm text-gray-500 flex flex-wrap items-center gap-1 md:gap-2 mt-0.5">
                    <span className="truncate">{wf.description || 'No description'}</span>
                    <span className="hidden sm:inline">•</span>
                    <span className="hidden sm:flex capitalize items-center gap-1">
                      {wf.trigger_type === 'schedule' && <Clock className="h-3 w-3" />}
                      {wf.trigger_type}
                    </span>
                    {wf.trigger_type === 'schedule' && (wf.trigger_config as any)?.cron && (
                      <code className="hidden md:inline bg-gray-100 px-1 py-0.5 rounded text-xs">{(wf.trigger_config as any).cron}</code>
                    )}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1 md:gap-2 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button variant="ghost" size="icon" onClick={(e) => { e.stopPropagation(); deleteWorkflow.mutate(wf.id) }} className="h-7 w-7 md:h-8 md:w-8 text-red-400 hover:text-red-600">
                  <Trash2 className="h-3.5 w-3.5 md:h-4 md:w-4" />
                </Button>
                <ChevronRight className="h-4 w-4 md:h-5 md:w-5 text-gray-400" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* How-to instructions dialog */}
      <Dialog open={showInfo} onOpenChange={setShowInfo}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <GitFork className="h-5 w-5 text-purple-500" />
              How to Create a Workflow
            </DialogTitle>
          </DialogHeader>
          <div className="py-2 space-y-5">
            <p className="text-sm text-gray-500">
              A workflow is a pipeline of AI agents that collaborate to complete a task. Here's how to set one up from scratch.
            </p>
            <ol className="space-y-4">
              {[
                {
                  icon: Bot,
                  color: 'bg-blue-100 text-blue-600',
                  title: 'Create your agents',
                  body: 'Head to the Agents page and create one or more agents. Each agent needs a name, a model (e.g. GPT-4o), and a system prompt that defines its role.',
                },
                {
                  icon: Plus,
                  color: 'bg-purple-100 text-purple-600',
                  title: 'Create a new workflow',
                  body: 'Click "New Workflow", enter a name and an optional description, then hit Create. The workflow builder opens automatically.',
                },
                {
                  icon: Share2,
                  color: 'bg-green-100 text-green-600',
                  title: 'Build the graph',
                  body: 'In the builder, drag your agents from the side panel onto the canvas. Connect them in order: Start → Agent(s) → End. Add Approval nodes anywhere you want a human review step.',
                },
                {
                  icon: Settings,
                  color: 'bg-orange-100 text-orange-600',
                  title: 'Configure the trigger',
                  body: 'Click Settings (top-right of the builder) to choose how the workflow starts: manually, on a schedule (cron), via a Telegram message, or via a webhook POST.',
                },
                {
                  icon: PlayCircle,
                  color: 'bg-teal-100 text-teal-600',
                  title: 'Run it',
                  body: 'Hit the Run button in the builder toolbar, or go to the Executions page. Type a starting prompt and watch the agents work through the pipeline in real-time.',
                },
              ].map((step, i) => {
                const StepIcon = step.icon
                return (
                  <li key={i} className="flex gap-3">
                    <div className={`mt-0.5 shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${step.color}`}>
                      <StepIcon className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-gray-800">
                        <span className="text-gray-400 mr-1.5">{i + 1}.</span>{step.title}
                      </p>
                      <p className="text-sm text-gray-500 mt-0.5">{step.body}</p>
                    </div>
                  </li>
                )
              })}
            </ol>
            <div className="rounded-lg bg-blue-50 border border-blue-100 px-4 py-3 text-sm text-blue-700">
              <strong>Tip:</strong> Not sure where to start? Use a <strong>Template</strong> — it creates agents and a pre-wired workflow in one click. Click "Browse Templates" to explore.
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setShowInfo(false)}>Close</Button>
            <Button onClick={() => { setShowInfo(false); setShowCreate(true) }}>
              <Plus className="h-4 w-4 mr-2" />Create a Workflow
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={showCreate} onOpenChange={v => { setShowCreate(v); setCreateError(''); setCreateTab('scratch') }}>
        <DialogContent className="w-[95vw] max-w-xl">
          <DialogHeader><DialogTitle>New Workflow</DialogTitle></DialogHeader>

          {/* Tabs */}
          <div className="flex gap-1 p-1 bg-gray-100 rounded-lg mb-2">
            <button
              onClick={() => setCreateTab('scratch')}
              className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${createTab === 'scratch' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}
            >
              <Plus className="h-4 w-4" /> From Scratch
            </button>
            <button
              onClick={() => setCreateTab('template')}
              className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${createTab === 'template' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}
            >
              <LayoutTemplate className="h-4 w-4" /> From Template
            </button>
          </div>

          {createError && <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-2 text-sm">{createError}</div>}

          {createTab === 'scratch' ? (
            <div className="space-y-4">
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
          ) : (
            <div className="space-y-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                <Input
                  value={templateSearch}
                  onChange={e => setTemplateSearch(e.target.value)}
                  placeholder="Search templates…"
                  className="pl-9"
                />
              </div>
              <div className="max-h-80 overflow-y-auto space-y-2 pr-1">
                {filteredTemplates.length === 0 ? (
                  <div className="text-center py-8 text-gray-400">
                    <Zap className="h-8 w-8 mx-auto mb-2 opacity-30" />
                    <p className="text-sm">No templates found</p>
                  </div>
                ) : filteredTemplates.map((t: Template) => (
                  <button
                    key={t.slug}
                    onClick={() => handleInstantiateFromDialog(t.slug)}
                    disabled={instantiate.isPending}
                    className="w-full text-left p-3 rounded-xl border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all disabled:opacity-50 group"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-1.5 mb-1">
                          <span className="font-medium text-sm text-gray-900">{t.name}</span>
                          {t.difficulty && (
                            <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 capitalize">{t.difficulty}</span>
                          )}
                          <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">{t.agent_count} agents</span>
                        </div>
                        <p className="text-xs text-gray-500 line-clamp-1">{t.description}</p>
                        {t.agents_preview && t.agents_preview.length > 0 && (
                          <div className="flex items-center gap-1 mt-1.5 flex-wrap">
                            {t.agents_preview.map((a, i) => (
                              <span key={i} className="flex items-center gap-1">
                                <span className="text-xs px-2 py-0.5 rounded-full text-white font-medium" style={{ backgroundColor: a.color }}>{a.name}</span>
                                {i < t.agents_preview!.length - 1 && <ChevronRight className="h-3 w-3 text-gray-300 shrink-0" />}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-blue-500 shrink-0 mt-1" />
                    </div>
                  </button>
                ))}
              </div>
              {instantiate.isPending && (
                <div className="flex items-center gap-2 text-sm text-blue-600 py-2">
                  <Loader2 className="h-4 w-4 animate-spin" /> Creating workflow from template…
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
