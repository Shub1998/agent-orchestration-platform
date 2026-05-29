import { NavLink } from 'react-router-dom'
import { Bot, GitFork, Play, LayoutTemplate, Settings, Activity, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', icon: Activity, label: 'Dashboard', end: true },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/workflows', icon: GitFork, label: 'Workflows' },
  { to: '/executions', icon: Play, label: 'Executions' },
  { to: '/templates', icon: LayoutTemplate, label: 'Templates' },
]

export function Sidebar() {
  return (
    <aside className="w-60 min-h-screen bg-gray-950 text-white flex flex-col">
      <div className="flex items-center gap-2 px-6 py-5 border-b border-gray-800">
        <div className="p-1.5 bg-blue-600 rounded-lg">
          <Zap className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-lg leading-none">AgentFlow</h1>
          <p className="text-xs text-gray-400 mt-0.5">Orchestration Platform</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-3 py-4 border-t border-gray-800">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            cn('flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
              isActive ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800')
          }
        >
          <Settings className="h-4 w-4" />
          Settings
        </NavLink>
      </div>
    </aside>
  )
}
