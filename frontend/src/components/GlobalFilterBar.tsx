import { useEffect, useState } from 'react'
import { Filter, X } from 'lucide-react'
import { api } from '../services/api'
import { useFilters } from '../hooks/FilterContext'
import type { AvailableFilters } from '../types'

const LABELS: Record<string, string> = {
  city: 'City',
  restaurant: 'Restaurant',
  cuisine: 'Cuisine',
  order_status: 'Order Status',
  payment_method: 'Payment Method',
  customer_type: 'Customer Type',
  food_category: 'Food Category',
}

export default function GlobalFilterBar({ datasetId }: { datasetId: string }) {
  const { filters, setFilters, resetFilters } = useFilters()
  const [available, setAvailable] = useState<AvailableFilters>({})

  useEffect(() => {
    if (!datasetId) return
    api.getFilters(datasetId).then(setAvailable).catch(() => setAvailable({}))
  }, [datasetId])

  const keys = Object.keys(available).filter((k) => k !== 'date_range')
  const activeCount = Object.values(filters).filter((v) => (Array.isArray(v) ? v.length > 0 : !!v)).length

  if (keys.length === 0 && !available.date_range) return null

  return (
    <div className="card p-3 mb-4 flex flex-wrap items-center gap-3">
      <div className="flex items-center gap-1.5 text-sm font-medium text-slate-500">
        <Filter size={15} /> Filters
      </div>

      {available.date_range && (
        <div className="flex items-center gap-1.5">
          <input
            type="date"
            className="input text-xs py-1"
            min={available.date_range[0]}
            max={available.date_range[1]}
            value={filters.date_from || ''}
            onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
          />
          <span className="text-slate-400 text-xs">to</span>
          <input
            type="date"
            className="input text-xs py-1"
            min={available.date_range[0]}
            max={available.date_range[1]}
            value={filters.date_to || ''}
            onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
          />
        </div>
      )}

      {keys.map((key) => (
        <select
          key={key}
          className="input text-xs py-1"
          value={(filters as any)[key]?.[0] || ''}
          onChange={(e) =>
            setFilters({ ...filters, [key]: e.target.value ? [e.target.value] : undefined })
          }
        >
          <option value="">{LABELS[key] || key}</option>
          {available[key as keyof AvailableFilters]?.map((v: string) => (
            <option key={v} value={v}>{v}</option>
          ))}
        </select>
      ))}

      {activeCount > 0 && (
        <button onClick={resetFilters} className="flex items-center gap-1 text-xs text-rose-500 hover:underline ml-auto">
          <X size={13} /> Clear filters ({activeCount})
        </button>
      )}
    </div>
  )
}
