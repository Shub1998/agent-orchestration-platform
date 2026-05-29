import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from './client'
import type { Agent } from './types'

export const agentKeys = {
  all: ['agents'] as const,
  detail: (id: string) => ['agents', id] as const,
}

export function useAgents() {
  return useQuery({
    queryKey: agentKeys.all,
    queryFn: () => apiClient.get<Agent[]>('/agents').then(r => r.data),
  })
}

export function useAgent(id: string) {
  return useQuery({
    queryKey: agentKeys.detail(id),
    queryFn: () => apiClient.get<Agent>(`/agents/${id}`).then(r => r.data),
    enabled: !!id,
  })
}

export function useCreateAgent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Agent>) => apiClient.post<Agent>('/agents', data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: agentKeys.all }),
  })
}

export function useUpdateAgent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<Agent> & { id: string }) =>
      apiClient.patch<Agent>(`/agents/${id}`, data).then(r => r.data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: agentKeys.all })
      qc.invalidateQueries({ queryKey: agentKeys.detail(vars.id) })
    },
  })
}

export function useDeleteAgent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/agents/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: agentKeys.all }),
  })
}

export function useTestAgent() {
  return useMutation({
    mutationFn: ({ id, prompt }: { id: string; prompt: string }) =>
      apiClient.post(`/agents/${id}/test`, { prompt }).then(r => r.data),
  })
}

export function useClearAgentMemory() {
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/agents/${id}/memory`),
  })
}

export function useAvailableTools() {
  return useQuery({
    queryKey: ['tools'],
    queryFn: () => apiClient.get('/tools').then(r => r.data),
  })
}
