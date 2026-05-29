import { useState } from 'react'
import { useAgents, useCreateAgent, useUpdateAgent, useDeleteAgent, useTestAgent, useAvailableTools } from '@/api/agents'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Bot, Plus, Trash2, Edit, Zap, Brain, Wrench, Send, Loader2, Shield, X } from 'lucide-react'
import type { Agent } from '@/api/types'

const MODELS = [
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini', provider: 'openai' },
  { value: 'gpt-4o', label: 'GPT-4o', provider: 'openai' },
  { value: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku', provider: 'anthropic' },
  { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet', provider: 'anthropic' },
]

const AVATAR_COLORS = ['#6366f1', '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#f97316']

function AgentForm({ agent, onSave, onClose }: { agent?: Agent; onSave: (data: Partial<Agent>) => void; onClose: () => void }) {
  const { data: tools = [] } = useAvailableTools()
  const [form, setForm] = useState({
    name: agent?.name || '',
    role: agent?.role || 'assistant',
    description: agent?.description || '',
    system_prompt: agent?.system_prompt || '',
    model: agent?.model || 'gpt-4o-mini',
    provider: agent?.provider || 'openai',
    temperature: agent?.temperature ?? 0.7,
    max_iterations: agent?.max_iterations ?? 10,
    memory_enabled: agent?.memory_enabled ?? true,
    tools: agent?.tools || [],
    telegram_enabled: agent?.telegram_enabled || false,
    avatar_color: agent?.avatar_color || '#6366f1',
    max_output_tokens: agent?.max_output_tokens ?? 4096,
    guardrail_keywords: agent?.guardrail_keywords || [],
    _guardrailInput: '',
  })

  const toggleTool = (toolName: string) => {
    setForm(f => ({ ...f, tools: f.tools.includes(toolName) ? f.tools.filter(t => t !== toolName) : [...f.tools, toolName] }))
  }

  return (
    <div className="space-y-4 max-h-[75vh] overflow-y-auto pr-1">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>Name *</Label>
          <Input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Research Agent" />
        </div>
        <div>
          <Label>Role</Label>
          <Input value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))} placeholder="researcher" />
        </div>
      </div>

      <div>
        <Label>Description</Label>
        <Input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="Brief description of this agent's purpose" />
      </div>

      <div>
        <Label>System Prompt *</Label>
        <Textarea value={form.system_prompt} onChange={e => setForm(f => ({ ...f, system_prompt: e.target.value }))} placeholder="You are an expert researcher..." className="h-28" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>Model</Label>
          <Select value={form.model} onValueChange={v => {
            const m = MODELS.find(m => m.value === v)
            setForm(f => ({ ...f, model: v, provider: m?.provider || 'openai' }))
          }}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {MODELS.map(m => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Temperature ({form.temperature})</Label>
          <input type="range" min="0" max="2" step="0.1" value={form.temperature}
            onChange={e => setForm(f => ({ ...f, temperature: parseFloat(e.target.value) }))}
            className="w-full mt-2" />
        </div>
      </div>

      <div>
        <Label className="mb-2 block">Tools</Label>
        <div className="flex flex-wrap gap-2">
          {(tools as { name: string; description: string }[]).map((tool) => (
            <button key={tool.name} onClick={() => toggleTool(tool.name)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${form.tools.includes(tool.name) ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'}`}
              title={tool.description}>
              {tool.name}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-6">
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={form.memory_enabled} onChange={e => setForm(f => ({ ...f, memory_enabled: e.target.checked }))} className="rounded" />
          Enable Memory
        </label>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={form.telegram_enabled} onChange={e => setForm(f => ({ ...f, telegram_enabled: e.target.checked }))} className="rounded" />
          Telegram Enabled
        </label>
      </div>

      <div className="space-y-3 p-3 bg-orange-50 rounded-lg border border-orange-100">
        <Label className="flex items-center gap-1 text-orange-700"><Shield className="h-3.5 w-3.5" />Guardrails</Label>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label className="text-xs text-gray-500">Max output tokens</Label>
            <Input type="number" min={256} max={32000} value={form.max_output_tokens}
              onChange={e => setForm(f => ({ ...f, max_output_tokens: parseInt(e.target.value) || 4096 }))} />
          </div>
          <div>
            <Label className="text-xs text-gray-500">Blocked keywords (press Enter to add)</Label>
            <Input
              value={form._guardrailInput}
              onChange={e => setForm(f => ({ ...f, _guardrailInput: e.target.value }))}
              onKeyDown={e => {
                if (e.key === 'Enter' && form._guardrailInput.trim()) {
                  setForm(f => ({ ...f, guardrail_keywords: [...f.guardrail_keywords, f._guardrailInput.trim()], _guardrailInput: '' }))
                }
              }}
              placeholder="e.g. confidential"
            />
          </div>
        </div>
        {form.guardrail_keywords.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {form.guardrail_keywords.map(kw => (
              <span key={kw} className="flex items-center gap-1 px-2 py-0.5 bg-orange-100 text-orange-700 rounded text-xs">
                {kw}
                <button onClick={() => setForm(f => ({ ...f, guardrail_keywords: f.guardrail_keywords.filter(k => k !== kw) }))}>
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      <div>
        <Label className="mb-2 block">Avatar Color</Label>
        <div className="flex gap-2">
          {AVATAR_COLORS.map(color => (
            <button key={color} onClick={() => setForm(f => ({ ...f, avatar_color: color }))}
              className={`h-7 w-7 rounded-full border-2 transition-all ${form.avatar_color === color ? 'border-gray-800 scale-110' : 'border-transparent'}`}
              style={{ backgroundColor: color }} />
          ))}
        </div>
      </div>

      <div className="flex gap-3 pt-2">
        <Button onClick={() => { const { _guardrailInput, ...data } = form; onSave(data) }} className="flex-1">Save Agent</Button>
        <Button variant="outline" onClick={onClose}>Cancel</Button>
      </div>
    </div>
  )
}

function TestPanel({ agent, onClose }: { agent: Agent; onClose: () => void }) {
  const [prompt, setPrompt] = useState('')
  const [result, setResult] = useState('')
  const testAgent = useTestAgent()

  const handleTest = async () => {
    const res = await testAgent.mutateAsync({ id: agent.id, prompt })
    setResult(res.output || 'No output')
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500">Test agent with a prompt (memory disabled for tests)</p>
      <Textarea value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Enter your test prompt..." className="h-24" />
      <Button onClick={handleTest} disabled={!prompt || testAgent.isPending} className="w-full">
        {testAgent.isPending ? <><Loader2 className="h-4 w-4 animate-spin mr-2" />Running...</> : <><Send className="h-4 w-4 mr-2" />Run Test</>}
      </Button>
      {result && (
        <div className="bg-gray-50 rounded-lg p-4 text-sm whitespace-pre-wrap max-h-60 overflow-y-auto border">
          {result}
        </div>
      )}
    </div>
  )
}

export function AgentsPage() {
  const { data: agents = [], isLoading } = useAgents()
  const createAgent = useCreateAgent()
  const updateAgent = useUpdateAgent()
  const deleteAgent = useDeleteAgent()

  const [showCreate, setShowCreate] = useState(false)
  const [editAgent, setEditAgent] = useState<Agent | null>(null)
  const [testAgent, setTestAgent] = useState<Agent | null>(null)
  const [formError, setFormError] = useState('')

  const handleCreate = async (data: Partial<Agent>) => {
    setFormError('')
    try {
      await createAgent.mutateAsync(data)
      setShowCreate(false)
    } catch (e: unknown) {
      setFormError(e instanceof Error ? e.message : 'Failed to create agent')
    }
  }

  const handleUpdate = async (data: Partial<Agent>) => {
    if (!editAgent) return
    setFormError('')
    try {
      await updateAgent.mutateAsync({ id: editAgent.id, ...data })
      setEditAgent(null)
    } catch (e: unknown) {
      setFormError(e instanceof Error ? e.message : 'Failed to update agent')
    }
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Agents</h1>
          <p className="text-gray-500 mt-1">Create and configure your AI agents</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" /> New Agent
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-gray-400" /></div>
      ) : agents.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-medium">No agents yet</h3>
          <p className="text-sm mt-1">Create your first agent or use a template</p>
          <Button onClick={() => setShowCreate(true)} className="mt-4">Create Agent</Button>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-6">
          {agents.map(agent => (
            <Card key={agent.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full flex items-center justify-center text-white font-bold text-lg" style={{ backgroundColor: agent.avatar_color }}>
                      {agent.name[0].toUpperCase()}
                    </div>
                    <div>
                      <CardTitle className="text-base">{agent.name}</CardTitle>
                      <p className="text-xs text-gray-500 capitalize">{agent.role}</p>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="icon" onClick={() => setTestAgent(agent)} className="h-8 w-8">
                      <Zap className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => setEditAgent(agent)} className="h-8 w-8">
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => deleteAgent.mutate(agent.id)} className="h-8 w-8 text-red-500 hover:text-red-700">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-500 mb-3 line-clamp-2">{agent.description || agent.system_prompt.slice(0, 80) + '...'}</p>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary" className="text-xs">{agent.model}</Badge>
                  {agent.memory_enabled && <Badge variant="outline" className="text-xs gap-1"><Brain className="h-3 w-3" />Memory</Badge>}
                  {agent.tools.length > 0 && <Badge variant="outline" className="text-xs gap-1"><Wrench className="h-3 w-3" />{agent.tools.length} tools</Badge>}
                  {agent.telegram_enabled && <Badge variant="outline" className="text-xs">Telegram</Badge>}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={showCreate} onOpenChange={v => { setShowCreate(v); setFormError('') }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader><DialogTitle>Create New Agent</DialogTitle></DialogHeader>
          {formError && <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-2 text-sm">{formError}</div>}
          <AgentForm onSave={handleCreate} onClose={() => { setShowCreate(false); setFormError('') }} />
        </DialogContent>
      </Dialog>

      <Dialog open={!!editAgent} onOpenChange={v => { if (!v) { setEditAgent(null); setFormError('') } }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader><DialogTitle>Edit Agent</DialogTitle></DialogHeader>
          {formError && <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-2 text-sm">{formError}</div>}
          {editAgent && <AgentForm agent={editAgent} onSave={handleUpdate} onClose={() => { setEditAgent(null); setFormError('') }} />}
        </DialogContent>
      </Dialog>

      <Dialog open={!!testAgent} onOpenChange={() => setTestAgent(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Test: {testAgent?.name}</DialogTitle></DialogHeader>
          {testAgent && <TestPanel agent={testAgent} onClose={() => setTestAgent(null)} />}
        </DialogContent>
      </Dialog>
    </div>
  )
}
