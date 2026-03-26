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
  const organizations = output.organizations
  if (!Array.isArray(organizations) || organizations.length === 0) {
    return null
  }

  const OrganizationsExtractVisualization: React.FC<VisualizationProps> = ({
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

    const orgs = output?.organizations || []

    return (
      <Card>
        <CardHeader>
          <CardTitle>Organizations Extract</CardTitle>
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
                {orgs.map((org: any, index: number) => {
                  const mentions = org.mentions || []
                  const isExpanded = expandedMentions.has(index)
                  return (
                    <React.Fragment key={index}>
                      <TableRow>
                        <TableCell className="font-medium">{org.name || '-'}</TableCell>
                        <TableCell>{org.type || '-'}</TableCell>
                        <TableCell>{org.role_in_story || '-'}</TableCell>
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
    id: `${nodeId}-organizations`,
    title: 'Organizations Extract',
    nodeId,
    nodeLabel,
    component: OrganizationsExtractVisualization,
  }
}
