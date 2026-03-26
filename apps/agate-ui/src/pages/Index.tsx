import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { 
  listProjects, 
  listGraphs, 
  createProject, 
  updateProject, 
  deleteProject,
  deleteGraph,
  updateGraph,
  createGraph,
  type Project, 
  type Graph,
  type ProjectCreate,
  type GraphCreate
} from '@/lib/api'
import { formatDateCentral } from '@/lib/utils'
import { Loader2, Plus, Building2, Trash2, Copy } from 'lucide-react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import ProjectCard from '@/components/ProjectCard'
import ProjectDialog from '@/components/ProjectDialog'
import ProjectSettings from '@/components/ProjectSettings'
import RunsList from './RunsList'

export default function Index() {
  const [projects, setProjects] = useState<Project[]>([])
  const [graphs, setGraphs] = useState<Graph[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [flowToDelete, setFlowToDelete] = useState<Graph | null>(null)
  const [settingsProject, setSettingsProject] = useState<Project | null>(null)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      setLoading(true)
      const [projectsData, graphsData] = await Promise.all([
        listProjects(),
        listGraphs()
      ])
      setProjects(projectsData)
      setGraphs(graphsData)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateProject = () => {
    setEditingProject(null)
    setDialogOpen(true)
  }

  const handleEditProject = (project: Project) => {
    setEditingProject(project)
    setDialogOpen(true)
  }

  const handleSaveProject = async (data: ProjectCreate) => {
    try {
      if (editingProject) {
        const updated = await updateProject(editingProject.id, data)
        setProjects(prev => 
          prev.map(project => project.id === editingProject.id ? updated : project)
        )
      } else {
        const newProject = await createProject(data)
        setProjects(prev => [...prev, newProject])
      }
    } catch (error) {
      console.error('Failed to save project:', error)
      throw error
    }
  }

  const handleDeleteProject = async (project: Project) => {
    try {
      await deleteProject(project.id)
      setProjects(prev => prev.filter(p => p.id !== project.id))
    } catch (error) {
      console.error('Failed to delete project:', error)
      throw error
    }
  }

  const handleCreateFlow = (project: Project) => {
    // Navigate to flow creation with project context
    navigate(`/flow/new?project=${project.id}`)
  }

  const handleDeleteFlow = (flow: Graph) => {
    setFlowToDelete(flow)
    setDeleteDialogOpen(true)
  }

  const handleDuplicateFlow = async (flow: Graph) => {
    try {
      // Create a new graph with "Copy of" prefix
      const duplicateData: GraphCreate = {
        name: `Copy of ${flow.name}`,
        project_id: flow.project_id,
        spec: flow.spec
      }
      
      const newGraph = await createGraph(duplicateData)
      setGraphs(prev => [...prev, newGraph])
      
      // Navigate to the new flow
      navigate(`/flow/${newGraph.id}`)
    } catch (error) {
      console.error('Failed to duplicate flow:', error)
      // You could add a toast notification here
    }
  }

  const handleProjectSettings = (project: Project) => {
    setSettingsProject(project)
    setSettingsOpen(true)
  }

  const confirmDeleteFlow = async () => {
    if (!flowToDelete) return
    
    try {
      await deleteGraph(flowToDelete.id)
      setGraphs(prev => prev.filter(g => g.id !== flowToDelete.id))
      setDeleteDialogOpen(false)
      setFlowToDelete(null)
    } catch (error) {
      console.error('Failed to delete flow:', error)
      // You could add a toast notification here
    }
  }

  const handleProjectChange = async (graph: Graph, newProjectId: number) => {
    try {
      // Prepare update data - keep all existing fields, just change project_id
      const updateData: GraphCreate = {
        name: graph.name,
        project_id: newProjectId,
        spec: graph.spec
      }
      
      const updated = await updateGraph(graph.id, updateData)
      setGraphs(prev => prev.map(g => g.id === graph.id ? updated : g))
    } catch (error) {
      console.error('Failed to update flow project:', error)
      // You could add a toast notification here
    }
  }

  const getFlowsForProject = (projectId: number) => {
    return graphs.filter(graph => graph.project_id === projectId)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const ProjectsList = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Projects</h1>
          <p className="text-muted-foreground mt-1">
            Manage your projects and their flows
          </p>
        </div>
        <Button onClick={handleCreateProject}>
          <Plus className="mr-2 h-4 w-4" />
          New Project
        </Button>
      </div>

      {projects.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Building2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground mb-4">
                No projects yet. Create your first project to get started.
              </p>
              <Button onClick={handleCreateProject}>
                <Plus className="mr-2 h-4 w-4" />
                Create Project
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              flows={getFlowsForProject(project.id)}
              onEdit={handleEditProject}
              onDelete={handleDeleteProject}
              onCreateFlow={handleCreateFlow}
              onSettings={handleProjectSettings}
            />
          ))}
        </div>
      )}

      <ProjectDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        project={editingProject}
        onSave={handleSaveProject}
        onDelete={handleDeleteProject}
      />
      
      <ProjectSettings
        project={settingsProject}
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
      />
    </div>
  )

  return (
    <>
      <Tabs defaultValue="projects" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="projects">Projects</TabsTrigger>
          <TabsTrigger value="flows">Flows</TabsTrigger>
          <TabsTrigger value="runs">Runs</TabsTrigger>
        </TabsList>
        <TabsContent value="projects">
          <ProjectsList />
        </TabsContent>
        <TabsContent value="flows">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold">Flows</h1>
                <p className="text-muted-foreground mt-1">
                  View all flows across all projects
                </p>
              </div>
            </div>
            
            {graphs.length === 0 ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center">
                    <p className="text-muted-foreground mb-4">
                      No flows found. Create an project and add flows to get started.
                    </p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="p-0">
                  <table className="w-full">
                    <thead className="border-b bg-muted/50">
                      <tr>
                        <th className="text-left p-4 font-medium">Name</th>
                        <th className="text-left p-4 font-medium">Project</th>
                        <th className="text-left p-4 font-medium">Nodes</th>
                        <th className="text-left p-4 font-medium">Created</th>
                        <th className="text-right p-4 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {graphs.map((graph) => {
                        const org = projects.find(o => o.id === graph.project_id)
                        return (
                          <tr
                            key={graph.id}
                            className="border-b last:border-b-0 hover:bg-muted/50 transition-colors"
                          >
                            <td 
                              className="p-4 cursor-pointer"
                              onClick={() => navigate(`/flow/${graph.id}`)}
                            >
                              <div className="font-medium">{graph.name}</div>
                            </td>
                            <td 
                              className="p-4"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <Select
                                value={graph.project_id.toString()}
                                onValueChange={(value) => handleProjectChange(graph, parseInt(value))}
                              >
                                <SelectTrigger className="w-[180px]">
                                  <SelectValue placeholder="Select project" />
                                </SelectTrigger>
                                <SelectContent>
                                  {projects.map((project) => (
                                    <SelectItem key={project.id} value={project.id.toString()}>
                                      {project.name}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </td>
                            <td 
                              className="p-4 cursor-pointer"
                              onClick={() => navigate(`/flow/${graph.id}`)}
                            >
                              <div className="flex flex-wrap gap-1">
                                {graph.spec.nodes.map((node) => (
                                  <span
                                    key={node.id}
                                    className="text-xs px-2 py-1 bg-secondary rounded-md"
                                  >
                                    {node.type}
                                  </span>
                                ))}
                              </div>
                            </td>
                            <td 
                              className="p-4 text-sm text-muted-foreground cursor-pointer"
                              onClick={() => navigate(`/flow/${graph.id}`)}
                            >
                              {formatDateCentral(graph.created_at, { includeTime: false })}
                            </td>
                            <td className="p-4">
                              <div className="flex items-center justify-end gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleDuplicateFlow(graph)
                                  }}
                                  className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
                                  title="Duplicate flow"
                                >
                                  <Copy className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleDeleteFlow(graph)
                                  }}
                                  className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                                  title="Delete flow"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
        <TabsContent value="runs">
          <RunsList />
        </TabsContent>
      </Tabs>

      {/* Delete Flow Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Flow</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{flowToDelete?.name}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDeleteFlow}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

