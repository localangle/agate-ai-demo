import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface WorksExtractPanelProps {
  node: any
  onChange?: (text: string) => void
  onRun?: () => void
  running?: boolean
  currentRun?: any
  editMode?: boolean
  setNodes?: (nodes: any) => void
}

export default function WorksExtractPanel({
  node,
  onChange,
  onRun,
  running,
  currentRun,
  editMode,
  setNodes
}: WorksExtractPanelProps) {
  const nodeOutput = currentRun?.node_outputs?.[node.id]
  const latestData = nodeOutput || null

  return (
    <>
      <div className="space-y-3">
        <div>
          <Label className="text-sm font-medium">Description</Label>
          <p className="text-sm text-muted-foreground mt-1">
            This node uses an LLM to extract works (laws, reports, books, products, artworks) from text. Use placeholders like {`{text}`} in your prompt.
          </p>
        </div>
      </div>

      <div className="pt-4 border-t">
        <div>
          <Label className="text-sm font-medium">Parameters</Label>
        </div>

        <div className="space-y-2 text-sm mt-2">
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Model</Label>
            {editMode && setNodes ? (
              <Select
                value={node.data.model || 'gpt-5.4-mini'}
                onValueChange={(value) => {
                  setNodes((nds: any[]) =>
                    nds.map((n: any) =>
                      n.id === node.id
                        ? { ...n, data: { ...n.data, model: value } }
                        : n
                    )
                  )
                }}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {nodeMetadata.availableModels?.map((model: any) => (
                    <SelectItem key={model.value} value={model.value}>
                      {model.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <div className="flex justify-between items-center p-2 bg-muted rounded">
                <span className="text-muted-foreground">Model</span>
                <span className="font-medium text-xs">{node.data.model || 'gpt-5.4-mini'}</span>
              </div>
            )}
          </div>
        </div>

        <div className="pt-2">
          <Label className="text-sm font-medium">Prompt</Label>
          {editMode && setNodes ? (
            <Textarea
              value={node.data?.prompt || nodeMetadata.defaultParams?.prompt || ''}
              onChange={(e) => {
                setNodes((nds: any[]) =>
                  nds.map((n: any) =>
                    n.id === node.id
                      ? { ...n, data: { ...n.data, prompt: e.target.value } }
                      : n
                  )
                )
              }}
              placeholder="Enter custom prompt"
              className="mt-2 min-h-[200px] px-3 py-2 text-xs border border-input bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 font-mono"
            />
          ) : (
            <div className="mt-2 p-2 bg-muted rounded max-h-48 overflow-y-auto">
              <pre className="text-xs whitespace-pre-wrap font-mono">
                {node.data?.prompt || nodeMetadata.defaultParams?.prompt || 'Using default prompt'}
              </pre>
            </div>
          )}
        </div>

        <div className="pt-2">
          <Label className="text-sm font-medium">Output Format</Label>
          {editMode && setNodes ? (
            <Textarea
              value={node.data?.json_format || nodeMetadata.defaultParams?.json_format || ''}
              onChange={(e) => {
                setNodes((nds: any[]) =>
                  nds.map((n: any) =>
                    n.id === node.id
                      ? { ...n, data: { ...n.data, json_format: e.target.value } }
                      : n
                  )
                )
              }}
              placeholder='{ "works": [] }'
              className="mt-2 min-h-[100px] px-3 py-2 text-xs border border-input bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 font-mono"
            />
          ) : (
            <div className="mt-2 p-2 bg-muted rounded max-h-48 overflow-y-auto">
              <pre className="text-xs whitespace-pre-wrap font-mono">
                {node.data?.json_format || nodeMetadata.defaultParams?.json_format || '{ "works": [] }'}
              </pre>
            </div>
          )}
        </div>
      </div>

      {latestData && latestData.works && (
        <div className="pt-4 border-t">
          <Label className="text-sm font-medium">Latest Run</Label>
          <div className="mt-2 space-y-2">
            <div className="text-xs text-muted-foreground">
              Works found: {latestData.works.length}
            </div>
            {latestData.works.length > 0 && (
              <div>
                <Label className="text-xs font-medium">Sample Works:</Label>
                <div className="mt-1 space-y-1 max-h-32 overflow-y-auto">
                  {latestData.works.slice(0, 3).map((work: any, index: number) => (
                    <div key={index} className="text-xs p-2 bg-muted rounded">
                      <div className="font-medium">
                        {work.name || 'Unknown'}
                        {work.type && ` (${work.type})`}
                      </div>
                      {work.role_in_story && (
                        <div className="text-muted-foreground mt-1">{work.role_in_story}</div>
                      )}
                      {work.mentions && work.mentions.length > 0 && (
                        <div className="text-muted-foreground mt-1 text-xs">
                          {work.mentions.length} mention{work.mentions.length !== 1 ? 's' : ''}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
