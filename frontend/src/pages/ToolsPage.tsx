import { useState } from 'react'
import { useCustomTools, useCreateCustomTool, useUpdateCustomTool, useDeleteCustomTool } from '@/api/custom_tools'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Wrench, Plus, Edit, Trash2, Loader2, Globe, CheckCircle, XCircle, AlertCircle, X } from 'lucide-react'
import type { CustomTool } from '@/api/types'

const METHODS = ['POST', 'GET', 'PUT', 'DELETE', 'PATCH']

const METHOD_COLORS: Record<string, string> = {
  GET: 'bg-green-100 text-green-700',
  POST: 'bg-blue-100 text-blue-700',
  PUT: 'bg-yellow-100 text-yellow-700',
  DELETE: 'bg-red-100 text-red-700',
  PATCH: 'bg-purple-100 text-purple-700',
}

interface FormState {
  name: string
  display_name: string
  description: string
  url: string
  method: string
  headers_raw: string
  body_template: string
  is_active: boolean
}

const EMPTY_FORM: FormState = {
  name: '',
  display_name: '',
  description: '',
  url: '',
  method: 'POST',
  headers_raw: '{}',
  body_template: '',
  is_active: true,
}

function slugify(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 64)
}

function ToolForm({
  initial,
  editId,
  onClose,
}: {
  initial?: FormState
  editId?: string
  onClose: () => void
}) {
  const create = useCreateCustomTool()
  const update = useUpdateCustomTool()
  const [form, setForm] = useState<FormState>(initial || EMPTY_FORM)
  const [error, setError] = useState('')

  const set = (key: keyof FormState, value: string | boolean) =>
    setForm(f => ({ ...f, [key]: value }))

  const handleNameBlur = () => {
    if (!form.name && form.display_name) {
      set('name', slugify(form.display_name))
    }
  }

  const handleSubmit = async () => {
    setError('')
    if (!form.display_name.trim() || !form.name.trim() || !form.url.trim() || !form.description.trim()) {
      setError('Name, identifier, description, and URL are required.')
      return
    }
    let headers: Record<string, string> = {}
    try {
      headers = JSON.parse(form.headers_raw || '{}')
    } catch {
      setError('Headers must be valid JSON (e.g. {"Authorization": "Bearer token"})')
      return
    }
    const payload = {
      name: form.name,
      display_name: form.display_name,
      description: form.description,
      url: form.url,
      method: form.method,
      headers,
      body_template: form.body_template,
      is_active: form.is_active,
    }
    try {
      if (editId) {
        await update.mutateAsync({ id: editId, ...payload })
      } else {
        await create.mutateAsync(payload)
      }
      onClose()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to save tool')
    }
  }

  const isPending = create.isPending || update.isPending

  return (
    <div className="space-y-4 max-h-[78vh] overflow-y-auto px-1">
      {error && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <Label>Display Name <span className="text-red-500">*</span></Label>
          <Input
            value={form.display_name}
            onChange={e => set('display_name', e.target.value)}
            onBlur={handleNameBlur}
            placeholder="Weather Lookup"
          />
          <p className="text-xs text-gray-400 mt-1">Human-readable label</p>
        </div>
        <div>
          <Label>Tool Identifier <span className="text-red-500">*</span></Label>
          <Input
            value={form.name}
            onChange={e => set('name', slugify(e.target.value))}
            placeholder="weather_lookup"
            className="font-mono text-sm"
            disabled={!!editId}
          />
          <p className="text-xs text-gray-400 mt-1">Used by agents (lowercase, underscores)</p>
        </div>
      </div>

      <div>
        <Label>Description <span className="text-red-500">*</span></Label>
        <Textarea
          value={form.description}
          onChange={e => set('description', e.target.value)}
          placeholder="Look up current weather for a given city name. Returns temperature, conditions, and forecast."
          className="h-20 resize-none"
        />
        <p className="text-xs text-gray-400 mt-1">The LLM reads this to decide when to use the tool — be specific about inputs and outputs.</p>
      </div>

      <div className="grid grid-cols-[1fr_120px] gap-3">
        <div>
          <Label>Webhook URL <span className="text-red-500">*</span></Label>
          <Input
            value={form.url}
            onChange={e => set('url', e.target.value)}
            placeholder="https://api.example.com/weather"
            className="font-mono text-sm"
          />
        </div>
        <div>
          <Label>Method</Label>
          <Select value={form.method} onValueChange={v => set('method', v)}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {METHODS.map(m => <SelectItem key={m} value={m}>{m}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <Label>Headers (JSON)</Label>
        <Textarea
          value={form.headers_raw}
          onChange={e => set('headers_raw', e.target.value)}
          placeholder={'{"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"}'}
          className="h-20 font-mono text-xs resize-none"
        />
      </div>

      <div>
        <Label>Body Template</Label>
        <Textarea
          value={form.body_template}
          onChange={e => set('body_template', e.target.value)}
          placeholder={'{"query": "{{input}}"}'}
          className="h-20 font-mono text-xs resize-none"
        />
        <p className="text-xs text-gray-400 mt-1">
          Use <code className="bg-gray-100 px-1 rounded">{'{{input}}'}</code> where the agent's argument should be inserted.
          Leave blank to send the raw input as the body.
        </p>
      </div>

      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input
          type="checkbox"
          checked={form.is_active}
          onChange={e => set('is_active', e.target.checked)}
          className="rounded"
        />
        Active (agents can use this tool)
      </label>

      <div className="flex gap-3 pt-2">
        <Button onClick={handleSubmit} disabled={isPending} className="flex-1">
          {isPending && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
          {editId ? 'Update Tool' : 'Create Tool'}
        </Button>
        <Button variant="outline" onClick={onClose}>Cancel</Button>
      </div>
    </div>
  )
}

export function ToolsPage() {
  const { data: tools = [], isLoading } = useCustomTools()
  const deleteTool = useDeleteCustomTool()
  const [showCreate, setShowCreate] = useState(false)
  const [editTool, setEditTool] = useState<CustomTool | null>(null)

  const handleDelete = async (tool: CustomTool) => {
    if (!confirm(`Delete tool "${tool.display_name}"? Agents currently using it will fail if called.`)) return
    await deleteTool.mutateAsync(tool.id)
  }

  return (
    <div className="p-4 md:p-6 lg:p-8">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-6 md:mb-8">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Custom Tools</h1>
          <p className="text-gray-500 mt-1 text-sm md:text-base">
            Define HTTP webhook tools that your agents can call during execution
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)} className="shrink-0">
          <Plus className="h-4 w-4 mr-2" /> New Tool
        </Button>
      </div>

      {/* How it works banner */}
      <div className="mb-6 p-4 bg-blue-50 border border-blue-100 rounded-xl text-sm text-blue-800 flex gap-3">
        <Globe className="h-5 w-5 shrink-0 text-blue-500 mt-0.5" />
        <div>
          <p className="font-semibold mb-1">How custom tools work</p>
          <p className="text-blue-700">
            Each tool makes an HTTP request to your webhook URL when called by an agent.
            Use <code className="bg-blue-100 px-1 rounded font-mono">{'{{input}}'}</code> in the body template to inject the agent's argument.
            After creating a tool, assign it to agents by name on the Agents page.
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-gray-400" /></div>
      ) : tools.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <Wrench className="h-12 w-12 mx-auto mb-4 opacity-30" />
          <h3 className="text-lg font-medium text-gray-600">No custom tools yet</h3>
          <p className="text-sm mt-1">Create a webhook tool to extend what your agents can do</p>
          <Button onClick={() => setShowCreate(true)} className="mt-4">Create First Tool</Button>
        </div>
      ) : (
        <div className="space-y-3">
          {tools.map(tool => (
            <div key={tool.id} className="flex items-start gap-4 p-4 bg-white border rounded-xl hover:shadow-sm transition-shadow">
              <div className="p-2.5 bg-gray-100 rounded-lg shrink-0">
                <Wrench className="h-5 w-5 text-gray-600" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <span className="font-semibold text-gray-900">{tool.display_name}</span>
                  <code className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-mono">{tool.name}</code>
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${METHOD_COLORS[tool.method] || 'bg-gray-100 text-gray-700'}`}>
                    {tool.method}
                  </span>
                  {tool.is_active ? (
                    <span className="flex items-center gap-1 text-xs text-green-700 bg-green-50 px-2 py-0.5 rounded">
                      <CheckCircle className="h-3 w-3" /> Active
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                      <XCircle className="h-3 w-3" /> Inactive
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mb-1.5 line-clamp-2">{tool.description}</p>
                <code className="text-xs text-gray-400 font-mono truncate block">{tool.url}</code>
              </div>

              <div className="flex shrink-0 gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setEditTool(tool)}
                  title="Edit"
                >
                  <Edit className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-red-500 hover:text-red-700"
                  onClick={() => handleDelete(tool)}
                  disabled={deleteTool.isPending}
                  title="Delete"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={showCreate} onOpenChange={v => { if (!v) setShowCreate(false) }}>
        <DialogContent className="w-[95vw] max-w-2xl">
          <DialogHeader><DialogTitle>New Custom Tool</DialogTitle></DialogHeader>
          <ToolForm onClose={() => setShowCreate(false)} />
        </DialogContent>
      </Dialog>

      <Dialog open={!!editTool} onOpenChange={v => { if (!v) setEditTool(null) }}>
        <DialogContent className="w-[95vw] max-w-2xl">
          <DialogHeader><DialogTitle>Edit Tool — {editTool?.display_name}</DialogTitle></DialogHeader>
          {editTool && (
            <ToolForm
              editId={editTool.id}
              initial={{
                name: editTool.name,
                display_name: editTool.display_name,
                description: editTool.description,
                url: editTool.url,
                method: editTool.method,
                headers_raw: JSON.stringify(editTool.headers || {}, null, 2),
                body_template: editTool.body_template,
                is_active: editTool.is_active,
              }}
              onClose={() => setEditTool(null)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
