import { useState } from 'react'
import { useTemplates, useInstantiateTemplate, useCreateTemplate, useDeleteTemplate } from '@/api/templates'
import { useWorkflows } from '@/api/workflows'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import {
  Loader2, Search, Headphones, ChevronRight, Zap, Bot, Brain, Settings, Plus, Trash2,
  Info, ArrowRight, Workflow, LayoutTemplate, BarChart2, Pen, UserCheck, CheckCircle, X,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { Template } from '@/api/types'

// ── Icon map ──────────────────────────────────────────────────────────────────
const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  search: Search,
  headphones: Headphones,
  zap: Zap,
  bot: Bot,
  brain: Brain,
  settings: Settings,
  pen: Pen,
  'bar-chart': BarChart2,
  'user-check': UserCheck,
}

const ICON_OPTIONS = [
  { value: 'zap', label: 'Zap' },
  { value: 'bot', label: 'Bot' },
  { value: 'brain', label: 'Brain' },
  { value: 'search', label: 'Search' },
  { value: 'headphones', label: 'Headphones' },
  { value: 'pen', label: 'Pen' },
  { value: 'bar-chart', label: 'Bar Chart' },
  { value: 'user-check', label: 'User Check' },
  { value: 'settings', label: 'Settings' },
]

const CATEGORY_OPTIONS = [
  { value: 'productivity', label: 'Productivity' },
  { value: 'support', label: 'Support' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'analytics', label: 'Analytics' },
  { value: 'automation', label: 'Automation' },
  { value: 'research', label: 'Research' },
  { value: 'other', label: 'Other' },
]

const CATEGORY_STYLES: Record<string, { badge: string; gradient: string }> = {
  productivity: { badge: 'bg-blue-100 text-blue-700', gradient: 'from-blue-500 to-blue-700' },
  support:      { badge: 'bg-green-100 text-green-700', gradient: 'from-green-500 to-emerald-600' },
  marketing:    { badge: 'bg-pink-100 text-pink-700', gradient: 'from-pink-500 to-rose-600' },
  analytics:    { badge: 'bg-purple-100 text-purple-700', gradient: 'from-purple-500 to-violet-700' },
  automation:   { badge: 'bg-orange-100 text-orange-700', gradient: 'from-orange-500 to-amber-600' },
  research:     { badge: 'bg-cyan-100 text-cyan-700', gradient: 'from-cyan-500 to-teal-600' },
  other:        { badge: 'bg-gray-100 text-gray-700', gradient: 'from-gray-500 to-gray-700' },
}

const DIFFICULTY_STYLES: Record<string, string> = {
  beginner:     'bg-green-50 text-green-700 border border-green-200',
  intermediate: 'bg-yellow-50 text-yellow-700 border border-yellow-200',
  advanced:     'bg-red-50 text-red-700 border border-red-200',
}

const ALL_CATEGORIES = ['all', 'productivity', 'support', 'marketing', 'analytics', 'automation', 'research', 'other']
const CAT_LABELS: Record<string, string> = {
  all: 'All', productivity: 'Productivity', support: 'Support',
  marketing: 'Marketing', analytics: 'Analytics', automation: 'Automation',
  research: 'Research', other: 'Other',
}

interface CreateForm {
  workflow_id: string; name: string; description: string; category: string; icon: string
}
const DEFAULT_FORM: CreateForm = { workflow_id: '', name: '', description: '', category: 'productivity', icon: 'zap' }

