// Auto-injected metadata for GeocodeAgent
const nodeMetadata = {
  "type": "GeocodeAgent",
  "name": "GeocodeAgent",
  "label": "Geocode Agent",
  "description": "Intelligent geocoding using LLM reasoning",
  "category": "enrichment",
  "icon": "MapPin",
  "color": "bg-purple-500",
  "inputs": [
    {
      "id": "locations",
      "label": "Locations",
      "type": "array",
      "required": true
    }
  ],
  "outputs": [
    {
      "id": "locations",
      "label": "Geocoded Locations",
      "type": "array"
    }
  ],
  "defaultParams": {
    "model": "gpt-5.4-mini"
  },
  "parameters": {
    "model": {
      "type": "select",
      "label": "Model",
      "default": "gpt-5.4-mini",
      "options": [
        "gpt-5.4-mini",
        "gpt-5.4",
        "gpt-5.4-nano"
      ]
    }
  },
  "requiredUpstreamNodes": [
    "PlaceExtract",
    "PlaceFilter"
  ],
  "dependencyHelperText": "Requires extracted places as input."
};

import React from 'react'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'

interface GeocodeAgentPanelProps {
  node: any
  onChange?: (text: string) => void
  onRun?: () => void
  running?: boolean
  currentRun?: any
  editMode?: boolean
  setNodes?: (nodes: any) => void
}

export default function GeocodeAgentPanel({
  node,
  onChange,
  onRun,
  running,
  currentRun,
  editMode,
  setNodes
}: GeocodeAgentPanelProps) {
  const params = node.data || { 
    calculateParents: false,
  }
  
  const isDisabled = !(editMode && setNodes)
  
  const handleCalculateParentsChange = (checked: boolean) => {
    if (setNodes) {
      setNodes((nodes: any[]) =>
        nodes.map((n) =>
          n.id === node.id
            ? { ...n, data: { ...n.data, calculateParents: checked } }
            : n
        )
      )
    }
  }

  // Get latest run data - only show if we have specific node output
  const nodeOutput = currentRun?.node_outputs?.[node.id]
  const latestData = nodeOutput || null
  const locationCount = latestData?.locations?.length || 0

  return (
    <>
      <div className="space-y-3">
        <div>
          <Label className="text-sm font-medium">Description</Label>
          <p className="text-sm text-muted-foreground mt-1">
            This node uses LLM reasoning to intelligently geocode locations from PlaceExtract or PlaceFilter. 
            It enhances geocoding accuracy by understanding context and resolving ambiguities.
          </p>
        </div>
      </div>

      <div className="pt-4 border-t">
        <div>
          <Label className="text-sm font-medium">Parameters</Label>
        </div>
        
        <div className="space-y-3 mt-2">
          <div>
            <Label htmlFor="calculateParents" className="text-xs text-muted-foreground">Calculate Parents</Label>
            {editMode && setNodes ? (
              <div className="mt-1 flex items-center space-x-2">
                <Switch
                  id="calculateParents"
                  checked={params.calculateParents || false}
                  onCheckedChange={handleCalculateParentsChange}
                />
                <Label htmlFor="calculateParents" className="text-xs">
                  {params.calculateParents ? 'Enabled' : 'Disabled'}
                </Label>
              </div>
            ) : (
              <div className="mt-1 p-2 bg-muted rounded">
                <span className="text-xs font-mono">{params.calculateParents ? 'Enabled' : 'Disabled'}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {latestData && (
        <div className="pt-4 border-t">
          <Label className="text-sm font-medium">Latest Run</Label>
          <div className="mt-2 space-y-2">
            <div className="text-xs text-muted-foreground">
              <div>Geocoded {locationCount} location{locationCount !== 1 ? 's' : ''}</div>
            </div>
            
            {locationCount > 0 && (
              <div>
                <Label className="text-xs font-medium">Sample Output:</Label>
                <div className="text-xs font-mono p-2 bg-muted rounded mt-1 max-h-32 overflow-y-auto">
                  {JSON.stringify(latestData.locations[0], null, 2).substring(0, 200)}
                  {JSON.stringify(latestData.locations[0], null, 2).length > 200 ? '...' : ''}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
