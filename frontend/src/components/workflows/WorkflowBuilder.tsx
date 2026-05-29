import { useState, useCallback, useEffect } from 'react'
import ReactFlow, {
  Node, Edge, addEdge, Connection, useNodesState, useEdgesState,
  Background, Controls, MiniMap, BackgroundVariant, MarkerType, EdgeProps,
  getBezierPath, EdgeLabelRenderer, BaseEdge,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { AgentNode } from './AgentNode'
import { useAgents } from '@/api/agents'
import { useSaveWorkflowGraph, useTriggerWorkflow } from '@/api/workflows'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Save, Play, Loader2, Plus, GitMerge, UserCheck, GitFork, Trash2 } from 'lucide-react'
import type { Workflow, Agent } from '@/api/types'
import { useExecutionStore } from '@/stores/executionStore'
import { useNavigate } from 'react-router-dom'

// ─── Clickable edge with condition label ────────────────────────────────────
function ConditionEdge({
  id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition,
  data, markerEnd, style,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition })
  const condition = data?.condition as string | undefined

  return (
    <>
      <BaseEdge path={edgePath} markerEnd={markerEnd} style={style} />
      <EdgeLabelRenderer>
        <div
          style={{ position: 'absolute', transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`, pointerEvents: 'all' }}
          className="nodrag nopan flex items-center gap-1"
        >
          <button
            onClick={() => data?.onEditCondition?.(id)}
            className={`px-2 py-0.5 rounded text-xs font-medium border shadow-sm transition-colors ${
              condition
                ? 'bg-indigo-100 text-indigo-700 border-indigo-300 hover:bg-indigo-200'
                : 'bg-white text-gray-400 border-gray-200 hover:border-indigo-300 hover:text-indigo-500'
            }`}
            title="Click to set routing condition"
          >
            {condition || '+ condition'}
          </button>
          <button
            onClick={() => data?.onDeleteEdge?.(id)}
            className="h-4 w-4 rounded-full bg-red-100 text-red-400 hover:bg-red-500 hover:text-white flex items-center justify-center transition-colors opacity-0 group-hover:opacity-100"
            title="Delete edge"
          >
            <Trash2 className="h-2.5 w-2.5" />
          </button>
        </div>
      </EdgeLabelRenderer>
    </>
  )
}

const nodeTypes = { agentNode: AgentNode }
const edgeTypes = { conditionEdge: ConditionEdge }

function workflowToFlow(workflow: Workflow, agents: Agent[], callbacks: { onEditCondition: (id: string) => void; onDeleteEdge: (id: string) => void }) {
  const agentMap = Object.fromEntries(agents.map(a => [a.id, a]))

  const nodes: Node[] = workflow.nodes.map(n => ({
    id: n.id,
    type: 'agentNode',
    position: { x: n.position_x, y: n.position_y },
    data: {
      label: n.label || agentMap[n.agent_id || '']?.name || n.node_type,
      nodeType: n.node_type,
      agent: n.agent_id ? agentMap[n.agent_id] : undefined,
      agent_id: n.agent_id,
      node_type: n.node_type,
      approvalDescription: (n.config as any)?.description,
      approvalTimeout: (n.config as any)?.timeout_seconds,
    },
  }))

  const edges: Edge[] = workflow.edges.map(e => ({
    id: e.id,
    source: e.source_node_id,
    target: e.target_node_id,
    type: 'conditionEdge',
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { stroke: '#6366f1', strokeWidth: 2 },
    data: { condition: e.condition, original_id: e.id, ...callbacks },
  }))

  return { nodes, edges }
}

interface WorkflowBuilderProps {
  workflow: Workflow
}

export function WorkflowBuilder({ workflow }: WorkflowBuilderProps) {
  const { data: agents = [] } = useAgents()
  const saveGraph = useSaveWorkflowGraph()
  const triggerWorkflow = useTriggerWorkflow()
  const { startStream } = useExecutionStore()
  const navigate = useNavigate()

  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [isDirty, setIsDirty] = useState(false)
  const [showRunDialog, setShowRunDialog] = useState(false)
  const [showAgentPicker, setShowAgentPicker] = useState(false)
  const [runPrompt, setRunPrompt] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState('')

  // Edge condition editor
  const [editingEdgeId, setEditingEdgeId] = useState<string | null>(null)
  const [conditionDraft, setConditionDraft] = useState('')

  // Approval node dialog
  const [showApprovalDialog, setShowApprovalDialog] = useState(false)
  const [approvalForm, setApprovalForm] = useState({ label: 'Human Approval', description: '', timeout_seconds: 3600 })

  const handleEditCondition = useCallback((edgeId: string) => {
    setEditingEdgeId(edgeId)
    const edge = edges.find(e => e.id === edgeId)
    setConditionDraft((edge?.data as any)?.condition || '')
  }, [edges])

  const handleDeleteEdge = useCallback((edgeId: string) => {
    setEdges(eds => eds.filter(e => e.id !== edgeId))
    setIsDirty(true)
  }, [setEdges])

  const handleSaveCondition = useCallback(() => {
    if (!editingEdgeId) return
    setEdges(eds => eds.map(e =>
      e.id === editingEdgeId
        ? { ...e, data: { ...e.data, condition: conditionDraft || null } }
        : e
    ))
    setIsDirty(true)
    setEditingEdgeId(null)
  }, [editingEdgeId, conditionDraft, setEdges])

  useEffect(() => {
    const { nodes: n, edges: e } = workflowToFlow(workflow, agents, { onEditCondition: handleEditCondition, onDeleteEdge: handleDeleteEdge })
    setNodes(n)
    setEdges(e)
    setIsDirty(false)
  }, [workflow.id, agents.length])

  // Keep callbacks fresh in edge/node data
  useEffect(() => {
    setEdges(eds => eds.map(e => ({
      ...e,
      data: { ...e.data, onEditCondition: handleEditCondition, onDeleteEdge: handleDeleteEdge },
    })))
  }, [handleEditCondition, handleDeleteEdge])

  const onConnect = useCallback((connection: Connection) => {
    setEdges(eds => addEdge({
      ...connection,
      type: 'conditionEdge',
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: '#6366f1', strokeWidth: 2 },
      data: { condition: null, onEditCondition: handleEditCondition, onDeleteEdge: handleDeleteEdge },
    }, eds))
    setIsDirty(true)
  }, [setEdges, handleEditCondition, handleDeleteEdge])

  const addAgentNode = (agent: Agent) => {
    const id = `node_${Date.now()}`
    setNodes(ns => [...ns, {
      id,
      type: 'agentNode',
      position: { x: Math.random() * 400 + 200, y: Math.random() * 200 + 150 },
      data: { label: agent.name, nodeType: 'agent', agent, agent_id: agent.id, node_type: 'agent' },
    }])
    setIsDirty(true)
    setShowAgentPicker(false)
  }

  const addApprovalNode = () => {
    const id = `node_${Date.now()}`
    setNodes(ns => [...ns, {
      id,
      type: 'agentNode',
      position: { x: Math.random() * 300 + 300, y: Math.random() * 200 + 200 },
      data: {
        label: approvalForm.label,
        nodeType: 'approval',
        node_type: 'approval',
        agent_id: null,
        approvalDescription: approvalForm.description,
        approvalTimeout: approvalForm.timeout_seconds,
      },
    }])
    setIsDirty(true)
    setShowApprovalDialog(false)
    setApprovalForm({ label: 'Human Approval', description: '', timeout_seconds: 3600 })
  }

  const addRouterNode = () => {
    const id = `node_${Date.now()}`
    setNodes(ns => [...ns, {
      id,
      type: 'agentNode',
      position: { x: Math.random() * 300 + 300, y: Math.random() * 200 + 200 },
      data: { label: 'Router', nodeType: 'router', node_type: 'router', agent_id: null },
    }])
    setIsDirty(true)
  }

  const handleSave = async () => {
    setIsSaving(true)
    setSaveError('')
    try {
      const nodeData = nodes.map(n => ({
        id: n.id,
        agent_id: n.data.agent_id || null,
        node_type: n.data.node_type || n.data.nodeType || 'agent',
        label: n.data.label,
        position_x: n.position.x,
        position_y: n.position.y,
        config: n.data.nodeType === 'approval'
          ? { description: n.data.approvalDescription || '', timeout_seconds: n.data.approvalTimeout || 3600 }
          : {},
      }))

      const edgeData = edges.map(e => ({
        source_node_id: e.source,
        target_node_id: e.target,
        condition: (e.data as any)?.condition || null,
        label: typeof e.label === 'string' ? e.label : '',
      }))

      await saveGraph.mutateAsync({ id: workflow.id, nodes: nodeData, edges: edgeData })
      setIsDirty(false)
    } catch (e: unknown) {
      setSaveError(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setIsSaving(false)
    }
  }

  const handleRun = async () => {
    if (!runPrompt.trim()) return
    const result = await triggerWorkflow.mutateAsync({ id: workflow.id, prompt: runPrompt })
    setShowRunDialog(false)
    setRunPrompt('')
    startStream(result.id)
    navigate(`/executions/${result.id}`)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-white">
        <div className="flex items-center gap-2 flex-wrap">
          <Button variant="outline" size="sm" onClick={() => setShowAgentPicker(true)}>
            <Plus className="h-4 w-4 mr-1" /> Add Agent
          </Button>
          <Button variant="outline" size="sm" onClick={() => setShowApprovalDialog(true)}
            className="border-amber-300 text-amber-700 hover:bg-amber-50">
            <UserCheck className="h-4 w-4 mr-1" /> Add Approval
          </Button>
          <Button variant="outline" size="sm" onClick={addRouterNode}
            className="border-purple-300 text-purple-700 hover:bg-purple-50">
            <GitFork className="h-4 w-4 mr-1" /> Add Router
          </Button>
          <span className="text-xs text-gray-400 hidden md:inline">Hover node to delete · Click edge label to set condition</span>
          {isDirty && <span className="text-xs text-orange-500 font-medium">• Unsaved changes</span>}
          {saveError && <span className="text-xs text-red-500">{saveError}</span>}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleSave} disabled={isSaving || !isDirty}>
            {isSaving ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Save className="h-4 w-4 mr-1" />}
            Save
          </Button>
          <Button size="sm" onClick={() => setShowRunDialog(true)}>
            <Play className="h-4 w-4 mr-1" /> Run
          </Button>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={changes => { onNodesChange(changes); setIsDirty(true) }}
          onEdgesChange={changes => { onEdgesChange(changes); setIsDirty(true) }}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          deleteKeyCode={['Backspace', 'Delete']}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.3}
          maxZoom={2}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#e5e7eb" />
          <Controls />
          <MiniMap nodeStrokeWidth={3} zoomable pannable className="!bottom-4 !right-4" />
        </ReactFlow>
      </div>

      {/* ── Edge condition editor ── */}
      <Dialog open={!!editingEdgeId} onOpenChange={() => setEditingEdgeId(null)}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <GitMerge className="h-4 w-4" /> Edge Routing Condition
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <p className="text-sm text-gray-500">
              Enter a keyword that the upstream output must contain to follow this edge.
              Leave blank for an unconditional connection.
            </p>
            <div>
              <Label>Condition keyword</Label>
              <Input
                value={conditionDraft}
                onChange={e => setConditionDraft(e.target.value)}
                placeholder='e.g. "billing" or "approved"'
                autoFocus
                onKeyDown={e => e.key === 'Enter' && handleSaveCondition()}
              />
            </div>
            <p className="text-xs text-gray-400">
              The router checks if the upstream output contains this keyword (case-insensitive).
            </p>
            <div className="flex gap-2">
              <Button onClick={handleSaveCondition} className="flex-1">Apply</Button>
              <Button variant="outline" onClick={() => { setConditionDraft(''); handleSaveCondition() }}>Clear</Button>
              <Button variant="outline" onClick={() => setEditingEdgeId(null)}>Cancel</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* ── Approval node config ── */}
      <Dialog open={showApprovalDialog} onOpenChange={setShowApprovalDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <UserCheck className="h-5 w-5 text-amber-500" /> Add Human Approval Step
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-gray-500">
              Pauses the workflow until a human approves or rejects from the Executions monitor.
            </p>
            <div>
              <Label>Node label</Label>
              <Input
                value={approvalForm.label}
                onChange={e => setApprovalForm(f => ({ ...f, label: e.target.value }))}
                placeholder="Manager Review"
              />
            </div>
            <div>
              <Label>Description <span className="text-gray-400 font-normal">(shown to approver)</span></Label>
              <Textarea
                value={approvalForm.description}
                onChange={e => setApprovalForm(f => ({ ...f, description: e.target.value }))}
                placeholder="Please review the agent's output and approve or reject to continue."
                className="h-20"
              />
            </div>
            <div>
              <Label>Timeout (seconds)</Label>
              <Input
                type="number"
                min={60}
                max={86400}
                value={approvalForm.timeout_seconds}
                onChange={e => setApprovalForm(f => ({ ...f, timeout_seconds: parseInt(e.target.value) || 3600 }))}
              />
              <p className="text-xs text-gray-400 mt-1">Workflow auto-fails after this duration if no decision is made.</p>
            </div>
            <div className="flex gap-3">
              <Button onClick={addApprovalNode} className="flex-1 bg-amber-500 hover:bg-amber-600">
                <UserCheck className="h-4 w-4 mr-2" /> Add to Canvas
              </Button>
              <Button variant="outline" onClick={() => setShowApprovalDialog(false)}>Cancel</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* ── Agent picker ── */}
      <Dialog open={showAgentPicker} onOpenChange={setShowAgentPicker}>
        <DialogContent className="max-w-md">
          <DialogHeader><DialogTitle>Add Agent to Workflow</DialogTitle></DialogHeader>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {agents.length === 0 ? (
              <p className="text-center text-gray-400 py-8">No agents yet. Create agents first.</p>
            ) : agents.map(agent => (
              <button key={agent.id} onClick={() => addAgentNode(agent)}
                className="w-full flex items-center gap-3 p-3 rounded-lg border hover:bg-gray-50 transition-colors text-left">
                <div className="h-9 w-9 rounded-full flex items-center justify-center text-white font-bold" style={{ backgroundColor: agent.avatar_color }}>
                  {agent.name[0].toUpperCase()}
                </div>
                <div>
                  <p className="font-medium text-sm">{agent.name}</p>
                  <p className="text-xs text-gray-500">{agent.role} · {agent.model}</p>
                </div>
              </button>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* ── Run dialog ── */}
      <Dialog open={showRunDialog} onOpenChange={setShowRunDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Run Workflow</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-gray-500">Enter the initial prompt/task for this workflow:</p>
            <Textarea value={runPrompt} onChange={e => setRunPrompt(e.target.value)}
              placeholder="e.g. Research the latest trends in AI for 2025..."
              className="h-32" autoFocus />
            <div className="flex gap-3">
              <Button onClick={handleRun} disabled={!runPrompt.trim() || triggerWorkflow.isPending} className="flex-1">
                {triggerWorkflow.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Play className="h-4 w-4 mr-2" />}
                Start Execution
              </Button>
              <Button variant="outline" onClick={() => setShowRunDialog(false)}>Cancel</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
