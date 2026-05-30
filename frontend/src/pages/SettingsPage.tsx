import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { settingsApi, SettingsMap } from '@/api/settings'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  CheckCircle, XCircle, Loader2, Database, Zap,
  MessageCircle, Hash, Bot, Eye, EyeOff, ChevronDown, ChevronUp, Info, X,
} from 'lucide-react'

// ─── Channel registry ────────────────────────────────────────────────────────
// To add a new channel: append one entry here. No other changes needed.
interface ChannelDef {
  id: string
  label: string
  icon: React.ElementType
  color: string
  description: string
  fields: FieldDef[]
  instructions: string[]
  docsUrl?: string
}

interface FieldDef {
  key: string           // stored as platform_setting key
  label: string
  placeholder: string
  secret?: boolean      // masked input
  hint?: string
}

const CHANNELS: ChannelDef[] = [
  {
    id: 'telegram',
    label: 'Telegram',
    icon: MessageCircle,
    color: 'blue',
    description: 'Trigger workflows and receive agent replies via Telegram.',
    fields: [
      {
        key: 'telegram_bot_token',
        label: 'Bot Token',
        placeholder: '123456789:ABCdefGHI...',
        secret: true,
        hint: 'From @BotFather → /newbot',
      },
    ],
    instructions: [
      'Open Telegram and message @BotFather.',
      'Send /newbot, follow prompts, and copy the token.',
      'Paste the token above and click Save.',
      'Restart the telegram_bot service (docker compose restart telegram_bot).',
      'Message your bot /start to link your chat.',
      'Set trigger type = telegram on any workflow.',
    ],
  },
  {
    id: 'slack',
    label: 'Slack',
    icon: Hash,
    color: 'green',
    description: 'Post agent outputs to Slack channels or respond to slash commands.',
    fields: [
      {
        key: 'slack_bot_token',
        label: 'Bot Token',
        placeholder: 'xoxb-...',
        secret: true,
        hint: 'From api.slack.com → OAuth & Permissions',
      },
      {
        key: 'slack_signing_secret',
        label: 'Signing Secret',
        placeholder: 'a1b2c3...',
        secret: true,
        hint: 'From api.slack.com → Basic Information',
      },
    ],
    instructions: [
      'Go to api.slack.com/apps and create a new app.',
      'Under OAuth & Permissions, add bot scopes: chat:write, commands.',
      'Install the app to your workspace and copy the Bot Token.',
      'Copy the Signing Secret from Basic Information.',
      'Paste both values above and click Save.',
      'Add the /slack integration handler to the backend (see docs).',
      'Set trigger type = slack on any workflow.',
    ],
  },
  {
    id: 'discord',
    label: 'Discord',
    icon: Bot,
    color: 'purple',
    description: 'Run agents from Discord commands or post results to channels.',
    fields: [
      {
        key: 'discord_bot_token',
        label: 'Bot Token',
        placeholder: 'MTI3...',
        secret: true,
        hint: 'From discord.com/developers → Bot → Token',
      },
      {
        key: 'discord_application_id',
        label: 'Application ID',
        placeholder: '1234567890...',
        hint: 'From discord.com/developers → General Information',
      },
    ],
    instructions: [
      'Go to discord.com/developers/applications and create a new application.',
      'Under Bot, click Add Bot and copy the Token.',
      'Copy the Application ID from General Information.',
      'Paste both values above and click Save.',
      'Invite the bot to your server with the bot OAuth2 scope.',
      'Add the /discord integration handler to the backend (see docs).',
      'Set trigger type = discord on any workflow.',
    ],
  },
]

