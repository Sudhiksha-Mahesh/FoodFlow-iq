import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { useApp } from '../hooks/AppContext'
import { useFilters } from '../hooks/FilterContext'
import { LoadingState, EmptyState, UnavailableState, SectionTitle, KpiCard } from '../components/Common'
import GlobalFilterBar from '../components/GlobalFilterBar'
import EChart from '../charts/EChart'
import { Users, UserPlus, Repeat, Wallet } from 'lucide-react'

const SEGMENT_COLORS: Record<string, string> = {
  Champions: '#16a34a',
  'Loyal Customers': '#2563eb',
  'Potential Loyalists': '#0ea5e9',
  'New Customers': '#8b5cf6',
  'At Risk': '#f59e0b',
  'Cannot Lose Them': '#ef4444',
  'Lost Customers': '#94a3b8',
}

export default function CustomerPage() {
  const { currentDataset } = useApp()
  const { filters } = useFilters()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [selectedSegment, setSelectedSegment] = useState<string | null>(null)

  useEffect(() => {
    if (!currentDataset) return
    setLoading(true)
    api.dashboardCustomers(currentDataset.dataset_id, filters).then(setData).finally(() => setLoading(false))
  }, [currentDataset, filters])

  if (!currentDataset) return <EmptyState title="No dataset loaded" />
  if (loading) return <LoadingState label="Segmenting customers…" />
  if (!data) return <EmptyState title="No data available" />
  if (!data.available) return <UnavailableState reason={data.reason} />

  const table = (data.customer_table || []).filter((c: any) => !selectedSegment || c.segment === selectedSegment)

  return (
    <div className="space-y-6">
      <SectionTitle>Customer Analytics</SectionTitle>
      <GlobalFilterBar datasetId={currentDataset.dataset_id} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Total Customers" value={data.total_customers?.toLocaleString()} icon={Users} />
        {data.new_customers !== undefined && <KpiCard label="New Customers" value={data.new_customers} icon={UserPlus} />}
        {data.returning_customers !== undefined && <KpiCard label="Returning Customers" value={data.returning_customers} icon={Repeat} />}
        {data.avg_customer_spend !== undefined && <KpiCard label="Avg Customer Spend" value={`₹${data.avg_customer_spend}`} icon={Wallet} />}
      </div>

      {data.segments && (
        <div className="card p-5">
          <h3 className="font-semibold mb-1">RFM Customer Segments</h3>
          <p className="text-xs text-slate-400 mb-3">Click a segment slice to filter the customer table below.</p>
          <div className="grid md:grid-cols-2 gap-4 items-center">
            <EChart height={280} option={{
              tooltip: { trigger: 'item' },
              series: [{
                type: 'pie', radius: ['35%', '70%'],
                data: data.segments.map((s: any) => ({ name: s.segment, value: s.count, itemStyle: { color: SEGMENT_COLORS[s.segment] } })),
              }],
            }} />
            <div className="flex flex-wrap gap-2">
              {data.segments.map((s: any) => (
                <button
                  key={s.segment}
                  onClick={() => setSelectedSegment(selectedSegment === s.segment ? null : s.segment)}
                  className={`badge border ${selectedSegment === s.segment ? 'ring-2 ring-brand-500' : ''}`}
                  style={{ borderColor: SEGMENT_COLORS[s.segment], color: SEGMENT_COLORS[s.segment] }}
                >
                  {s.segment} · {s.count}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {data.top_customers && (
        <div className="card p-5">
          <h3 className="font-semibold mb-3">Top Customers by Spend</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-200 dark:border-slate-800">
                <th className="py-2">Customer ID</th><th className="py-2 text-right">Orders</th>
                <th className="py-2 text-right">Total Spend</th><th className="py-2 text-right">Recency (days)</th><th className="py-2">Segment</th>
              </tr>
            </thead>
            <tbody>
              {data.top_customers.map((c: any) => (
                <tr key={c.customer_id} className="border-b border-slate-100 dark:border-slate-800/60">
                  <td className="py-1.5 font-medium">{c.customer_id}</td>
                  <td className="py-1.5 text-right">{c.frequency}</td>
                  <td className="py-1.5 text-right">₹{c.monetary?.toLocaleString()}</td>
                  <td className="py-1.5 text-right">{c.recency}</td>
                  <td className="py-1.5">{c.segment}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {table.length > 0 && (
        <div className="card p-5">
          <h3 className="font-semibold mb-3">
            Customer Table {selectedSegment && <span className="text-brand-600">— {selectedSegment}</span>}
          </h3>
          <div className="max-h-[420px] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-white dark:bg-slate-900">
                <tr className="text-left text-slate-400 border-b border-slate-200 dark:border-slate-800">
                  <th className="py-2">Customer ID</th><th className="py-2 text-right">Orders</th>
                  <th className="py-2 text-right">Spending</th><th className="py-2 text-right">Avg Order Value</th>
                  <th className="py-2">Last Order</th><th className="py-2 text-right">Recency</th><th className="py-2">Segment</th>
                </tr>
              </thead>
              <tbody>
                {table.slice(0, 200).map((c: any) => (
                  <tr key={c.customer_id} className="border-b border-slate-100 dark:border-slate-800/60">
                    <td className="py-1.5 font-medium">{c.customer_id}</td>
                    <td className="py-1.5 text-right">{c.orders}</td>
                    <td className="py-1.5 text-right">₹{c.total_spending?.toLocaleString()}</td>
                    <td className="py-1.5 text-right">₹{Math.round(c.avg_order_value || 0)}</td>
                    <td className="py-1.5">{c.last_order_date}</td>
                    <td className="py-1.5 text-right">{c.recency}</td>
                    <td className="py-1.5">{c.segment}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
