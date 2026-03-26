export type MetadataCategory =
  | 'input'
  | 'enrichment'
  | 'output'
  | 'filter'
  | 'geography'
  | 'formatting'
  | 'control'
  | 'people'
  | 'organization'
  | 'work'
  | 'image'
  | 'text'
  | 'extraction'
  | string

export const categoryColors: Record<string, string> = {
  input: 'text-blue-600',
  enrichment: 'text-emerald-600',
  output: 'text-slate-600',
  filter: 'text-amber-600',
  geography: 'text-purple-600',
  formatting: 'text-zinc-600',
  control: 'text-indigo-600',
  people: 'text-indigo-600',
  organization: 'text-amber-700',
  work: 'text-teal-700',
  image: 'text-fuchsia-700',
  text: 'text-orange-600',
}

export const categoryBgColors: Record<string, string> = {
  input: 'bg-blue-100',
  enrichment: 'bg-emerald-100',
  output: 'bg-slate-100',
  filter: 'bg-amber-100',
  geography: 'bg-purple-100',
  formatting: 'bg-zinc-100',
  control: 'bg-indigo-100',
  people: 'bg-indigo-100',
  organization: 'bg-amber-100',
  work: 'bg-teal-100',
  image: 'bg-fuchsia-100',
  text: 'bg-orange-100',
}

const typeCategoryOverrides: Record<string, string> = {
  PlaceExtract: 'geography',
  GeocodeAgent: 'geography',
  PlaceFilter: 'filter',
  PeopleExtract: 'people',
  OrganizationsExtract: 'organization',
  WorksExtract: 'work',
  ImageEnrich: 'image',
  EmbedImages: 'image',
  StatsNode: 'text',
}

export function getNodeCategory(nodeType: string, metadataCategory?: MetadataCategory): string {
  if (typeCategoryOverrides[nodeType]) {
    return typeCategoryOverrides[nodeType]
  }
  if (metadataCategory === 'extraction') {
    return 'enrichment'
  }
  return metadataCategory || 'enrichment'
}

