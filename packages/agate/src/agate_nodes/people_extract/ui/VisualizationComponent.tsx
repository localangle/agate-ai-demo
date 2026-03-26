import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronRight, CheckCircle, XCircle } from 'lucide-react'
import type { VisualizationProps, VisualizationDescriptor } from '@/lib/visualizations'

/**
 * Build visualization descriptor for PeopleExtract node output.
 * Returns null if no valid people data is found.
 */
export function buildVisualization(
  nodeId: string,
  nodeLabel: string,
  output: any
): VisualizationDescriptor | null {
  if (!output || typeof output !== 'object') {
    return null
  }

  const people = output.people
  if (!Array.isArray(people) || people.length === 0) {
    return null
  }

  // Visualization component
  const PeopleExtractVisualization: React.FC<VisualizationProps> = ({ nodeId, nodeLabel, output }) => {
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

    const people = output?.people || []

    return (
      <Card>
        <CardHeader>
          <CardTitle>People Extract</CardTitle>
          {nodeLabel !== nodeId && (
            <CardDescription>{nodeLabel}</CardDescription>
          )}
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[200px]">Name</TableHead>
                  <TableHead className="w-[150px]">Title</TableHead>
                  <TableHead className="w-[200px]">Affiliation</TableHead>
                  <TableHead>Role in Story</TableHead>
                  <TableHead className="w-[100px]">Public Figure</TableHead>
                  <TableHead className="w-[120px]">Mentions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {people.map((person: any, index: number) => {
                  const name = person.name
                  const fullName = typeof name === 'string' ? name : name?.full || 'Unknown'
                  const firstName = typeof name === 'object' ? name?.first || '' : ''
                  const lastName = typeof name === 'object' ? name?.last || '' : ''
                  const displayName = fullName || `${firstName} ${lastName}`.trim() || 'Unknown'
                  
                  const mentions = person.mentions || []
                  const isExpanded = expandedMentions.has(index)

                  return (
                    <React.Fragment key={index}>
                      <TableRow>
                        <TableCell className="font-medium">{displayName}</TableCell>
                        <TableCell>{person.title || '-'}</TableCell>
                        <TableCell>{person.affiliation || '-'}</TableCell>
                        <TableCell>{person.role_in_story || '-'}</TableCell>
                        <TableCell>{person.public_figure ? 'Yes' : 'No'}</TableCell>
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
                      {isExpanded && mentions.length > 0 && (
                        <TableRow>
                          <TableCell colSpan={6} className="bg-muted/50">
                            <div className="space-y-2 py-2">
                              <div className="text-xs font-medium text-muted-foreground">Mentions:</div>
                              {mentions.map((mention: any, mentionIndex: number) => {
                                const isVerified = mention.verified ?? false
                                
                                return (
                                  <div key={mentionIndex} className="text-sm pl-4 border-l-2 border-border">
                                    <div className="flex items-start gap-2">
                                      <div className="flex items-center gap-1.5 mt-0.5">
                                        {isVerified ? (
                                          <CheckCircle className="h-4 w-4 text-green-600" title="Verified: Mention found in original text" />
                                        ) : (
                                          <XCircle className="h-4 w-4 text-red-600" title="Not verified: Mention not found in original text" />
                                        )}
                                        {mention.quote && (
                                          <span className="text-xs font-medium text-primary px-1.5 py-0.5 bg-primary/10 rounded">Quote</span>
                                        )}
                                      </div>
                                      <span className="flex-1">{mention.text}</span>
                                    </div>
                                  </div>
                                )
                              })}
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
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
    id: `${nodeId}-people`,
    nodeId,
    title: 'People Extract',
    description: nodeLabel !== nodeId ? nodeLabel : undefined,
    component: PeopleExtractVisualization,
    data: undefined,
  }
}

