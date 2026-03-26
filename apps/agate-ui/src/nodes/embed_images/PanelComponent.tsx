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

import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface EmbedImagesPanelProps {
  node: any
  onChange?: (text: string) => void
  onRun?: () => void
  running?: boolean
  currentRun?: any
  editMode?: boolean
  setNodes?: (nodes: any) => void
}

export default function EmbedImagesPanel({
  node,
  onChange,
  onRun,
  running,
  currentRun,
  editMode,
  setNodes
}: EmbedImagesPanelProps) {
  // Get latest run data - only show if we have specific node output
  const nodeOutput = currentRun?.node_outputs?.[node.id]
  const latestData = nodeOutput || null

  return (
    <>
      <div className="space-y-3">
        <div>
          <Label className="text-sm font-medium">Description</Label>
          <p className="text-sm text-muted-foreground mt-1">
            This node generates text descriptions for images using OpenAI vision models, then creates embeddings of those descriptions.
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
                value={node.data?.llm_model || 'gpt-5.4-mini'}
                onValueChange={(value) => {
                  setNodes((nodes: any) =>
                    nodes.map((n: any) =>
                      n.id === node.id
                        ? { ...n, data: { ...n.data, llm_model: value } }
                        : n
                    )
                  )
                }}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {nodeMetadata.availableModels?.map((model) => (
                    <SelectItem key={model.value} value={model.value}>
                      {model.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <div className="flex justify-between items-center p-2 bg-muted rounded">
                <span className="text-muted-foreground">Model</span>
                <span className="font-medium text-xs">{node.data?.llm_model || 'gpt-5.4-mini'}</span>
              </div>
            )}
          </div>
        </div>

        <div className="pt-2">
          <Label className="text-sm font-medium">Prompt</Label>
          {editMode && setNodes ? (
            <Textarea
              placeholder="Enter prompt for image analysis..."
              value={node.data?.prompt || "Describe this image in detail."}
              onChange={(e) => {
                setNodes((nodes: any) =>
                  nodes.map((n: any) =>
                    n.id === node.id
                      ? { ...n, data: { ...n.data, prompt: e.target.value } }
                      : n
                  )
                )
              }}
              className="mt-2 min-h-[100px] text-xs font-mono"
            />
          ) : (
            <div className="mt-2 p-3 bg-muted rounded-lg">
              <p className="text-xs text-muted-foreground whitespace-pre-wrap">
                {node.data?.prompt || 'Describe this image in detail.'}
              </p>
            </div>
          )}
        </div>

        <div className="pt-2 text-xs text-muted-foreground">
          <div>Embedding Model: text-embedding-3-small (1536 dimensions)</div>
        </div>

        <div className="pt-2">
          <Label className="text-sm font-medium">Output Field Name</Label>
          {editMode && setNodes ? (
            <input
              type="text"
              value={node.data?.output_name || 'image_embeddings'}
              onChange={(e) => {
                setNodes((nodes: any) =>
                  nodes.map((n: any) =>
                    n.id === node.id
                      ? { ...n, data: { ...n.data, output_name: e.target.value } }
                      : n
                  )
                )
              }}
              placeholder="image_embeddings"
              className="mt-2 w-full px-3 py-2 text-xs border border-input bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            />
          ) : (
            <div className="mt-2 p-2 bg-muted rounded">
              <span className="text-xs font-mono">{node.data?.output_name || 'image_embeddings'}</span>
            </div>
          )}
        </div>
      </div>

      {latestData && latestData[node.data?.output_name || 'image_embeddings'] && (
        <div className="pt-4 border-t">
          <Label className="text-sm font-medium">Latest Results</Label>
          <div className="mt-2 space-y-3">
            {latestData[node.data?.output_name || 'image_embeddings'].map((result: any, index: number) => (
              <div key={index} className="p-3 bg-muted rounded-md">
                <div className="text-xs space-y-2">
                  <div>
                    <Label className="text-xs font-medium">Image {index + 1}</Label>
                    {result.url && (
                      <div className="text-xs text-muted-foreground mt-1">
                        URL: {result.url.substring(0, 50)}...
                      </div>
                    )}
                    {result.caption && (
                      <div className="text-xs text-muted-foreground mt-1">
                        Caption: {result.caption}
                      </div>
                    )}
                  </div>
                  <div>
                    <Label className="text-xs font-medium">Generated Text:</Label>
                    <div className="text-xs p-2 bg-background rounded mt-1">
                      {result.generated_text?.substring(0, 200)}
                      {result.generated_text && result.generated_text.length > 200 && '...'}
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    <div>Embedding Dimensions: {result.embedding_dimensions || result.embedding?.length || 0}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
