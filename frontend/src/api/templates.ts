import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from './client'
import type { Template } from './types'

export function useTemplates() {
  return useQuery({
    queryKey: ['templates'],
    queryFn: () => apiClient.get<Template[]>('/templates').then(r => r.data),
  })
}

export function useInstantiateTemplate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (slug: string) => apiClient.post(`/templates/${slug}/instantiate`).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['workflows'] })
      qc.invalidateQueries({ queryKey: ['agents'] })
    },
  })
}
