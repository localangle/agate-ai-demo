import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { getNodeIcon, getNodeLabel, getNodeBgColor } from '@/lib/nodeUtils'

interface ImageEnrichData {
  prompt?: string
  llm_model?: string
  output_name?: string
}

function ImageEnrichNode({ data, selected }: NodeProps<ImageEnrichData>) {
  const requiredUpstreamNodes: string[] = []
  const dependencyHelperText = 'Requires JSON input with image objects ("image" or "images" field, or objects with "url" or "base64" fields).'
  const icon = getNodeIcon('ImageEnrich', 'h-4 w-4')
  const bgColor = getNodeBgColor('ImageEnrich')

  return (
    <Card className={`w-[200px] ${selected ? 'ring-2 ring-primary' : ''}`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <div className={`flex items-center justify-center w-6 h-6 rounded-full ${bgColor}`}>
            {icon}
          </div>
          Image Enrich
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
        {data?.output_name && (
          <div className="pt-2 border-t border-border/50">
            <p className="text-xs font-medium text-foreground truncate" title={data.output_name}>
              Output: {data.output_name}
            </p>
          </div>
        )}
        <Handle
          type="source"
          position={Position.Right}
          id="metadata"
          className="w-3 h-3 bg-gray-700"
        />
      </CardContent>
    </Card>
  )
}

export default memo(ImageEnrichNode)

