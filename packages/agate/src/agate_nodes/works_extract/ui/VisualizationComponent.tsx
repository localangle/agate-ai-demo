import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronRight } from 'lucide-react'
import type { VisualizationProps, VisualizationDescriptor } from '@/lib/visualizations'

export function buildVisualization(
  nodeId: string,
  nodeLabel: string,
  output: any
): VisualizationDescriptor | null {
  if (!output || typeof output !== 'object') {
    return null
  }
  const works = output.works
  if (!Array.isArray(works) || works.length === 0) {
    return null
  }

  const WorksExtractVisualization: React.FC<VisualizationProps> = ({
    nodeId,
    nodeLabel,
    output,
  }) => {
    const [expandedMentions, setExpandedMentions] = useState<Set<number>>(new Set())

    const toggleMentions = (index: number) => {
      const newExpanded = new Set(expandedMentions)
      if (newExpanded.has(index)) {
        newExpanded.delete(index)
      } else {
        newExpanded.add(index)
      }
      setExpandedMentions(newExpanded)
    }

    const worksList = output?.works || []

    return (
      <Card>
        <CardHeader>
          <CardTitle>Works Extract</CardTitle>
          {nodeLabel !== nodeId && <CardDescription>{nodeLabel}</CardDescription>}
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[200px]">Name</TableHead>
                  <TableHead className="w-[120px]">Type</TableHead>
                  <TableHead>Role in Story</TableHead>
                  <TableHead className="w-[100px]">Mentions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {worksList.map((work: any, index: number) => {
                  const mentions = work.mentions || []
                  const isExpanded = expandedMentions.has(index)
                  return (
                    <React.Fragment key={index}>
                      <TableRow>
                        <TableCell className="font-medium">{work.name || '-'}</TableCell>
                        <TableCell>{work.type || '-'}</TableCell>
                        <TableCell>{work.role_in_story || '-'}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span>{mentions.length}</span>
                            {mentions.length > 0 && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0"
                                onClick={() => toggleMentions(index)}
                              >
                                {isExpanded ? (
                                  <ChevronDown className="h-4 w-4" />
                                ) : (
                                  <ChevronRight className="h-4 w-4" />
                                )}
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                      {isExpanded &&
                        mentions.map((m: any, mi: number) => (
                          <TableRow key={`${index}-${mi}`} className="bg-muted/50">
                            <TableCell colSpan={4} className="text-xs py-2">
                              {m.text || '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                    </React.Fragment>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    )
  }

  return {
    id: `${nodeId}-works`,
    title: 'Works Extract',
    nodeId,
    nodeLabel,
    component: WorksExtractVisualization,
  }
}
