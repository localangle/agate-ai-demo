// Auto-injected metadata for ImageEnrich
const nodeMetadata = {
  "type": "ImageEnrich",
  "label": "Image Enrich",
  "icon": "Sparkles",
  "description": "Generate structured metadata for images using LLM vision models",
  "category": "enrichment",
  "color": "bg-purple-500",
  "requiredUpstreamNodes": [],
  "dependencyHelperText": "Requires JSON input with image objects (\"image\" or \"images\" field, or objects with \"url\" or \"base64\" fields).",
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
      "id": "metadata",
      "label": "Metadata",
      "type": "array"
    }
  ],
  "defaultParams": {
    "prompt": "Analyze this image and extract structured metadata. Focus on visual elements, composition, subjects, and any relevant details.",
    "llm_model": "gpt-5.4-mini",
    "json_format": "{}",
    "output_name": "image_metadata"
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

interface ImageEnrichPanelProps {
  node: any
  onChange?: (text: string) => void
  onRun?: () => void
  running?: boolean
  currentRun?: any
  editMode?: boolean
  setNodes?: (nodes: any) => void
}

export default function ImageEnrichPanel({
  node,
  onChange,
  onRun,
  running,
  currentRun,
  editMode,
  setNodes
}: ImageEnrichPanelProps) {
  // Get latest run data - only show if we have specific node output
  const nodeOutput = currentRun?.node_outputs?.[node.id]
  const latestData = nodeOutput || null

  const availableModels = [
    { value: "gpt-5.4-mini", label: "GPT-5.4 Mini" },
    { value: "gpt-5.4", label: "GPT-5.4" },
    { value: "gpt-5.4-nano", label: "GPT-5.4 Nano" }
  ]

  return (
    <>
      <div className="space-y-3">
        <div>
          <Label className="text-sm font-medium">Description</Label>
          <p className="text-sm text-muted-foreground mt-1">
            This node uses LLM vision models to analyze images and extract structured metadata.
            Use JSON path placeholders in your prompt to include context from the input:
          </p>
          <ul className="text-xs text-muted-foreground mt-2 space-y-1 list-disc list-inside">
            <li><code className="bg-muted px-1 rounded">{'{caption}'}</code> - extracts the image caption</li>
            <li><code className="bg-muted px-1 rounded">{'{text}'}</code> - extracts article text (if available)</li>
            <li><code className="bg-muted px-1 rounded">{'{url}'}</code> - extracts the image URL</li>
            <li><code className="bg-muted px-1 rounded">{'{raw}'}</code> - passes entire input JSON</li>
          </ul>
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
                value={node.data.llm_model || 'gpt-5.4-mini'}
                onValueChange={(value) => {
                  setNodes((nds: any[]) =>
                    nds.map((n: any) =>
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
                  {availableModels.map((model) => (
                    <SelectItem key={model.value} value={model.value}>
                      {model.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <div className="flex justify-between items-center p-2 bg-muted rounded">
                <span className="text-muted-foreground">Model</span>
                <span className="font-medium text-xs">{node.data.llm_model || 'gpt-5.4-mini'}</span>
              </div>
            )}
          </div>
        </div>

        <div className="pt-2">
          <Label className="text-sm font-medium">Prompt</Label>
          {editMode && setNodes ? (
            <Textarea
              value={node.data.prompt || ''}
              onChange={(e) => {
                setNodes((nds: any[]) =>
                  nds.map((n: any) =>
                    n.id === node.id
                      ? { ...n, data: { ...n.data, prompt: e.target.value } }
                      : n
                  )
                )
              }}
              placeholder="Enter your prompt here. Use JSON path placeholders like {caption}, {text}, {raw}, etc."
              className="mt-2 min-h-[80px] text-xs font-mono"
            />
          ) : (
            <div className="mt-2 p-3 bg-muted rounded-lg">
              <p className="text-xs text-muted-foreground whitespace-pre-wrap">
                {node.data.prompt || 'No prompt set'}
              </p>
            </div>
          )}
        </div>

        <div className="pt-2">
          <Label className="text-sm font-medium">Output Format</Label>
          {editMode && setNodes ? (
            <Textarea
              value={node.data.json_format || ''}
              onChange={(e) => {
                setNodes((nds: any[]) =>
                  nds.map((n: any) =>
                    n.id === node.id
                      ? { ...n, data: { ...n.data, json_format: e.target.value } }
                      : n
                  )
                )
              }}
              placeholder='{"key": "value", "example": "format"}'
              className="mt-2 min-h-[60px] text-xs font-mono"
            />
          ) : (
            <div className="mt-2 p-3 bg-muted rounded-lg">
              <p className="text-xs text-muted-foreground font-mono">
                {node.data.json_format || '{}'}
              </p>
            </div>
          )}
          <p className="text-xs text-muted-foreground mt-1">
            Specify the format of the output as JSON
          </p>
        </div>

        <div className="pt-2">
          <Label className="text-sm font-medium">Output Field Name</Label>
          {editMode && setNodes ? (
            <input
              type="text"
              value={node.data.output_name || 'image_metadata'}
              onChange={(e) => {
                setNodes((nds: any[]) =>
                  nds.map((n: any) =>
                    n.id === node.id
                      ? { ...n, data: { ...n.data, output_name: e.target.value } }
                      : n
                  )
                )
              }}
              placeholder="image_metadata"
              className="mt-2 w-full px-3 py-2 text-xs border border-input bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            />
          ) : (
            <div className="mt-2 p-2 bg-muted rounded">
              <span className="text-xs font-mono">{node.data.output_name || 'image_metadata'}</span>
            </div>
          )}
          <p className="text-xs text-muted-foreground mt-1">
            Will be prefixed with "meta_" automatically
          </p>
        </div>
      </div>

      {latestData && latestData[`meta_${node.data.output_name || 'image_metadata'}`] && (
        <div className="pt-4 border-t">
          <Label className="text-sm font-medium">Latest Run</Label>
          <div className="mt-2 space-y-2">
            <div className="text-xs text-muted-foreground">
              <div>Metadata generated for {Array.isArray(latestData[`meta_${node.data.output_name || 'image_metadata'}`]) ? latestData[`meta_${node.data.output_name || 'image_metadata'}`].length : 0} image(s)</div>
            </div>
            
            <div>
              <Label className="text-xs font-medium">Sample Output:</Label>
              <div className="text-xs font-mono p-2 bg-muted rounded mt-1 max-h-32 overflow-y-auto">
                {JSON.stringify(latestData[`meta_${node.data.output_name || 'image_metadata'}`], null, 2).substring(0, 200)}
                {JSON.stringify(latestData[`meta_${node.data.output_name || 'image_metadata'}`], null, 2).length > 200 ? '...' : ''}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

