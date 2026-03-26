import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'

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

interface StatsPanelProps {
  node: any
  onChange?: (text: string) => void
  onRun?: () => void
  running?: boolean
  currentRun?: any
  editMode?: boolean
  setNodes?: (nodes: any) => void
}

export default function StatsPanel({
  node,
  onChange,
  onRun,
  running,
  currentRun,
  editMode,
  setNodes
}: StatsPanelProps) {
  // Get latest run data - only show if we have specific node output
  const nodeOutput = currentRun?.node_outputs?.[node.id]
  const latestData = nodeOutput || null

  const enabledStats = node.data.enabled_stats || nodeMetadata.defaultParams.enabled_stats || []

  const handleStatToggle = (statValue: string, checked: boolean) => {
    if (!setNodes) return
    
    const currentStats = enabledStats || []
    let newStats: string[]
    
    if (checked) {
      // Add stat if not already present
      newStats = currentStats.includes(statValue) ? currentStats : [...currentStats, statValue]
    } else {
      // Remove stat
      newStats = currentStats.filter((s: string) => s !== statValue)
    }
    
    setNodes((nds: any[]) =>
      nds.map((n: any) =>
        n.id === node.id
          ? { ...n, data: { ...n.data, enabled_stats: newStats } }
          : n
      )
    )
  }

  return (
    <>
      <div className="space-y-3">
        <div>
          <Label className="text-sm font-medium">Description</Label>
          <p className="text-sm text-muted-foreground mt-1">
            Calculate text statistics and output them as a meta_stats JSON object.
            Select which statistics to calculate from the options below.
          </p>
        </div>
      </div>

      <div className="pt-4 border-t">
        <div>
          <Label className="text-sm font-medium">Statistics</Label>
        </div>
        
        <div className="space-y-2 text-sm mt-2">
          {editMode && setNodes ? (
            <div className="space-y-2">
              {nodeMetadata.availableStats?.map((stat: any) => (
                <div key={stat.value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`stat-${stat.value}`}
                    checked={enabledStats.includes(stat.value)}
                    onCheckedChange={(checked) => handleStatToggle(stat.value, checked === true)}
                  />
                  <Label
                    htmlFor={`stat-${stat.value}`}
                    className="text-sm font-normal cursor-pointer"
                  >
                    {stat.label}
                  </Label>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-1">
              {enabledStats.length > 0 ? (
                enabledStats.map((statValue: string) => {
                  const stat = nodeMetadata.availableStats?.find((s: any) => s.value === statValue)
                  return (
                    <div key={statValue} className="flex justify-between items-center p-2 bg-muted rounded">
                      <span className="text-muted-foreground">{stat?.label || statValue}</span>
                      <span className="font-medium text-xs">✓</span>
                    </div>
                  )
                })
              ) : (
                <div className="p-2 bg-muted rounded text-muted-foreground text-xs">
                  No statistics selected
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {latestData && latestData.meta_stats && (
        <div className="pt-4 border-t">
          <Label className="text-sm font-medium">Results</Label>
          <div className="mt-2 p-3 bg-muted rounded-lg">
            <pre className="text-xs font-mono overflow-auto max-h-40">
              {JSON.stringify(latestData.meta_stats, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </>
  )
}
