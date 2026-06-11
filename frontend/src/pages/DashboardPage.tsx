import { useAgents } from '@/api/agents'
import { useWorkflows } from '@/api/workflows'
import { useExecutions } from '@/api/executions'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Bot, GitFork, Play, CheckCircle, XCircle, Clock, Loader2, Zap } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import type { Execution } from '@/api/types'

function StatusBadge({ status }: { status: Execution['status'] }) {
  const config: Record<string, { variant: 'secondary' | 'default' | 'outline' | 'destructive'; icon: React.ElementType; label: string }> = {
    pending: { variant: 'secondary', icon: Clock, label: 'Pending' },
    running: { variant: 'default', icon: Loader2, label: 'Running' },
    completed: { variant: 'outline', icon: CheckCircle, label: 'Completed' },
    failed: { variant: 'destructive', icon: XCircle, label: 'Failed' },
    cancelled: { variant: 'outline', icon: XCircle, label: 'Cancelled' },
    awaiting_approval: { variant: 'outline', icon: Clock, label: 'Awaiting Approval' },
  }
  const { variant, icon: Icon, label } = config[status] ?? config.pending
  return (
    <Badge variant={variant} className="flex items-center gap-1 shrink-0">
      <Icon className={`h-3 w-3 ${status === 'running' ? 'animate-spin' : ''}`} />
      <span className="hidden sm:inline">{label}</span>
    </Badge>
  )
}

export function DashboardPage() {
  const { data: agents = [] } = useAgents()
  const { data: workflows = [] } = useWorkflows()
  const { data: executions = [] } = useExecutions()

  const runningCount = executions.filter(e => e.status === 'running').length
  const completedCount = executions.filter(e => e.status === 'completed').length
  const failedCount = executions.filter(e => e.status === 'failed').length
  const recentExecutions = executions.slice(0, 5)

  return (
    <div className="p-4 md:p-6 lg:p-8">
      <div className="mb-6 md:mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1 text-sm md:text-base">Monitor your AI agents and workflows</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-6 mb-6 md:mb-8">
        <Card>
          <CardContent className="pt-4 md:pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm font-medium text-gray-500">Total Agents</p>
                <p className="text-2xl md:text-3xl font-bold">{agents.length}</p>
              </div>
              <div className="p-2 md:p-3 bg-blue-100 rounded-full">
                <Bot className="h-4 w-4 md:h-6 md:w-6 text-blue-600" />
              </div>
            </div>
            <Link to="/agents" className="text-xs md:text-sm text-blue-600 hover:underline mt-2 block">Manage agents →</Link>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4 md:pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm font-medium text-gray-500">Workflows</p>
                <p className="text-2xl md:text-3xl font-bold">{workflows.length}</p>
              </div>
              <div className="p-2 md:p-3 bg-purple-100 rounded-full">
                <GitFork className="h-4 w-4 md:h-6 md:w-6 text-purple-600" />
              </div>
            </div>
            <Link to="/workflows" className="text-xs md:text-sm text-purple-600 hover:underline mt-2 block">Build workflows →</Link>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4 md:pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm font-medium text-gray-500">Running Now</p>
                <p className="text-2xl md:text-3xl font-bold text-green-600">{runningCount}</p>
              </div>
              <div className="p-2 md:p-3 bg-green-100 rounded-full">
                <Zap className="h-4 w-4 md:h-6 md:w-6 text-green-600" />
              </div>
            </div>
            <p className="text-xs md:text-sm text-gray-400 mt-2">{completedCount} completed</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4 md:pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm font-medium text-gray-500">Failed</p>
                <p className="text-2xl md:text-3xl font-bold text-red-600">{failedCount}</p>
              </div>
              <div className="p-2 md:p-3 bg-red-100 rounded-full">
                <XCircle className="h-4 w-4 md:h-6 md:w-6 text-red-600" />
              </div>
            </div>
            <p className="text-xs md:text-sm text-gray-400 mt-2">Out of {executions.length} total</p>
          </CardContent>
        </Card>
      </div>

      {/* Bottom panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <CardTitle className="text-base md:text-lg">Recent Executions</CardTitle>
              <Link to="/executions"><Button variant="outline" size="sm">View all</Button></Link>
            </CardHeader>
            <CardContent>
              {recentExecutions.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <Play className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No executions yet. Trigger a workflow to get started.</p>
                </div>
              ) : (
                <div className="space-y-2 md:space-y-3">
                  {recentExecutions.map(exec => (
                    <Link key={exec.id} to={`/executions/${exec.id}`} className="block">
                      <div className="flex items-center justify-between p-2.5 md:p-3 rounded-lg border hover:bg-gray-50 transition-colors gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">
                            {(exec.trigger_payload as any)?.prompt || 'No prompt'}
                          </p>
                          <p className="text-xs text-gray-400 mt-0.5">
                            {new Date(exec.created_at).toLocaleString()}
                          </p>
                        </div>
                        <StatusBadge status={exec.status} />
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-base md:text-lg">Active Workflows</CardTitle>
            </CardHeader>
            <CardContent>
              {workflows.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <GitFork className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No workflows yet</p>
                  <Link to="/templates" className="text-sm text-blue-600 hover:underline mt-1 block">
                    Start from a template
                  </Link>
                </div>
              ) : (
                <div className="space-y-2">
                  {workflows.slice(0, 6).map(wf => (
                    <Link key={wf.id} to={`/workflows/${wf.id}`} className="block">
                      <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 transition-colors">
                        <div className="h-2 w-2 shrink-0 rounded-full bg-green-400" />
                        <span className="text-sm font-medium truncate">{wf.name}</span>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