// ─── How to add a new channel (developer instructions) ───────────────────────
const NEW_CHANNEL_STEPS = [
  {
    title: '1. Register the channel in the frontend',
    code: `// frontend/src/pages/SettingsPage.tsx  →  CHANNELS array
{
  id: 'my_channel',
  label: 'My Channel',
  icon: SomeIcon,          // lucide-react icon
  color: 'orange',         // tailwind color name
  description: 'Short description shown on the card.',
  fields: [
    { key: 'my_channel_token', label: 'Token', placeholder: 'tok_...', secret: true },
  ],
  instructions: [
    'Step 1: create a bot / app in the provider dashboard.',
    'Step 2: copy the token and paste it above.',
    'Step 3: restart the service.',
  ],
}`,
  },
  {
    title: '2. Add the backend integration',
    code: `# backend/app/integrations/my_channel/bot.py
# Read token from DB at startup:
from app.models.platform_setting import PlatformSetting
# ... implement your integration using the token

# backend/app/integrations/my_channel/router.py
# Add a FastAPI router for webhooks / polling

# backend/app/main.py
app.include_router(my_channel.router, prefix="/api/v1")`,
  },
  {
    title: '3. Add a send tool (optional)',
    code: `# backend/app/tools/send_my_channel.py
# Allows agents to push messages to your channel as a tool action`,
  },
]

// ─── Components ──────────────────────────────────────────────────────────────

const colorMap: Record<string, string> = {
  blue:   'bg-blue-50 border-blue-100 text-blue-900 text-blue-700',
  green:  'bg-green-50 border-green-100 text-green-900 text-green-700',
  purple: 'bg-purple-50 border-purple-100 text-purple-900 text-purple-700',
  orange: 'bg-orange-50 border-orange-100 text-orange-900 text-orange-700',
}

