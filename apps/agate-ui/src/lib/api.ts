const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
    ...init,
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Request failed: ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export type Project = {
  id: number
  name: string
  system_prompt?: string
  created_at: string
}

export type ProjectCreate = {
  name: string
  system_prompt?: string | null
}

export type ApiKey = {
  key_name: string
  created_at: string
  updated_at: string
}

export type ApiKeyCreate = {
  key_name: string
  value: string
}

export type GraphSpecNode = {
  id: string
  type: string
  params: Record<string, any>
  position?: { x: number; y: number }
}

export type GraphSpecEdge = {
  source: string
  target: string
  sourceHandle?: string | null
  targetHandle?: string | null
}

export type GraphSpec = {
  name: string
  nodes: GraphSpecNode[]
  edges: GraphSpecEdge[]
}

export type Graph = {
  id: number
  name: string
  project_id: number
  spec: GraphSpec
  created_at: string
  updated_at: string
}

export type GraphCreate = {
  name: string
  project_id: number
  spec: GraphSpec
}

export type ProcessedItemSummary = {
  id: number
  status: string
  source_file?: string | null
  created_at: string
  updated_at: string
  output_s3_bucket?: string | null
  output_s3_key?: string | null
  current_node_types?: string[] | null
  input_article_id?: string | null
  input_headline?: string | null
  is_array_splitter_item?: boolean
}

export type ProcessedItem = {
  id: number
  run_id: number
  status: string
  input?: Record<string, any> | null
  output?: Record<string, any> | null
  error?: string | null
  source_file?: string | null
  created_at: string
  updated_at: string
  node_outputs?: Record<string, any>
  node_logs?: Record<string, string[]>
}

export type Run = {
  id: number
  graph_id: number
  project_id: number
  status: 'pending' | 'running' | 'completed' | 'completed_with_errors'
  total_items: number
  pending_items: number
  running_items: number
  succeeded_items: number
  failed_items: number
  created_at: string
  updated_at: string
  node_outputs?: Record<string, any>
  node_logs?: Record<string, string[]>
  items?: ProcessedItemSummary[]
}

export async function listProjects() {
  return request<Project[]>('/projects/')
}

export async function createProject(data: ProjectCreate) {
  return request<Project>('/projects/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateProject(projectId: number, data: Partial<ProjectCreate>) {
  return request<Project>(`/projects/${projectId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteProject(projectId: number) {
  return request<{ message: string }>(`/projects/${projectId}`, { method: 'DELETE' })
}

export async function listProjectApiKeys(projectId: number) {
  return request<ApiKey[]>(`/projects/${projectId}/api-keys`)
}

export async function setProjectApiKey(projectId: number, data: ApiKeyCreate) {
  return request<ApiKey>(`/projects/${projectId}/api-keys`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function deleteProjectApiKey(projectId: number, keyName: string) {
  return request<{ message: string }>(`/projects/${projectId}/api-keys/${encodeURIComponent(keyName)}`, {
    method: 'DELETE',
  })
}

export async function listGraphs() {
  return request<Graph[]>('/graphs')
}

export async function getGraph(graphId: number) {
  return request<Graph>(`/graphs/${graphId}`)
}

export async function createGraph(data: GraphCreate) {
  return request<Graph>('/graphs', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateGraph(graphId: number, data: GraphCreate) {
  return request<Graph>(`/graphs/${graphId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteGraph(graphId: number) {
  return request<{ message: string }>(`/graphs/${graphId}`, { method: 'DELETE' })
}

export async function listRuns(limit = 50, offset = 0) {
  return request<Run[]>(`/runs?limit=${limit}&offset=${offset}`)
}

export async function getRun(runId: number) {
  return request<Run>(`/runs/${runId}`)
}

export async function createRun(graphId: number, data: { input: Record<string, any> }) {
  return request<Run>(`/runs/${graphId}`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function cancelRun(runId: number) {
  return request<Run>(`/runs/${runId}/cancel`, { method: 'POST' })
}

export async function getProcessedItem(runId: number, itemId: number) {
  return request<ProcessedItem>(`/runs/${runId}/items/${itemId}`)
}

export async function rerunProcessedItem(runId: number, itemId: number) {
  return request<{ message: string }>(`/runs/${runId}/items/${itemId}/rerun`, {
    method: 'POST',
  })
}

