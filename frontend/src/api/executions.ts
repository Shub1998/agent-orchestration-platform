import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from './client'
import type { Execution } from './types'

export const executionKeys = {
  all: (workflowId?: string) => workflowId ? ['executions', workflowId] : ['executions'],
  detail: (id: string) => ['executions', 'detail', id] as const,
  logs: (id: string) => ['executions', 'logs', id] as const,
}

export function useExecutions(workflowId?: string) {
  return useQuery({
    queryKey: executionKeys.all(workflowId),
    queryFn: () => {
      const params = workflowId ? `?workflow_id=${workflowId}` : ''
      return apiClient.get<Execution[]>(`/executions${params}`).then(r => r.data)
    },
    refetchInterval: 5000,
  })
}

export function useExecution(id: string) {
  return useQuery({
    queryKey: executionKeys.detail(id),
    queryFn: () => apiClient.get<Execution>(`/executions/${id}`).then(r => r.data),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'running' || status === 'pending' || status === 'awaiting_approval' ? 2000 : false
    },
  })
}

export function useExecutionLogs(id: string) {
  return useQuery({
    queryKey: executionKeys.logs(id),
    queryFn: () => apiClient.get(`/executions/${id}/logs`).then(r => r.data),
    enabled: !!id,
  })
}

export function useCancelExecution() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/executions/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['executions'] }),
  })
}

export function useApproveExecution() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, decision, comment = '' }: { id: string; decision: 'approve' | 'reject'; comment?: string }) =>
      apiClient.post(`/executions/${id}/approve`, { decision, comment }).then(r => r.data),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: executionKeys.detail(vars.id) })
      qc.invalidateQueries({ queryKey: ['executions'] })
    },
  })
}
