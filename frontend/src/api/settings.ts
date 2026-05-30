import { apiClient } from './client'

export interface SettingEntry {
  value: string
  is_set: boolean
}

export type SettingsMap = Record<string, SettingEntry>

export const settingsApi = {
  getAll: (): Promise<SettingsMap> =>
    apiClient.get('/settings').then(r => r.data),

  set: (key: string, value: string): Promise<{ key: string; is_set: boolean }> =>
    apiClient.put(`/settings/${key}`, { value }).then(r => r.data),

  clear: (key: string): Promise<{ key: string; is_set: boolean }> =>
    apiClient.delete(`/settings/${key}`).then(r => r.data),
}
