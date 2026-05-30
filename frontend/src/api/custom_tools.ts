import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from './client'
import type { CustomTool } from './types'

const KEYS = {
  all: ['custom-tools'] as const,
}

export function useCustomTools() {
  return useQuery({
    queryKey: KEYS.all,
    queryFn: () => apiClient.get<CustomTool[]>('/custom-tools').then(r => r.data),
  })
}

export function useCreateCustomTool() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Omit<CustomTool, 'id' | 'created_at' | 'updated_at'>) =>
      apiClient.post<CustomTool>('/custom-tools', data).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.all })
      qc.invalidateQueries({ queryKey: ['tools'] })
    },
  })
}

export function useUpdateCustomTool() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<CustomTool> & { id: string }) =>
      apiClient.patch<CustomTool>(`/custom-tools/${id}`, data).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.all })
      qc.invalidateQueries({ queryKey: ['tools'] })
    },
  })
}

export function useDeleteCustomTool() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/custom-tools/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.all })
      qc.invalidateQueries({ queryKey: ['tools'] })
    },
  })
}
