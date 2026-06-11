export interface Agent {
  id: string
  name: string
  role: string
  description: string
  system_prompt: string
  model: string
  provider: string
  temperature: number
  max_iterations: number
  memory_enabled: boolean
  memory_collection: string | null
  tools: string[]
  telegram_enabled: boolean
  telegram_chat_ids: number[]
  avatar_color: string
  max_output_tokens: number
  guardrail_keywords: string[]
  input_guardrail_keywords: string[]
  max_input_length: number
  response_format: 'text' | 'json'
  created_at: string
  updated_at: string
}

export interface WorkflowNode {
  id: string
  workflow_id: string
  agent_id: string | null
  node_type: 'start' | 'end' | 'agent' | 'condition' | 'approval' | 'router'
  label: string
  position_x: number
  position_y: number
  config: Record<string, unknown>
}

export interface WorkflowEdge {
  id: string
  workflow_id: string
  source_node_id: string
  target_node_id: string
  condition: string | null
  label: string
}

export interface Workflow {
  id: string
  name: string
  description: string
  is_active: boolean
  trigger_type: string
  trigger_config: Record<string, unknown>
  template_slug: string | null
  created_at: string
  updated_at: string
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
}

export interface Execution {
  id: string
  workflow_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'awaiting_approval'
  trigger_type: string
  trigger_payload: Record<string, unknown>
  final_output: string | null
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  celery_task_id: string | null
  total_input_tokens: number
  total_output_tokens: number
  total_cost_usd: number
  created_at: string
}

export interface LogEntry {
  type: 'log' | 'execution_complete' | 'connected'
  execution_id?: string
  agent_id?: string
  agent_name?: string
  node_id?: string
  level?: string
  message?: string
  metadata?: Record<string, unknown>
  timestamp?: string
  status?: string
  output?: string
  error?: string
}

export interface TemplateAgentPreview {
  name: string
  role: string
  color: string
}

export interface Template {
  slug: string
  name: string
  description: string
  icon: string
  category: string
  agent_count: number
  is_custom: boolean
  created_at?: string
  difficulty?: 'beginner' | 'intermediate' | 'advanced'
  tags?: string[]
  use_cases?: string[]
  agents_preview?: TemplateAgentPreview[]
}

export interface AvailableTool {
  name: string
  description: string
  is_custom?: boolean
}

export interface CustomTool {
  id: string
  name: string
  display_name: string
  description: string
  tool_type: 'webhook' | 'code'
  url: string
  method: string
  headers: Record<string, string>
  body_template: string
  code: string
  is_active: boolean
  created_at: string
  updated_at: string
}
