import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { getNodeIcon, getNodeLabel, getNodeBgColor } from '@/lib/nodeUtils'

// Auto-injected metadata for StatsNode
const nodeMetadata = {
  "type": "StatsNode",
  "label": "Stats",
  "icon": "BarChart",
  "description": "Calculate text statistics (word count, character count, etc.)",
  "category": "text",
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
      "id": "meta_stats",
      "label": "Statistics",
      "type": "object"
    }
  ],
  "defaultParams": {
    "enabled_stats": ["word_count"]
  },
  "availableStats": [
    { "value": "word_count", "label": "Word Count" },
    { "value": "character_count", "label": "Character Count" },
    { "value": "character_count_no_spaces", "label": "Character Count (No Spaces)" },
    { "value": "sentence_count", "label": "Sentence Count" },
    { "value": "paragraph_count", "label": "Paragraph Count" },
    { "value": "reading_time_minutes", "label": "Reading Time (minutes)" }
  ]
};

interface StatsData {
  enabled_stats?: string[]
}

function StatsNode({ data, selected }: NodeProps<StatsData>) {
  const requiredUpstreamNodes = nodeMetadata?.requiredUpstreamNodes || []
  const dependencyHelperText = nodeMetadata?.dependencyHelperText || ''
  const icon = getNodeIcon('StatsNode', 'h-4 w-4')
  const bgColor = getNodeBgColor('StatsNode')

  return (
    <Card className={`w-[200px] ${selected ? 'ring-2 ring-primary' : ''}`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <div className={`flex items-center justify-center w-6 h-6 rounded-full ${bgColor}`}>
            {icon}
          </div>
          {getNodeLabel('StatsNode')}
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
        {data.enabled_stats && data.enabled_stats.length > 0 && (
          <div className="text-xs text-muted-foreground">
            <div className="font-medium">Stats:</div>
            <div>{data.enabled_stats.join(', ')}</div>
          </div>
        )}
        <Handle
          type="source"
          position={Position.Right}
          id="meta_stats"
          className="w-3 h-3 bg-gray-700"
        />
      </CardContent>
    </Card>
  )
}

export default memo(StatsNode)
