import { Label } from '@/components/ui/label'

interface EmbedPanelProps {
  node: any
  onChange?: (text: string) => void
  onRun?: () => void
  running?: boolean
  currentRun?: any
  editMode?: boolean
  setNodes?: (nodes: any) => void
}

export default function EmbedPanel({
  node,
  onChange,
  onRun,
  running,
  currentRun,
  editMode,
  setNodes
}: EmbedPanelProps) {
  // Get latest run data - only show if we have specific node output
  const nodeOutput = currentRun?.node_outputs?.[node.id]
  const latestData = nodeOutput || null

  return (
    <>
      <div className="space-y-3">
        <div>
          <Label className="text-sm font-medium">Description</Label>
          <p className="text-sm text-muted-foreground mt-1">
            This node converts text into a vector embedding with {node.data.dimensions || 1536} dimensions using OpenAI's embedding models.
          </p>
        </div>
      </div>

      <div className="pt-4 border-t">
        <div>
          <Label className="text-sm font-medium">Parameters</Label>
        </div>
        
        <div className="space-y-2 text-sm mt-2">
          <div className="flex justify-between items-center p-2 bg-muted rounded">
            <span className="text-muted-foreground">Model</span>
            <span className="font-medium text-xs">{node.data.model || 'text-embedding-3-small'}</span>
          </div>
          
          <div className="flex justify-between items-center p-2 bg-muted rounded">
            <span className="text-muted-foreground">Dimensions</span>
            <span className="font-medium">{node.data.dimensions || 1536}</span>
          </div>
        </div>

        <div className="pt-2">
          <Label className="text-sm font-medium">Output Field Name</Label>
          {editMode && setNodes ? (
            <input
              type="text"
              value={node.data?.output_name || 'text_embedding'}
              onChange={(e) => {
                setNodes((nodes: any) =>
                  nodes.map((n: any) =>
                    n.id === node.id
                      ? { ...n, data: { ...n.data, output_name: e.target.value } }
                      : n
                  )
                )
              }}
              placeholder="text_embedding"
              className="mt-2 w-full px-3 py-2 text-xs border border-input bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            />
          ) : (
            <div className="mt-2 p-2 bg-muted rounded">
              <span className="text-xs font-mono">{node.data?.output_name || 'text_embedding'}</span>
            </div>
          )}
        </div>
      </div>

      {(() => {
        if (!latestData) return null
        
        // Get the embedding data from the output field name
        const outputName = node.data?.output_name || 'text_embedding'
        const embeddingData = latestData[outputName]
        
        if (!embeddingData || !embeddingData.embedding) {
          return null
        }
        
        return (
          <div className="pt-4 border-t">
            <Label className="text-sm font-medium">Latest Run</Label>
            <div className="mt-2 space-y-2">
              <div className="text-xs text-muted-foreground">
                <div>Vector Length: {embeddingData.embedding.length}</div>
                <div>Model: {embeddingData.embedding_model || 'text-embedding-3-small'}</div>
              </div>
              
              <div>
                <Label className="text-xs font-medium">First 5 dimensions:</Label>
                <div className="text-xs font-mono p-2 bg-muted rounded mt-1">
                  [{embeddingData.embedding.slice(0, 5).map((val: number) => val.toFixed(4)).join(', ')}...]
                </div>
              </div>
            </div>
          </div>
        )
      })()}
    </>
  )
}
