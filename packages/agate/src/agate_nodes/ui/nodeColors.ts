// Synced from apps/agate-ui/src/lib/nodeColors.ts — edit there first.

export const categoryColors = {
  input: 'text-blue-500',
  enrichment: 'text-green-500',
  filter: 'text-orange-500',
  output: 'text-slate-500',
  geography: 'text-purple-500',
  formatting: 'text-red-500',
  control: 'text-cyan-500',
  people: 'text-indigo-500',
  organization: 'text-amber-600',
  image: 'text-orange-500',
  text: 'text-orange-500',
  work: 'text-slate-600',
} as const

export const categoryBgColors = {
  input: 'bg-blue-100',
  enrichment: 'bg-green-100',
  filter: 'bg-orange-100',
  output: 'bg-slate-100',
  geography: 'bg-purple-100',
  formatting: 'bg-red-100',
  control: 'bg-cyan-100',
  people: 'bg-indigo-100',
  organization: 'bg-amber-100',
  image: 'bg-orange-100',
  text: 'bg-orange-100',
  work: 'bg-slate-100',
} as const

export const geographyTypes = new Set(['GeocodeSimple', 'GeocodeAgent', 'CustomGeographies', 'PlaceExtract', 'PlaceFilter'])
export const imageTypes = new Set(['EmbedImages', 'ImageEnrich'])
export const textTypes = new Set(['Embed', 'LLMEnrich', 'StatsNode'])
export const peopleTypes = new Set(['PeopleExtract'])
export const organizationTypes = new Set(['OrganizationsExtract'])
export const workTypes = new Set(['WorksExtract'])

export type MetadataCategory =
  | 'input'
  | 'enrichment'
  | 'extraction'
  | 'organization'
  | 'output'
  | 'filter'
  | 'review'
  | 'formatting'
  | 'control'
  | 'text'
  | 'embedding'
  | 'work'

export type NodeCategory =
  | 'input'
  | 'enrichment'
  | 'output'
  | 'filter'
  | 'geography'
  | 'formatting'
  | 'control'
  | 'people'
  | 'organization'
  | 'image'
  | 'text'
  | 'work'

export function getNodeCategory(nodeType: string, metadataCategory?: MetadataCategory): NodeCategory {
  if (geographyTypes.has(nodeType)) {
    return 'geography'
  } else if (imageTypes.has(nodeType)) {
    return 'image'
  } else if (textTypes.has(nodeType)) {
    return 'text'
  } else if (peopleTypes.has(nodeType)) {
    return 'people'
  } else if (workTypes.has(nodeType)) {
    return 'work'
  } else if (organizationTypes.has(nodeType)) {
    return 'organization'
  } else if (metadataCategory === 'formatting') {
    return 'formatting'
  } else if (metadataCategory === 'control') {
    return 'control'
  } else if (metadataCategory === 'organization') {
    return 'organization'
  } else if (metadataCategory === 'extraction') {
    return 'people'
  } else if (metadataCategory === 'review') {
    return 'geography'
  } else if (metadataCategory === 'embedding') {
    return 'formatting'
  } else if (metadataCategory) {
    return metadataCategory as NodeCategory
  } else {
    return 'input'
  }
}

export function getNodeIconColor(nodeType: string, metadataCategory?: MetadataCategory): string {
  const category = getNodeCategory(nodeType, metadataCategory)
  return categoryColors[category] || 'text-gray-500'
}

export function getNodeBgColor(nodeType: string, metadataCategory?: MetadataCategory): string {
  const category = getNodeCategory(nodeType, metadataCategory)
  return categoryBgColors[category] || 'bg-gray-100'
}
