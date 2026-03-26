// Auto-injected metadata for EmbedImages
const nodeMetadata = {
  "type": "EmbedImages",
  "name": "EmbedImages",
  "label": "Embed Images",
  "description": "Generate descriptions and embeddings for images using OpenAI",
  "category": "enrichment",
  "icon": "Image",
  "color": "bg-orange-500",
  "requiredUpstreamNodes": [],
  "dependencyHelperText": "Requires JSON input with an \"images\" attribute.",
  "inputs": [
    {
      "id": "images",
      "label": "Images",
      "type": "object",
      "required": true
    }
  ],
  "outputs": [
    {
      "id": "results",
      "label": "Results",
      "type": "array"
    }
  ],
  "defaultParams": {
    "prompt": "Describe this image in detail. Use the provided context (caption and article text) to inform your description, but focus primarily on what you see in the image itself.",
    "llm_model": "gpt-5.4-mini",
    "output_name": "image_embeddings"
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

import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { getNodeIcon, getNodeLabel, getNodeBgColor } from '@/lib/nodeUtils'

interface EmbedImagesData {
  prompt?: string
  llm_model?: string
}

function EmbedImagesNode({ data, selected }: NodeProps<EmbedImagesData>) {
  const requiredUpstreamNodes = nodeMetadata?.requiredUpstreamNodes || []
  const dependencyHelperText = nodeMetadata?.dependencyHelperText || ''
  const icon = getNodeIcon('EmbedImages', 'h-4 w-4')
  const bgColor = getNodeBgColor('EmbedImages')

  return (
    <Card className={`w-[200px] ${selected ? 'ring-2 ring-primary' : ''}`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <div className={`flex items-center justify-center w-6 h-6 rounded-full ${bgColor}`}>
            {icon}
          </div>
          Embed Images
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <Handle
          type="target"
          position={Position.Left}
          id="images"
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
          id="results"
          className="w-3 h-3 bg-gray-700"
        />
      </CardContent>
    </Card>
  )
}

export default memo(EmbedImagesNode)
