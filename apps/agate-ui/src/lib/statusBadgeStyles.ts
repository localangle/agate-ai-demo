/**
 * Pastel status styles aligned with run summary cards (slate / yellow / emerald / rose / orange).
 * Use with `Badge`/`cn()` so tailwind-merge overrides `badgeVariants` defaults.
 */

export function processedItemStatusBadgeClasses(status: string): string {
  switch (status) {
    case 'pending':
      return 'border-slate-200/80 bg-slate-50 text-slate-700'
    case 'running':
      return 'border-yellow-200/80 bg-yellow-50 text-yellow-800'
    case 'succeeded':
      return 'border-emerald-200/80 bg-emerald-50 text-emerald-800'
    case 'failed':
      return 'border-rose-200/80 bg-rose-50 text-rose-800'
    case 'timed_out':
      return 'border-orange-200/80 bg-orange-50 text-orange-800'
    default:
      return 'border-slate-200/80 bg-slate-50 text-slate-700'
  }
}

export function runStatusBadgeClasses(status: string): string {
  switch (status) {
    case 'pending':
      return 'border-slate-200/80 bg-slate-50 text-slate-700'
    case 'running':
      return 'border-yellow-200/80 bg-yellow-50 text-yellow-800'
    case 'completed':
      return 'border-emerald-200/80 bg-emerald-50 text-emerald-800'
    case 'completed_with_errors':
      return 'border-orange-200/80 bg-orange-50 text-orange-800'
    default:
      return 'border-slate-200/80 bg-slate-50 text-slate-700'
  }
}

/** Small status dot (legacy panels). */
export function runStatusDotClasses(status: string): string {
  switch (status) {
    case 'pending':
      return 'bg-slate-400'
    case 'running':
      return 'bg-yellow-400'
    case 'completed':
      return 'bg-emerald-500'
    case 'completed_with_errors':
      return 'bg-orange-500'
    default:
      return 'bg-slate-400'
  }
}