// ── Detail Modal ──────────────────────────────────────────────────────────────
function TemplateDetailModal({
  template,
  onClose,
  onUse,
  isPending,
}: {
  template: Template
  onClose: () => void
  onUse: () => void
  isPending: boolean
}) {
  const Icon = ICONS[template.icon] || Zap
  const styles = CATEGORY_STYLES[template.category] || CATEGORY_STYLES.other

  return (
    <div className="space-y-5">
      <div className="flex items-start gap-4">
        <div className={`p-3 bg-gradient-to-br ${styles.gradient} rounded-xl shrink-0`}>
          <Icon className="h-7 w-7 text-white" />
        </div>
        <div className="min-w-0">
          <h2 className="text-xl font-bold text-gray-900">{template.name}</h2>
          <div className="flex flex-wrap gap-2 mt-2">
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles.badge}`}>{template.category}</span>
            {template.difficulty && (
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${DIFFICULTY_STYLES[template.difficulty]}`}>
                {template.difficulty}
              </span>
            )}
            {template.is_custom && (
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700">custom</span>
            )}
          </div>
        </div>
      </div>

      <p className="text-sm text-gray-600 leading-relaxed">{template.description}</p>

      {/* Agent pipeline */}
      {template.agents_preview && template.agents_preview.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Agent Pipeline</p>
          <div className="flex flex-wrap items-center gap-1.5">
            {template.agents_preview.map((agent, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-white"
                  style={{ backgroundColor: agent.color }}>
                  {agent.role === 'approval' ? '✋' : '🤖'} {agent.name}
                </div>
                {i < template.agents_preview!.length - 1 && (
                  <ChevronRight className="h-3.5 w-3.5 text-gray-300 shrink-0" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Use cases */}
      {template.use_cases && template.use_cases.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Use Cases</p>
          <ul className="space-y-1">
            {template.use_cases.map((uc, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                <CheckCircle className="h-3.5 w-3.5 text-green-500 shrink-0 mt-0.5" />
                {uc}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Tags */}
      {template.tags && template.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {template.tags.map(tag => (
            <span key={tag} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">#{tag}</span>
          ))}
        </div>
      )}

      <div className="flex gap-3 pt-2">
        <Button onClick={onUse} disabled={isPending} className="flex-1">
          {isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
          Use This Template
        </Button>
        <Button variant="outline" onClick={onClose}>Close</Button>
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export function TemplatesPage() {
  const { data: templates = [], isLoading } = useTemplates()
  const { data: workflows = [] } = useWorkflows()
  const instantiate = useInstantiateTemplate()
  const createTemplate = useCreateTemplate()
  const deleteTemplate = useDeleteTemplate()
  const navigate = useNavigate()

  const [search, setSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState('all')
  const [detailTemplate, setDetailTemplate] = useState<Template | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [form, setForm] = useState<CreateForm>(DEFAULT_FORM)

  const handleInstantiate = async (slug: string) => {
    const result = await instantiate.mutateAsync(slug) as { workflow_id?: string }
    setDetailTemplate(null)
    if (result?.workflow_id) {
      navigate('/workflows', { state: { selectedWorkflowId: result.workflow_id } })
    } else {
      navigate('/workflows')
    }
  }

  const handleCreate = async () => {
    if (!form.workflow_id || !form.name.trim()) return
    await createTemplate.mutateAsync(form)
    setCreateOpen(false)
    setForm(DEFAULT_FORM)
  }

  const handleDelete = async (slug: string, name: string) => {
    if (!confirm(`Delete template "${name}"?`)) return
    await deleteTemplate.mutateAsync(slug)
  }

  // Filter
  const filtered = templates.filter((t: Template) => {
    const matchesCategory = activeCategory === 'all' || t.category === activeCategory
    const q = search.toLowerCase()
    const matchesSearch = !q || t.name.toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q) ||
      (t.tags || []).some(tag => tag.includes(q))
    return matchesCategory && matchesSearch
  })

  // Which categories actually exist in the data
  const existingCats = new Set(templates.map((t: Template) => t.category))
  const visibleCats = ALL_CATEGORIES.filter(c => c === 'all' || existingCats.has(c))

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Templates</h1>
          <p className="text-gray-500 mt-1 text-sm md:text-base">Pre-built workflow blueprints — pick one and spin up a workflow in seconds</p>
        </div>
        <Button onClick={() => setCreateOpen(true)} variant="outline" className="shrink-0">
          <Plus className="h-4 w-4 mr-2" /> Save Workflow as Template
        </Button>
      </div>

      {/* Search + category filter */}
      <div className="mb-6 space-y-3">
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
          <Input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search templates…"
            className="pl-9"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {visibleCats.map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                activeCategory === cat
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {CAT_LABELS[cat]}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-gray-400" /></div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <Zap className="h-12 w-12 mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium">No templates found</p>
          {search && <p className="text-sm mt-1">Try a different search term or clear the filter</p>}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 md:gap-5">
          {filtered.map((template: Template) => {
            const Icon = ICONS[template.icon] || Zap
            const styles = CATEGORY_STYLES[template.category] || CATEGORY_STYLES.other
            return (
              <div
                key={template.slug}
                className="group bg-white border border-gray-200 rounded-2xl overflow-hidden hover:shadow-lg hover:border-gray-300 transition-all cursor-pointer"
                onClick={() => setDetailTemplate(template)}
              >
                {/* Card header gradient */}
                <div className={`bg-gradient-to-br ${styles.gradient} px-5 py-4`}>
                  <div className="flex items-start justify-between">
                    <div className="p-2 bg-white/20 rounded-lg">
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    <div className="flex gap-1.5 items-center">
                      {template.difficulty && (
                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-white/20 text-white capitalize">
                          {template.difficulty}
                        </span>
                      )}
                      {template.is_custom && (
                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-white/20 text-white">custom</span>
                      )}
                    </div>
                  </div>
                  <h3 className="mt-3 font-bold text-white text-base leading-snug">{template.name}</h3>
                  <span className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-medium bg-white/20 text-white`}>
                    {template.category}
                  </span>
                </div>

                {/* Card body */}
                <div className="px-5 py-4 space-y-3">
                  <p className="text-sm text-gray-600 line-clamp-2 leading-relaxed">{template.description}</p>

                  {/* Agent pipeline chips */}
                  {template.agents_preview && template.agents_preview.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1">
                      {template.agents_preview.map((agent, i) => (
                        <div key={i} className="flex items-center gap-1">
                          <span
                            className="px-2 py-0.5 rounded-full text-xs font-medium text-white"
                            style={{ backgroundColor: agent.color }}
                          >
                            {agent.name}
                          </span>
                          {i < template.agents_preview!.length - 1 && (
                            <ChevronRight className="h-3 w-3 text-gray-300 shrink-0" />
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Use cases (first 2) */}
                  {template.use_cases && template.use_cases.length > 0 && (
                    <div className="space-y-0.5">
                      {template.use_cases.slice(0, 2).map((uc, i) => (
                        <p key={i} className="text-xs text-gray-500 flex items-start gap-1">
                          <span className="text-green-500 shrink-0">✓</span> {uc}
                        </p>
                      ))}
                    </div>
                  )}

                  {/* Footer */}
                  <div className="flex items-center justify-between pt-1 border-t border-gray-100">
                    <span className="text-xs text-gray-400">{template.agent_count} agent{template.agent_count !== 1 ? 's' : ''}</span>
                    <div className="flex items-center gap-1">
                      {template.is_custom && (
                        <button
                          onClick={e => { e.stopPropagation(); handleDelete(template.slug, template.name) }}
                          disabled={deleteTemplate.isPending}
                          className="p-1 rounded hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                      <button
                        onClick={e => { e.stopPropagation(); handleInstantiate(template.slug) }}
                        disabled={instantiate.isPending}
                        className="flex items-center gap-1 px-3 py-1 rounded-lg bg-gray-900 text-white text-xs font-medium hover:bg-gray-700 transition-colors disabled:opacity-50"
                      >
                        {instantiate.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
                        Use <ChevronRight className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Template detail modal */}
      <Dialog open={!!detailTemplate} onOpenChange={v => { if (!v) setDetailTemplate(null) }}>
        <DialogContent className="w-[95vw] max-w-lg">
          <DialogHeader>
            <DialogTitle className="sr-only">Template Details</DialogTitle>
          </DialogHeader>
          {detailTemplate && (
            <TemplateDetailModal
              template={detailTemplate}
              onClose={() => setDetailTemplate(null)}
              onUse={() => handleInstantiate(detailTemplate.slug)}
              isPending={instantiate.isPending}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Create template from workflow dialog */}
      <Dialog open={createOpen} onOpenChange={v => { setCreateOpen(v); if (!v) setForm(DEFAULT_FORM) }}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Save Workflow as Template</DialogTitle></DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label>Source Workflow <span className="text-red-500">*</span></Label>
              <Select value={form.workflow_id} onValueChange={v => setForm(f => ({ ...f, workflow_id: v }))}>
                <SelectTrigger><SelectValue placeholder="Pick a workflow…" /></SelectTrigger>
                <SelectContent>
                  {workflows.map((w: any) => <SelectItem key={w.id} value={w.id}>{w.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Template Name <span className="text-red-500">*</span></Label>
              <Input placeholder="Marketing Research Pipeline" value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
            </div>
            <div className="space-y-1.5">
              <Label>Description</Label>
              <textarea
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                placeholder="Describe what this template does…" rows={3}
                value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Category</Label>
                <Select value={form.category} onValueChange={v => setForm(f => ({ ...f, category: v }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {CATEGORY_OPTIONS.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Icon</Label>
                <Select value={form.icon} onValueChange={v => setForm(f => ({ ...f, icon: v }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {ICON_OPTIONS.map(o => {
                      const Ic = ICONS[o.value] || Zap
                      return (
                        <SelectItem key={o.value} value={o.value}>
                          <span className="flex items-center gap-2"><Ic className="h-4 w-4" />{o.label}</span>
                        </SelectItem>
                      )
                    })}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={createTemplate.isPending || !form.workflow_id || !form.name.trim()}>
              {createTemplate.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
              Save Template
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
