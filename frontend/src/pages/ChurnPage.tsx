import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { useApp } from '../hooks/AppContext'
import { LoadingState, EmptyState, UnavailableState, SectionTitle, KpiCard } from '../components/Common'
import { AlertTriangle, ShieldCheck, ShieldAlert, ShieldX } from 'lucide-react'

const RISK_COLOR: Record<string, string> = {
  High: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300',
  Medium: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  Low: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
}

export default function ChurnPage() {
  const { currentDataset } = useApp()
  const [threshold, setThreshold] = useState(60)
  const [lowMax, setLowMax] = useState(30)
  const [medMax, setMedMax] = useState(60)
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<any>(null)
  const [sortDesc, setSortDesc] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    if (!currentDataset) return
    setLoading(true)
    api.churn(currentDataset.dataset_id, { churn_threshold_days: threshold, low_max: lowMax, medium_max: medMax })
      .then(setData).finally(() => setLoading(false))
  }, [currentDataset, threshold, lowMax, medMax])

  if (!currentDataset) return <EmptyState title="No dataset loaded" />

  let customers = data?.customers ? [...data.customers] : []
  if (search) customers = customers.filter((c: any) => c.customer_id.toLowerCase().includes(search.toLowerCase()))
  customers.sort((a: any, b: any) => sortDesc ? b.churn_probability - a.churn_probability : a.churn_probability - b.churn_probability)

  return (
    <div className="space-y-6">
      <SectionTitle>Customer Churn Prediction</SectionTitle>

      <div className="card p-4 space-y-3">
        <p className="text-sm text-slate-500">
          <strong>Churn definition:</strong> a customer is considered churned if they have not placed an order within the
          configured period, relative to the observation period.
        </p>
        <div className="flex flex-wrap gap-6 items-center text-sm">
          <label className="flex items-center gap-2">Churn Threshold:
            <input type="number" className="input w-20" value={threshold} min={7} onChange={(e) => setThreshold(Number(e.target.value))} /> days
          </label>
          <label className="flex items-center gap-2">Low/Medium boundary:
            <input type="number" className="input w-16" value={lowMax} onChange={(e) => setLowMax(Number(e.target.value))} />%
          </label>
          <label className="flex items-center gap-2">Medium/High boundary:
            <input type="number" className="input w-16" value={medMax} onChange={(e) => setMedMax(Number(e.target.value))} />%
          </label>
        </div>
      </div>

      {loading ? <LoadingState label="Training churn models (Logistic Regression, Decision Tree, Random Forest)…" /> : !data ? (
        <EmptyState title="No churn data available" />
      ) : !data.available ? (
        <UnavailableState reason={data.reason} />
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard label="High Risk Customers" value={data.summary.high_risk} icon={ShieldX} accent="rose" />
            <KpiCard label="Medium Risk Customers" value={data.summary.medium_risk} icon={ShieldAlert} accent="amber" />
            <KpiCard label="Low Risk Customers" value={data.summary.low_risk} icon={ShieldCheck} accent="emerald" />
            <KpiCard label="Avg Churn Probability" value={`${data.summary.avg_churn_probability}%`} icon={AlertTriangle} />
          </div>

          <div className="card p-5">
            <h3 className="font-semibold mb-3">Model Comparison</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-400 border-b border-slate-200 dark:border-slate-800">
                  <th className="py-2">Model</th><th className="py-2 text-right">Accuracy</th><th className="py-2 text-right">Precision</th>
                  <th className="py-2 text-right">Recall</th><th className="py-2 text-right">F1</th><th className="py-2 text-right">ROC-AUC</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(data.model_comparison).map(([name, m]: any) => (
                  <tr key={name} className={`border-b border-slate-100 dark:border-slate-800/60 ${name === data.best_model ? 'bg-emerald-50 dark:bg-emerald-950/20' : ''}`}>
                    <td className="py-1.5 font-medium capitalize">{name.replace(/_/g, ' ')} {name === data.best_model && <span className="badge bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300 ml-2">Best</span>}</td>
                    <td className="py-1.5 text-right">{m.metrics.accuracy}</td>
                    <td className="py-1.5 text-right">{m.metrics.precision}</td>
                    <td className="py-1.5 text-right">{m.metrics.recall}</td>
                    <td className="py-1.5 text-right">{m.metrics.f1_score}</td>
                    <td className="py-1.5 text-right">{m.metrics.roc_auc ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card p-5">
            <div className="flex items-center justify-between mb-3 gap-3 flex-wrap">
              <h3 className="font-semibold">Churn Risk Table</h3>
              <div className="flex gap-2">
                <input className="input text-sm" placeholder="Search customer ID…" value={search} onChange={(e) => setSearch(e.target.value)} />
                <button className="btn-secondary text-xs" onClick={() => setSortDesc((s) => !s)}>
                  Sort by risk {sortDesc ? '↓' : '↑'}
                </button>
              </div>
            </div>
            <div className="max-h-[420px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-white dark:bg-slate-900">
                  <tr className="text-left text-slate-400 border-b border-slate-200 dark:border-slate-800">
                    <th className="py-2">Customer</th><th className="py-2 text-right">Orders</th><th className="py-2 text-right">Total Spending</th>
                    <th className="py-2 text-right">Last Order</th><th className="py-2 text-right">Churn Probability</th><th className="py-2">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {customers.slice(0, 300).map((c: any) => (
                    <tr key={c.customer_id} className="border-b border-slate-100 dark:border-slate-800/60 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/40" onClick={() => setSelected(c)}>
                      <td className="py-1.5 font-medium">{c.customer_id}</td>
                      <td className="py-1.5 text-right">{c.orders}</td>
                      <td className="py-1.5 text-right">₹{c.total_spending?.toLocaleString()}</td>
                      <td className="py-1.5 text-right">{c.days_since_last_order}d ago</td>
                      <td className="py-1.5 text-right">{c.churn_probability}%</td>
                      <td className="py-1.5"><span className={`badge ${RISK_COLOR[c.risk]}`}>{c.risk}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {selected && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setSelected(null)}>
          <div className="card p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold mb-3">Customer {selected.customer_id}</h3>
            <div className="space-y-1 text-sm mb-4">
              <Row label="Total Orders" value={selected.orders} />
              <Row label="Total Spending" value={`₹${selected.total_spending?.toLocaleString()}`} />
              <Row label="Last Order" value={`${selected.days_since_last_order} days ago`} />
            </div>
            <div className={`rounded-lg p-3 mb-3 ${RISK_COLOR[selected.risk]}`}>
              <div className="text-sm">Churn Probability: <strong>{selected.churn_probability}%</strong></div>
              <div className="text-sm">Risk: <strong>{selected.risk.toUpperCase()}</strong></div>
            </div>
            <div className="text-sm">
              <strong>Suggested Action:</strong> {
                selected.risk === 'High' ? 'Launch a targeted retention campaign with personalized offers.' :
                selected.risk === 'Medium' ? 'Send a re-engagement discount or reminder notification.' :
                'Continue standard engagement — no urgent action needed.'
              }
            </div>
            <button className="btn-secondary mt-4 w-full" onClick={() => setSelected(null)}>Close</button>
          </div>
        </div>
      )}
    </div>
  )
}

function Row({ label, value }: { label: string; value: any }) {
  return <div className="flex justify-between"><span className="text-slate-400">{label}</span><span className="font-medium">{value}</span></div>
}
