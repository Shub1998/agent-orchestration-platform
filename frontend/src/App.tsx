import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { DashboardPage } from '@/pages/DashboardPage'
import { AgentsPage } from '@/pages/AgentsPage'
import { WorkflowsPage } from '@/pages/WorkflowsPage'
import { ExecutionsPage } from '@/pages/ExecutionsPage'
import { TemplatesPage } from '@/pages/TemplatesPage'
import { SettingsPage } from '@/pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="agents" element={<AgentsPage />} />
          <Route path="workflows" element={<WorkflowsPage />} />
          <Route path="workflows/:id" element={<WorkflowsPage />} />
          <Route path="executions" element={<ExecutionsPage />} />
          <Route path="executions/:id" element={<ExecutionsPage />} />
          <Route path="templates" element={<TemplatesPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
