import React from 'react'
import {
  FileText,
  Tag,
  Zap,
  Database,
  Brain,
  Filter,
  MapPin,
  Package,
  Search,
  Sparkles,
  Braces,
  FileJson,
  Image,
  Eye,
  Plug,
  User,
  Building2,
  BookOpen,
  BarChart,
  type LucideIcon,
} from 'lucide-react'
import { nodeMetadata } from '@/nodes/registry'
import { categoryBgColors, categoryColors, getNodeCategory, type MetadataCategory } from '@/lib/nodeColors'

const iconMap: Record<string, LucideIcon> = {
  FileText,
  Tag,
  Zap,
  Database,
  Brain,
  Filter,
  MapPin,
  Package,
  Search,
  Sparkles,
  Braces,
  FileJson,
  Image,
  Eye,
  Plug,
  User,
  Building2,
  BookOpen,
  BarChart,
}

function getMetadata(nodeType: string) {
  return nodeMetadata.find((n) => n.type === nodeType)
}

export function getNodeIcon(nodeType: string, className = 'h-4 w-4') {
  const meta = getMetadata(nodeType)
  const category = getNodeCategory(nodeType, meta?.category as MetadataCategory)
  const iconColorClass = categoryColors[category] || 'text-slate-600'
  const iconName = meta?.icon || 'FileText'
  const Icon = iconMap[iconName] || FileText
  return <Icon className={`${className} ${iconColorClass}`} />
}

export function getNodeLabel(nodeType: string) {
  const meta = getMetadata(nodeType)
  return meta?.label || nodeType
}

export function getNodeBgColor(nodeType: string) {
  const meta = getMetadata(nodeType)
  const category = getNodeCategory(nodeType, meta?.category as MetadataCategory)
  return categoryBgColors[category] || 'bg-slate-100'
}

