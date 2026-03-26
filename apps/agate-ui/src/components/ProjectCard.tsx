import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Building2, 
  ArrowRight, 
  Plus, 
  Edit, 
  Trash2,
  MoreHorizontal,
  Play,
  Settings
} from 'lucide-react'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import type { Project, Graph } from '@/lib/api'
import {
  DEFAULT_PROJECT_NAME,
  LEGACY_DEFAULT_PROJECT_NAME,
} from '@/lib/defaultProject'
import { format } from 'date-fns'

interface ProjectCardProps {
  project: Project
  flows: Graph[]
  onEdit?: (project: Project) => void
  onDelete?: (project: Project) => void
  onCreateFlow?: (project: Project) => void
  onSettings?: (project: Project) => void
}

export default function ProjectCard({
  project,
  flows,
  onEdit,
  onDelete,
  onCreateFlow,
  onSettings
}: ProjectCardProps) {
  const navigate = useNavigate()
  const [isHovered, setIsHovered] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)

  // Sort flows by created_at descending (most recent first)
  const sortedFlows = [...flows].sort((a, b) => {
    const dateA = new Date(a.created_at).getTime()
    const dateB = new Date(b.created_at).getTime()
    return dateB - dateA // Descending order (newest first)
  })

  const totalFlows = sortedFlows.length
  const flowPreviewLimit = 5
  const displayedFlows = isExpanded ? sortedFlows : sortedFlows.slice(0, flowPreviewLimit)

  const handleCardClick = () => {
    // Navigate to project detail view (we'll implement this later)
    // For now, we'll just show the flows in a modal or navigate to a flows view
    console.log('Navigate to project:', project.id)
  }

  const handleCreateFlow = (e: React.MouseEvent) => {
    e.stopPropagation()
    onCreateFlow?.(project)
  }

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    onEdit?.(project)
  }

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    onDelete?.(project)
  }

  const handleSettings = (e: React.MouseEvent) => {
    e.stopPropagation()
    onSettings?.(project)
  }

  return (
    <Card 
      className="group cursor-pointer transition-all duration-200 hover:shadow-md hover:scale-[1.02]"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleCardClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Building2 className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg">{project.name}</CardTitle>
              <p className="text-sm text-muted-foreground">
                Created {format(new Date(project.created_at), 'MMM d, yyyy')}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleSettings}>
                  <Settings className="h-4 w-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                {project.name !== DEFAULT_PROJECT_NAME &&
                  project.name !== LEGACY_DEFAULT_PROJECT_NAME && (
                  <DropdownMenuItem 
                    onClick={handleDelete}
                    className="text-destructive focus:text-destructive"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-4">
          {/* Flow count and status */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="text-xs">
                {totalFlows} flow{totalFlows !== 1 ? 's' : ''}
              </Badge>
              {totalFlows > 0 && (
                <Badge variant="outline" className="text-xs">
                  Active
                </Badge>
              )}
            </div>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleCreateFlow}
              className="transition-all duration-200"
            >
              <Plus className="h-4 w-4 mr-1" />
              New Flow
            </Button>
          </div>

          {/* Recent flows */}
          {displayedFlows.length > 0 ? (
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">
                {isExpanded ? 'All Flows' : 'Recent Flows'}
              </p>
              <div className="space-y-1">
                {displayedFlows.map((flow) => (
                  <div
                    key={flow.id}
                    className="flex items-center justify-between p-2 bg-muted/50 rounded-md hover:bg-muted/70 transition-colors"
                    onClick={(e) => {
                      e.stopPropagation()
                      navigate(`/flow/${flow.id}`)
                    }}
                  >
                    <div className="flex items-center gap-2">
                      <Play className="h-3 w-3 text-muted-foreground" />
                      <span className="text-sm font-medium">{flow.name}</span>
                    </div>
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                  </div>
                ))}
              </div>
              
              {totalFlows > flowPreviewLimit && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setIsExpanded(!isExpanded)
                  }}
                  className="text-xs text-muted-foreground hover:text-foreground text-center w-full py-1 transition-colors"
                >
                  {isExpanded 
                    ? 'Show less' 
                    : `+${totalFlows - flowPreviewLimit} more flow${totalFlows - flowPreviewLimit !== 1 ? 's' : ''}`
                  }
                </button>
              )}
            </div>
          ) : (
            <div className="text-center py-4">
              <p className="text-sm text-muted-foreground mb-3">
                No flows yet
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={handleCreateFlow}
                className="w-full"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create First Flow
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
