// Auto-injected metadata for Embed
const nodeMetadata = {
  "type": "Embed",
  "label": "Embed Text",
  "icon": "FileText",
  "description": "Create text embeddings using OpenAI",
  "category": "enrichment",
  "color": "bg-orange-500",
  "requiredUpstreamNodes": [],
  "dependencyHelperText": "Requires text input or JSON with a \"text\" attribute.",
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
      "id": "embedding",
      "label": "Embedding",
      "type": "array"
    }
  ],
  "defaultParams": {
    "model": "text-embedding-3-small",
    "dimensions": 1536,
    "output_name": "text_embedding"
  }
};

import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { getNodeIcon, getNodeLabel, getNodeBgColor } from '@/lib/nodeUtils'

interface EmbedData {
  model?: string
  dimensions?: number
}

function EmbedNode({ data, selected }: NodeProps<EmbedData>) {
  const requiredUpstreamNodes = nodeMetadata?.requiredUpstreamNodes || []
  const dependencyHelperText = nodeMetadata?.dependencyHelperText || ''
  const icon = getNodeIcon('Embed', 'h-4 w-4')
  const bgColor = getNodeBgColor('Embed')

  return (
    <Card className={`w-[200px] ${selected ? 'ring-2 ring-primary' : ''}`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <div className={`flex items-center justify-center w-6 h-6 rounded-full ${bgColor}`}>
            {icon}
          </div>
          Embed Text
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <Handle
          type="target"
          position={Position.Left}
          id="text"
          className="w-3 h-3 bg-gray-700"
        />
        <div className="text-xs space-y-2">
          {requiredUpstreamNodes.length > 0 && (
            <div className="space-y-1">
              <Label className="text-muted-foreground">Depends on:</Label>
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
        <Handle
          type="source"
          position={Position.Right}
          id="embedding"
          className="w-3 h-3 bg-gray-700"
        />
      </CardContent>
    </Card>
  )
}

export default memo(EmbedNode)
