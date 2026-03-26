// Auto-injected metadata for LLMEnrich
const nodeMetadata = {
  "type": "LLMEnrich",
  "label": "LLM Enrich",
  "icon": "Brain",
  "description": "Custom LLM enrichment with JSON output",
  "category": "enrichment",
  "color": "bg-green-500",
  "requiredUpstreamNodes": [],
  "dependencyHelperText": "Requires text or JSON input.",
  "inputs": [
    {
      "id": "text",
      "label": "Text",
      "type": "string",
      "required": true
    }
  ],
  "outputs": [
    {
      "id": "enriched_data",
      "label": "Enriched Data",
      "type": "object"
    }
  ],
  "defaultParams": {
    "model": "gpt-5.4-mini",
    "prompt": "",
    "json_format": "{}",
    "output_name": "meta_enriched_data"
  },
  "availableModels": [
    {
      "value": "gpt-5.4-mini",
      "label": "GPT-5.4 Mini"
    },
    {
      "value": "gpt-5.4",
      "label": "GPT-5.4"
    },
    {
      "value": "gpt-5.4-nano",
      "label": "GPT-5.4 Nano"
    }
  ]
};

import { Handle, Position } from 'reactflow'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getNodeIcon, getNodeLabel, getNodeBgColor } from '@/lib/nodeUtils'

export default function LLMEnrichNode({ data, selected }: any) {
  const requiredUpstreamNodes = nodeMetadata?.requiredUpstreamNodes || []
  const dependencyHelperText = nodeMetadata?.dependencyHelperText || ''
  const icon = getNodeIcon('LLMEnrich', 'h-4 w-4')
  const bgColor = getNodeBgColor('LLMEnrich')

  return (
    <Card className={`w-[200px] ${selected ? 'ring-2 ring-primary' : ''}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <div className={`flex items-center justify-center w-6 h-6 rounded-full ${bgColor}`}>
            {icon}
          </div>
          LLM Enrich
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="text-xs space-y-2">
          {requiredUpstreamNodes.length > 0 && (
            <div className="space-y-1">
              <span className="text-muted-foreground">Depends on:</span>
              <div className="flex flex-wrap gap-2">
                {requiredUpstreamNodes.map((nodeType: string) => {
                  const icon = getNodeIcon(nodeType, 'h-3 w-3')
                  const label = getNodeLabel(nodeType)
                  return (
                    <div key={nodeType} className="flex items-center gap-1">
                      {icon}
                      <span className="text-xs">{label}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
          {dependencyHelperText && (
            <p className="text-xs text-muted-foreground mt-1">{dependencyHelperText}</p>
          )}
        </div>
        {data?.output_name && (
          <div className="pt-2 border-t border-border/50">
            <p className="text-xs font-medium text-foreground truncate" title={data.output_name}>
              Output: {data.output_name}
            </p>
          </div>
        )}
        <Handle type="target" position={Position.Left} id="text" className="w-3 h-3 !bg-gray-700" />
        <Handle type="source" position={Position.Right} id="enriched_data" className="w-3 h-3 !bg-gray-700" />
      </CardContent>
    </Card>
  )
}
