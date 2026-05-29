import { Handle, Position, NodeProps, useReactFlow } from 'reactflow'
import { Bot, Brain, Wrench, X, UserCheck, GitFork, Clock } from 'lucide-react'
import type { Agent } from '@/api/types'

interface AgentNodeData {
  agent?: Agent
  label: string
  nodeType: string
  isActive?: boolean
  isAwaitingApproval?: boolean
  approvalDescription?: string
  approvalTimeout?: number
}

function DeleteButton({ id, nodeType }: { id: string; nodeType: string }) {
  const { deleteElements } = useReactFlow()
  if (nodeType === 'start' || nodeType === 'end') return null
  return (
    <button
      className="absolute -top-2 -right-2 h-5 w-5 rounded-full bg-red-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-sm hover:bg-red-600 z-10"
      onClick={e => { e.stopPropagation(); deleteElements({ nodes: [{ id }] }) }}
      title="Delete node"
    >
      <X className="h-3 w-3" />
    </button>
  )
}

export function AgentNode({ id, data, selected }: NodeProps<AgentNodeData>) {
  if (data.nodeType === 'start') {
    return (
      <div className={`px-4 py-2 rounded-full border-2 bg-green-50 border-green-400 font-semibold text-green-700 text-sm shadow-sm ${selected ? 'ring-2 ring-green-400' : ''}`}>
        <Handle type="source" position={Position.Right} className="!bg-green-400" />
        ▶ Start
      </div>
    )
  }

  if (data.nodeType === 'end') {
    return (
      <div className={`px-4 py-2 rounded-full border-2 bg-gray-100 border-gray-400 font-semibold text-gray-600 text-sm shadow-sm ${selected ? 'ring-2 ring-gray-400' : ''}`}>
        <Handle type="target" position={Position.Left} className="!bg-gray-400" />
        ■ End
      </div>
    )
  }

  if (data.nodeType === 'approval') {
    const isWaiting = data.isAwaitingApproval
    return (
      <div className={`relative group w-52 rounded-xl border-2 bg-amber-50 shadow-md transition-all
        ${selected ? 'ring-2 ring-amber-400 shadow-lg' : ''}
        ${isWaiting ? 'border-amber-500 ring-2 ring-amber-400 animate-pulse' : 'border-amber-300'}`}>
        <DeleteButton id={id} nodeType={data.nodeType} />
        <Handle type="target" position={Position.Left} className="!bg-amber-400 !w-3 !h-3" />
        <div className="p-3">
          <div className="flex items-center gap-2 mb-1">
            <div className={`h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0
              ${isWaiting ? 'bg-amber-500 animate-bounce' : 'bg-amber-400'}`}>
              <UserCheck className="h-4 w-4 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm text-amber-900 truncate">{data.label}</p>
              <p className="text-xs text-amber-600">Human approval required</p>
            </div>
          </div>
          {data.approvalDescription && (
            <p className="text-xs text-amber-700 bg-amber-100 rounded px-2 py-1 mt-1 line-clamp-2">
              {data.approvalDescription}
            </p>
          )}
          {data.approvalTimeout && (
            <div className="flex items-center gap-1 mt-1.5 text-xs text-amber-500">
              <Clock className="h-3 w-3" />
              Timeout: {Math.round(data.approvalTimeout / 60)}m
            </div>
          )}
          {isWaiting && (
            <div className="mt-2 px-2 py-1 bg-amber-200 rounded text-xs text-amber-800 font-medium text-center">
              ⏸ Awaiting approval…
            </div>
          )}
        </div>
        <Handle type="source" position={Position.Right} className="!bg-amber-400 !w-3 !h-3" />
      </div>
    )
  }

  if (data.nodeType === 'router') {
    return (
      <div className={`relative group w-44 rounded-xl border-2 bg-purple-50 shadow-md transition-all
        ${selected ? 'ring-2 ring-purple-400 shadow-lg' : 'border-purple-300'}`}>
        <DeleteButton id={id} nodeType={data.nodeType} />
        <Handle type="target" position={Position.Left} className="!bg-purple-400 !w-3 !h-3" />
        <div className="p-3">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-purple-500 flex items-center justify-center flex-shrink-0">
              <GitFork className="h-4 w-4 text-white" />
            </div>
            <div>
              <p className="font-semibold text-sm text-purple-900 truncate">{data.label}</p>
              <p className="text-xs text-purple-500">Condition router</p>
            </div>
          </div>
          <p className="text-xs text-purple-400 mt-1.5">Routes by edge conditions →</p>
        </div>
        <Handle type="source" position={Position.Right} className="!bg-purple-400 !w-3 !h-3" id="a" />
        <Handle type="source" position={Position.Bottom} className="!bg-purple-400 !w-3 !h-3" id="b" />
      </div>
    )
  }

  // Default: agent node
  const agent = data.agent
  const color = agent?.avatar_color || '#6366f1'

  return (
    <div className={`relative group w-52 rounded-xl border-2 bg-white shadow-md transition-all
      ${selected ? 'ring-2 ring-blue-400 shadow-lg' : ''}
      ${data.isActive ? 'border-green-400 ring-2 ring-green-300' : 'border-gray-200'}`}>
      <DeleteButton id={id} nodeType={data.nodeType} />
      <Handle type="target" position={Position.Left} className="!bg-gray-400 !w-3 !h-3" />
      <div className="p-3">
        <div className="flex items-center gap-2 mb-2">
          <div className="h-8 w-8 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0" style={{ backgroundColor: color }}>
            {data.label?.[0]?.toUpperCase() || <Bot className="h-4 w-4" />}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-sm text-gray-800 truncate">{data.label}</p>
            {agent && <p className="text-xs text-gray-500 capitalize truncate">{agent.role}</p>}
          </div>
        </div>
        {agent && (
          <div className="flex flex-wrap gap-1 mt-1">
            <span className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">{agent.model.split('-')[0]}</span>
            {agent.memory_enabled && (
              <span className="px-1.5 py-0.5 bg-purple-100 text-purple-600 rounded text-xs flex items-center gap-0.5">
                <Brain className="h-2.5 w-2.5" />mem
              </span>
            )}
            {agent.tools.length > 0 && (
              <span className="px-1.5 py-0.5 bg-blue-100 text-blue-600 rounded text-xs flex items-center gap-0.5">
                <Wrench className="h-2.5 w-2.5" />{agent.tools.length}
              </span>
            )}
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Right} className="!bg-gray-400 !w-3 !h-3" />
    </div>
  )
}