function ChannelCard({ channel, storedSettings }: { channel: ChannelDef; storedSettings: SettingsMap }) {
  const qc = useQueryClient()
  const [drafts, setDrafts] = useState<Record<string, string>>({})
  const [visible, setVisible] = useState<Record<string, boolean>>({})
  const [expanded, setExpanded] = useState(false)

  const isConfigured = channel.fields.every(f => storedSettings[f.key]?.is_set)

  const saveMutation = useMutation({
    mutationFn: async () => {
      for (const field of channel.fields) {
        const val = drafts[field.key]
        if (val !== undefined && val !== '') {
          await settingsApi.set(field.key, val)
        }
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['platform-settings'] })
      setDrafts({})
    },
  })

  const clearMutation = useMutation({
    mutationFn: async () => {
      for (const field of channel.fields) {
        await settingsApi.clear(field.key)
      }
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['platform-settings'] }),
  })

  const colorClasses = colorMap[channel.color] ?? colorMap.blue
  const [bg, border, title, body] = colorClasses.split(' ')
  const Icon = channel.icon

  const hasDraft = channel.fields.some(f => drafts[f.key] !== undefined && drafts[f.key] !== '')

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${bg} border ${border}`}>
              <Icon className={`h-5 w-5 ${body}`} />
            </div>
            <div>
              <CardTitle className="text-base">{channel.label}</CardTitle>
              <p className="text-sm text-gray-500 mt-0.5">{channel.description}</p>
            </div>
          </div>
          <Badge variant={isConfigured ? 'success' : 'secondary'} className="flex items-center gap-1 shrink-0">
            {isConfigured ? <CheckCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
            {isConfigured ? 'Configured' : 'Not set'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Fields */}
        <div className="space-y-3">
          {channel.fields.map(field => (
            <div key={field.key}>
              <Label className="text-xs font-medium text-gray-700">{field.label}</Label>
              {field.hint && <p className="text-xs text-gray-400 mb-1">{field.hint}</p>}
              <div className="flex gap-2 mt-1">
                <div className="relative flex-1">
                  <Input
                    type={field.secret && !visible[field.key] ? 'password' : 'text'}
                    placeholder={
                      storedSettings[field.key]?.is_set
                        ? storedSettings[field.key].value   // shows masked version from backend
                        : field.placeholder
                    }
                    value={drafts[field.key] ?? ''}
                    onChange={e => setDrafts(d => ({ ...d, [field.key]: e.target.value }))}
                    className="pr-8 font-mono text-sm"
                  />
                  {field.secret && (
                    <button
                      type="button"
                      onClick={() => setVisible(v => ({ ...v, [field.key]: !v[field.key] }))}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {visible[field.key] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={() => saveMutation.mutate()}
            disabled={!hasDraft || saveMutation.isPending}
          >
            {saveMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : null}
            Save
          </Button>
          {isConfigured && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => clearMutation.mutate()}
              disabled={clearMutation.isPending}
            >
              Clear
            </Button>
          )}
        </div>

        {/* Setup instructions (collapsible) */}
        <div>
          <button
            type="button"
            onClick={() => setExpanded(e => !e)}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
          >
            {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            Setup instructions
          </button>
          {expanded && (
            <div className={`mt-3 p-4 rounded-lg border ${bg} ${border}`}>
              <ol className={`text-sm ${body} space-y-1.5 list-decimal pl-4`}>
                {channel.instructions.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function ChannelInfoPopover() {
  const [open, setOpen] = useState(false)
  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="flex items-center justify-center h-5 w-5 rounded-full text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
        title="How to add a new channel"
      >
        <Info className="h-4 w-4" />
      </button>

      {open && (
        <>
          {/* backdrop */}
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />

          {/* panel */}
          <div className="absolute left-0 top-7 z-20 w-[560px] bg-white border border-gray-200 rounded-xl shadow-xl overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 border-b bg-gray-50">
              <p className="text-sm font-semibold text-gray-800">How to add a new messaging channel</p>
              <button type="button" onClick={() => setOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="px-5 py-4 space-y-5 max-h-[70vh] overflow-y-auto">
              {NEW_CHANNEL_STEPS.map(step => (
                <div key={step.title}>
                  <p className="text-xs font-semibold text-gray-700 mb-2">{step.title}</p>
                  <pre className="bg-gray-900 text-gray-200 rounded-lg p-3 text-xs overflow-x-auto whitespace-pre-wrap leading-relaxed">
                    {step.code}
                  </pre>
                </div>
              ))}
              <p className="text-xs text-gray-500 pb-1">
                The card appears automatically once you add the entry to the{' '}
                <code className="bg-gray-100 px-1 rounded">CHANNELS</code> array.
                Tokens are stored in <code className="bg-gray-100 px-1 rounded">platform_settings</code> and
                readable via <code className="bg-gray-100 px-1 rounded">GET /api/v1/settings</code>.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// ─── Page ────────────────────────────────────────────────────────────────────

export function SettingsPage() {
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.get('/health').then(r => r.data),
    refetchInterval: 10000,
  })

  const { data: storedSettings = {} } = useQuery({
    queryKey: ['platform-settings'],
    queryFn: settingsApi.getAll,
  })

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">Messaging channels, API keys, and system status</p>
      </div>

      <div className="max-w-2xl space-y-6">
        {/* System status */}
        <Card>
          <CardHeader><CardTitle className="text-lg">System Status</CardTitle></CardHeader>
          <CardContent>
            {healthLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <div className="space-y-3">
                {[
                  { label: 'API Server', status: health?.status === 'ok', icon: Zap },
                  { label: 'Redis', status: health?.redis === 'ok', icon: Database },
                ].map(({ label, status, icon: Icon }) => (
                  <div key={label} className="flex items-center justify-between py-2 border-b last:border-0">
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4 text-gray-500" />
                      <span className="text-sm font-medium">{label}</span>
                    </div>
                    <Badge variant={status ? 'success' : 'destructive'} className="flex items-center gap-1">
                      {status ? <CheckCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                      {status ? 'Online' : 'Offline'}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Messaging channels */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <h2 className="text-lg font-semibold text-gray-800">Messaging Channels</h2>
            <ChannelInfoPopover />
          </div>
          <div className="space-y-4">
            {CHANNELS.map(ch => (
              <ChannelCard key={ch.id} channel={ch} storedSettings={storedSettings} />
            ))}
          </div>
        </div>

        {/* API Keys reference */}
        <Card>
          <CardHeader><CardTitle className="text-lg">LLM API Keys</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500 mb-4">
              LLM provider keys are read from the <code className="bg-gray-100 px-1.5 py-0.5 rounded">.env</code> file at startup:
            </p>
            <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm space-y-1">
              <p className="text-green-400"># OpenAI</p>
              <p className="text-gray-300">OPENAI_API_KEY=sk-...</p>
              <p className="text-green-400 pt-2"># Anthropic</p>
              <p className="text-gray-300">ANTHROPIC_API_KEY=sk-ant-...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
