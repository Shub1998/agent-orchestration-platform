import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from './client'
import type { Workflow, WorkflowNode, WorkflowEdge } from './types'

export const workflowKeys = {
  all: ['workflows'] as const,
  detail: (id: string) => ['workflows', id] as const,
}

export function useWorkflows() {
  return useQuery({
    queryKey: workflowKeys.all,
    queryFn: () => apiClient.get<Workflow[]>('/workflows').then(r => r.data),
  })
}

export function useWorkflow(id: string) {
  return useQuery({
    queryKey: workflowKeys.detail(id),
    queryFn: () => apiClient.get<Workflow>(`/workflows/${id}`).then(r => r.data),
    enabled: !!id,
  })
}

export function useCreateWorkflow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; description?: string; trigger_type?: string }) =>
      apiClient.post<Workflow>('/workflows', data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: workflowKeys.all }),
  })
}

export function useUpdateWorkflow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string } & Partial<Workflow>) =>
      apiClient.patch<Workflow>(`/workflows/${id}`, data).then(r => r.data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: workflowKeys.all })
      qc.invalidateQueries({ queryKey: workflowKeys.detail(vars.id) })
    },
  })
}

export function useDeleteWorkflow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/workflows/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: workflowKeys.all }),
  })
}

export function useSaveWorkflowGraph() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, nodes, edges }: { id: string; nodes: Partial<WorkflowNode>[]; edges: Partial<WorkflowEdge>[] }) =>
      apiClient.post<Workflow>(`/workflows/${id}/graph`, { nodes, edges }).then(r => r.data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: workflowKeys.detail(vars.id) })
    },
  })
}

export function useTriggerWorkflow() {
  return useMutation({
    mutationFn: ({ id, prompt, context }: { id: string; prompt: string; context?: Record<string, unknown> }) =>
      apiClient.post(`/workflows/${id}/trigger`, { prompt, context: context || {} }).then(r => r.data),
  })
}
