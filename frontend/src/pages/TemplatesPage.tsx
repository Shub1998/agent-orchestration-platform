import { useTemplates, useInstantiateTemplate } from '@/api/templates'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Loader2, Search, Headphones, ChevronRight, Zap } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { Template } from '@/api/types'

const ICONS: Record<string, React.ComponentType<any>> = {
  search: Search,
  headphones: Headphones,
}

const CATEGORY_COLORS: Record<string, string> = {
  productivity: 'bg-blue-100 text-blue-700',
  support: 'bg-green-100 text-green-700',
}

export function TemplatesPage() {
  const { data: templates = [], isLoading } = useTemplates()
  const instantiate = useInstantiateTemplate()
  const navigate = useNavigate()

  const handleInstantiate = async (slug: string) => {
    const result = await instantiate.mutateAsync(slug)
    navigate(`/workflows`)
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Templates</h1>
        <p className="text-gray-500 mt-1">Pre-built workflow templates to get started quickly</p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-gray-400" /></div>
      ) : (
        <div className="grid grid-cols-2 gap-6 max-w-4xl">
          {templates.map((template: Template) => {
            const Icon = ICONS[template.icon] || Zap
            const colorClass = CATEGORY_COLORS[template.category] || 'bg-gray-100 text-gray-700'
            return (
              <Card key={template.slug} className="hover:shadow-lg transition-shadow border-2 hover:border-blue-200">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
                        <Icon className="h-6 w-6 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{template.name}</CardTitle>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium mt-1 inline-block ${colorClass}`}>
                          {template.category}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-sm text-gray-600 mb-4 leading-relaxed">
                    {template.description}
                  </CardDescription>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">{template.agent_count} agents</span>
                    <Button onClick={() => handleInstantiate(template.slug)} disabled={instantiate.isPending} size="sm">
                      {instantiate.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                      Use Template <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
