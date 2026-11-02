import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { useApp } from '../hooks/AppContext'
import { LoadingState, EmptyState, UnavailableState, SectionTitle } from '../components/Common'
import EChart from '../charts/EChart'
import { CalendarClock, TrendingUp, Trophy } from 'lucide-react'

export default function ForecastPage() {
  const { currentDataset } = useApp()
  const [horizon, setHorizon] = useState(7)
  const [groupBy, setGroupBy] = useState<string>('')
  const [groupValue, setGroupValue] = useState<string>('')
  const [filterOptions, setFilterOptions] = useState<any>({})
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!currentDataset) return
    api.getFilters(currentDataset.dataset_id).then(setFilterOptions).catch(() => {})
  }, [currentDataset])

  useEffect(() => {
    if (!currentDataset) return
    setLoading(true)
    api.forecast(currentDataset.dataset_id, {
      horizon,
      group_by: groupBy || null,
      group_value: groupValue || null,
    }).then(setData).finally(() => setLoading(false))
  }, [currentDataset, horizon, groupBy, groupValue])

  if (!currentDataset) return <EmptyState title="No dataset loaded" />

  const groupOptions: Record<string, string> = { city: 'city', restaurant: 'restaurant', cuisine: 'cuisine' }

  return (
    <div className="space-y-6">
      <SectionTitle>Demand Forecasting</SectionTitle>

      <div className="card p-4 flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-slate-400">Scope:</span>
          <select className="input" value={groupBy} onChange={(e) => { setGroupBy(e.target.value); setGroupValue('') }}>
            <option value="">Overall</option>
            {Object.entries(groupOptions).map(([k, label]) => (
              filterOptions[k] ? <option key={k} value={k}>{label}</option> : null
            ))}
          </select>
          {groupBy && filterOptions[groupBy] && (
            <select className="input" value={groupValue} onChange={(e) => setGroupValue(e.target.value)}>
              <option value="">Select {groupBy}…</option>
              {filterOptions[groupBy].map((v: string) => <option key={v} value={v}>{v}</option>)}
            </select>
          )}
        </div>
        <div className="flex items-center gap-2 text-sm ml-auto">
          <span className="text-slate-400">Forecast Horizon:</span>
          {[7, 14, 30].map((h) => (
            <button key={h} onClick={() => setHorizon(h)} className={`px-3 py-1.5 rounded-lg text-xs ${horizon === h ? 'bg-brand-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'}`}>
              {h} days
            </button>
          ))}
        </div>
      </div>

      {loading ? <LoadingState label="Training and comparing forecasting models…" /> : !data ? (
        <EmptyState title="No forecast available" />
      ) : !data.available ? (
        <UnavailableState reason={data.reason} />
      ) : (
        <>
          <div className="grid sm:grid-cols-3 gap-4">
            <StatCard icon={TrendingUp} label="Forecasted Orders Tomorrow" value={data.forecast_tomorrow ?? '—'} />
            <StatCard icon={CalendarClock} label="Expected Peak Day" value={data.expected_peak_day ?? '—'} />
            <StatCard icon={CalendarClock} label="Expected Peak Hour" value={data.expected_peak_hour ?? '—'} />
          </div>

          <div className="card p-4">
            <h3 className="font-medium text-sm mb-2 text-slate-500">Historical vs Forecasted Orders</h3>
            <EChart height={360} option={{
              tooltip: { trigger: 'axis' },
              legend: { data: ['Historical', 'Forecast'] },
              xAxis: { type: 'category', data: [...data.historical.dates, ...data.forecast.dates] },
              yAxis: { type: 'value' },
              grid: { left: 50, right: 20, top: 40, bottom: 30 },
              series: [
                { name: 'Historical', type: 'line', data: data.historical.orders, color: '#2563eb' },
                {
                  name: 'Forecast', type: 'line', color: '#f59e0b', lineStyle: { type: 'dashed' },
                  data: [...Array(data.historical.orders.length - 1).fill(null), data.historical.orders.at(-1), ...data.forecast.orders],
                },
              ],
            }} />
          </div>

          <div className="card p-5">
            <h3 className="font-semibold mb-3 flex items-center gap-2"><Trophy size={16} className="text-amber-500" /> Model Comparison</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-400 border-b border-slate-200 dark:border-slate-800">
                  <th className="py-2">Model</th><th className="py-2 text-right">MAE</th><th className="py-2 text-right">MSE</th><th className="py-2 text-right">RMSE</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(data.model_comparison).map(([name, m]: any) => (
                  <tr key={name} className={`border-b border-slate-100 dark:border-slate-800/60 ${name === data.best_model ? 'bg-emerald-50 dark:bg-emerald-950/20' : ''}`}>
                    <td className="py-1.5 font-medium capitalize">{name.replace(/_/g, ' ')} {name === data.best_model && <span className="badge bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300 ml-2">Best</span>}</td>
                    <td className="py-1.5 text-right">{m.metrics?.mae ?? '—'}</td>
                    <td className="py-1.5 text-right">{m.metrics?.mse ?? '—'}</td>
                    <td className="py-1.5 text-right">{m.metrics?.rmse ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

function StatCard({ icon: Icon, label, value }: { icon: any; label: string; value: any }) {
  return (
    <div className="card p-4 flex items-center gap-3">
      <div className="w-10 h-10 rounded-lg bg-brand-50 dark:bg-brand-900/30 flex items-center justify-center text-brand-600"><Icon size={18} /></div>
      <div>
        <div className="text-xs text-slate-400">{label}</div>
        <div className="text-lg font-semibold">{value}</div>
      </div>
    </div>
  )
}
