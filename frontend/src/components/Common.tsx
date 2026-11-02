import { LucideIcon, Loader2, AlertTriangle, Inbox } from 'lucide-react'
import type { ReactNode } from 'react'

export function KpiCard({
  label, value, icon: Icon, sub, accent = 'brand',
}: { label: string; value: string | number; icon?: LucideIcon; sub?: string; accent?: string }) {
  return (
    <div className="card p-4 flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide">{label}</span>
        {Icon && <Icon size={16} className={`text-${accent}-600`} />}
      </div>
      <span className="text-2xl font-semibold tracking-tight">{value}</span>
      {sub && <span className="text-xs text-slate-400">{sub}</span>}
    </div>
  )
}

export function LoadingState({ label = 'Crunching the numbers…' }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-slate-400 gap-3">
      <Loader2 className="animate-spin" size={28} />
      <span className="text-sm">{label}</span>
    </div>
  )
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center gap-2 text-slate-400">
      <Inbox size={32} />
      <span className="font-medium text-slate-500 dark:text-slate-300">{title}</span>
      {description && <span className="text-sm max-w-md">{description}</span>}
    </div>
  )
}

export function UnavailableState({ reason }: { reason?: string }) {
  return (
    <div className="card flex flex-col items-center justify-center py-16 text-center gap-2 px-6">
      <AlertTriangle size={28} className="text-amber-500" />
      <span className="font-medium">This analysis isn't available for the current dataset</span>
      {reason && <span className="text-sm text-slate-400 max-w-md">{reason}</span>}
    </div>
  )
}

export function StatusBadge({ status }: { status: 'available' | 'partial' | 'unavailable' }) {
  const map: Record<string, string> = {
    available: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
    partial: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
    unavailable: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300',
  }
  const symbol = status === 'available' ? '✓' : status === 'partial' ? '⚠' : '✗'
  return <span className={`badge ${map[status]}`}>{symbol} {status === 'available' ? 'Available' : status === 'partial' ? 'Partial' : 'Unavailable'}</span>
}

export function SectionTitle({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex items-center justify-between mb-3">
      <h2 className="text-lg font-semibold">{children}</h2>
      {action}
    </div>
  )
}
