import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, XCircle, Loader2, MessageCircle, Database, Zap, Bot } from 'lucide-react'

export function SettingsPage() {
  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.get('/health').then(r => r.data),
    refetchInterval: 10000,
  })

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">System status and configuration</p>
      </div>

      <div className="max-w-2xl space-y-6">
        <Card>
          <CardHeader><CardTitle className="text-lg">System Status</CardTitle></CardHeader>
          <CardContent>
            {isLoading ? (
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

        <Card>
          <CardHeader><CardTitle className="text-lg">Telegram Integration</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-4 bg-blue-50 rounded-lg border border-blue-100">
                <MessageCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-blue-900">How to set up Telegram</p>
                  <ol className="text-sm text-blue-700 mt-2 space-y-1.5 list-decimal pl-4">
                    <li>Message <code className="bg-blue-100 px-1 rounded">@BotFather</code> on Telegram and create a new bot</li>
                    <li>Copy the bot token and add it as <code className="bg-blue-100 px-1 rounded">TELEGRAM_BOT_TOKEN</code> in your <code className="bg-blue-100 px-1 rounded">.env</code> file</li>
                    <li>Restart the <code className="bg-blue-100 px-1 rounded">telegram_bot</code> service</li>
                    <li>Message your bot <code className="bg-blue-100 px-1 rounded">/start</code> to get your chat ID</li>
                    <li>Configure a workflow with trigger type = <code className="bg-blue-100 px-1 rounded">telegram</code></li>
                  </ol>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-lg">API Keys</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500 mb-4">Configure API keys in your <code className="bg-gray-100 px-1.5 py-0.5 rounded">.env</code> file:</p>
            <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm">
              <p className="text-green-400"># Required for OpenAI models</p>
              <p className="text-gray-300">OPENAI_API_KEY=sk-...</p>
              <p className="text-green-400 mt-2"># Required for Anthropic models</p>
              <p className="text-gray-300">ANTHROPIC_API_KEY=sk-ant-...</p>
              <p className="text-green-400 mt-2"># Required for Telegram bot</p>
              <p className="text-gray-300">TELEGRAM_BOT_TOKEN=...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
