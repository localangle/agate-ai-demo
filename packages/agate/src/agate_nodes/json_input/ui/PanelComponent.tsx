import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useState, useEffect } from 'react'

interface JSONInputPanelProps {
  node: any
  onChange?: (jsonData: any) => void
  onRun?: () => void
  running?: boolean
  currentRun?: any
  editMode?: boolean
  setNodes?: (nodes: any) => void
}

export default function JSONInputPanel({
  node,
  onChange,
  onRun,
  running,
  currentRun,
  editMode,
  setNodes
}: JSONInputPanelProps) {
  const [jsonText, setJsonText] = useState('')
  const [jsonError, setJsonError] = useState('')

  // Initialize JSON text from node data
  useEffect(() => {
    try {
      setJsonText(JSON.stringify(node.data || { text: '' }, null, 2))
    } catch (e) {
      setJsonText('{\n  "text": ""\n}')
    }
  }, [node.id])

  const handleJsonChange = (value: string) => {
    setJsonText(value)
    
    try {
      const parsed = JSON.parse(value)
      
      // Validate that text field exists
      if (!parsed.text && parsed.text !== '') {
        setJsonError('JSON must include a "text" field')
        return
      }
      
      setJsonError('')
      
      // Update node data
      if (setNodes) {
        setNodes((nds: any[]) =>
          nds.map((n: any) =>
            n.id === node.id
              ? { ...n, data: parsed }
              : n
          )
        )
      }
    } catch (e) {
      setJsonError('Invalid JSON syntax')
    }
  }

  const isDisabled = !(editMode && setNodes)

  return (
    <>
      <div className="space-y-3">
        <div>
          <Label className="text-sm font-medium">Description</Label>
          <p className="text-sm text-muted-foreground mt-1">
            This node provides structured JSON data to the flow. The "text" field is required for downstream text processing. 
            You can add any additional fields which will be passed along to downstream nodes.
          </p>
        </div>
      </div>

      <div className="pt-4 border-t">
        <div>
          <Label className="text-sm font-medium">Parameters</Label>
        </div>
        
        <div className="space-y-2 mt-2">
          <div>
            <Label htmlFor="node-json" className="text-xs text-muted-foreground">
              JSON Data (must include "text" field)
            </Label>
            <Textarea
              id="node-json"
              value={jsonText}
              onChange={(e) => handleJsonChange(e.target.value)}
              placeholder='{\n  "text": "Your text here...",\n  "title": "Optional title",\n  "author": "Optional author"\n}'
              className="min-h-[300px] mt-1 font-mono text-xs"
              disabled={isDisabled}
            />
            {jsonError && (
              <p className="text-xs text-red-500 mt-1">{jsonError}</p>
            )}
            <p className="text-xs text-muted-foreground mt-1">
              Example: {'{'}
              "text": "Article content", "title": "Article Title", "source": "Source Name"
              {'}'}
            </p>
          </div>
        </div>
      </div>

      {currentRun && (
        <div className="pt-4 border-t">
          <Label className="text-sm font-medium">Latest Run</Label>
          <div className="mt-2 space-y-2">
            <div className="text-xs text-muted-foreground">
              <div>Fields provided: {Object.keys(node.data || {}).length}</div>
            </div>
            
            <div>
              <Label className="text-xs font-medium">Data Preview:</Label>
              <div className="text-xs font-mono p-2 bg-muted rounded mt-1 max-h-32 overflow-y-auto">
                {JSON.stringify(node.data || {}, null, 2)}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

