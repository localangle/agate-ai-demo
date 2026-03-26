import type React from 'react'
import { nodeMetadata, visualizationComponents } from '@/nodes/registry'

export type MapPointFeature = {
  id: string
  coordinates: [number, number]
  label?: string
  description?: string
  group?: string
}

export type MapBoundingBoxFeature = {
  id: string
  bbox: [number, number, number, number]
  label?: string
  description?: string
  group?: string
  geometry?: {
    type: 'Polygon' | 'MultiPolygon'
    coordinates: number[][][] | number[][][][]
  }
}

export type GeocodeMapData = {
  points: MapPointFeature[]
  polygons: MapBoundingBoxFeature[]
}

export type VisualizationProps = {
  nodeId: string
  nodeLabel: string
  output: any
  data?: any
}

export type VisualizationDescriptor = {
  id: string
  nodeId: string
  title: string
  description?: string
  component: React.ComponentType<VisualizationProps>
  data?: any
  nodeOutput?: any
}

type BuildVisualizationFn = (
  nodeId: string,
  nodeLabel: string,
  output: any,
) => VisualizationDescriptor | null

type RunItemForVisualizations = {
  item: {
    output?: any
    node_outputs?: Record<string, any>
  }
  graph: {
    spec: {
      nodes: Array<{ id: string; type: string }>
    }
  }
}

export async function getVisualizationsForItem({
  item,
  graph,
}: RunItemForVisualizations): Promise<VisualizationDescriptor[]> {
  if (!item || !graph?.spec?.nodes) return []

  const descriptors: VisualizationDescriptor[] = []
  const nodeOutputs = item.node_outputs || {}

  for (const node of graph.spec.nodes) {
    const loader = visualizationComponents[node.type as keyof typeof visualizationComponents]
    if (!loader) continue

    try {
      const module = await loader()
      const buildVisualization = module.buildVisualization as BuildVisualizationFn | undefined
      if (!buildVisualization) continue

      const label = nodeMetadata.find((m) => m.type === node.type)?.label || node.type
      const output = nodeOutputs[node.id] ?? item.output
      const descriptor = buildVisualization(node.id, label, output)
      if (descriptor) {
        descriptors.push({ ...descriptor, nodeOutput: output })
      }
    } catch (error) {
      // Keep rendering other visualizations if one fails.
      console.error(`Failed to load visualization for ${node.type}:`, error)
    }
  }

  return descriptors
}

