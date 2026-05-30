import { NavLink } from 'react-router-dom'
import { Bot, GitFork, Play, LayoutTemplate, Settings, Activity, Zap, Wrench } from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', icon: Activity, label: 'Dashboard', end: true },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/workflows', icon: GitFork, label: 'Workflows' },
  { to: '/executions', icon: Play, label: 'Executions' },
  { to: '/templates', icon: LayoutTemplate, label: 'Templates' },
  { to: '/tools', icon: Wrench, label: 'Custom Tools' },
]

export function Sidebar() {
  return (
    <aside className="w-14 lg:w-60 min-h-screen bg-gray-950 text-white flex flex-col shrink-0 transition-all duration-200">
      {/* Logo */}
      <div className="flex items-center gap-2 px-3 lg:px-6 py-5 border-b border-gray-800 overflow-hidden">
        <div className="p-1.5 bg-blue-600 rounded-lg shrink-0">
          <Zap className="h-5 w-5 text-white" />
        </div>
        <div className="hidden lg:block overflow-hidden">
          <h1 className="font-bold text-lg leading-none whitespace-nowrap">AgentFlow</h1>
          <p className="text-xs text-gray-400 mt-0.5 whitespace-nowrap">Orchestration Platform</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 lg:px-3 py-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            title={label}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-2.5 lg:px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            <span className="hidden lg:block">{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Settings */}
      <div className="px-2 lg:px-3 py-4 border-t border-gray-800">
        <NavLink
          to="/settings"
          title="Settings"
          className={({ isActive }) =>
            cn('flex items-center gap-3 px-2.5 lg:px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
              isActive ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800')
          }
        >
          <Settings className="h-4 w-4 shrink-0" />
          <span className="hidden lg:block">Settings</span>
        </NavLink>
      </div>
    </aside>
  )
}
