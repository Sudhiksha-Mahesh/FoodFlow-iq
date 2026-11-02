import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { useApp } from '../hooks/AppContext'
import { useFilters } from '../hooks/FilterContext'
import { LoadingState, EmptyState, SectionTitle, KpiCard } from '../components/Common'
import GlobalFilterBar from '../components/GlobalFilterBar'
import EChart from '../charts/EChart'
import { IndianRupee, Package, TrendingUp, Percent } from 'lucide-react'

export default function SalesPage() {
  const { currentDataset } = useApp()
  const { filters } = useFilters()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [metric, setMetric] = useState<'revenue' | 'quantity' | 'profit'>('revenue')

  useEffect(() => {
    if (!currentDataset) return
    setLoading(true)
    api.dashboardSales(currentDataset.dataset_id, filters).then(setData).finally(() => setLoading(false))
  }, [currentDataset, filters])

  if (!currentDataset) return <EmptyState title="No dataset loaded" />
  if (loading) return <LoadingState label="Computing sales analytics…" />
  if (!data) return <EmptyState title="No data available" />

  const k = data.kpis || {}
  const products = [...(data.top_products || [])].sort((a: any, b: any) => (b[metric] || 0) - (a[metric] || 0)).slice(0, 10)

  return (
    <div className="space-y-6">
      <SectionTitle>Sales Analytics</SectionTitle>
      <GlobalFilterBar datasetId={currentDataset.dataset_id} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {k.avg_order_value !== undefined && <KpiCard label="Average Order Value" value={`₹${k.avg_order_value}`} icon={IndianRupee} />}
        {k.total_revenue !== undefined && <KpiCard label="Total Revenue" value={`₹${k.total_revenue.toLocaleString()}`} icon={TrendingUp} />}
        {k.total_profit !== undefined && <KpiCard label="Total Profit" value={`₹${k.total_profit.toLocaleString()}`} icon={IndianRupee} />}
        <KpiCard label="Total Orders" value={k.total_orders?.toLocaleString()} icon={Package} />
      </div>

      <div className="grid lg:grid-cols-2 gap-5">
        {data.revenue_by_month && (
          <Card title="Revenue by Month">
            <EChart option={{
              tooltip: { trigger: 'axis' },
              xAxis: { type: 'category', data: data.revenue_by_month.labels },
              yAxis: { type: 'value' },
              grid: { left: 55, right: 20, top: 20, bottom: 30 },
              series: [{ type: 'bar', data: data.revenue_by_month.revenue, color: '#2563eb' }],
            }} />
          </Card>
        )}
        {data.revenue_by_food_category && (
          <Card title="Revenue by Food Category">
            <EChart option={{
              tooltip: { trigger: 'item' },
              series: [{ type: 'pie', radius: '65%', data: data.revenue_by_food_category.map((d: any) => ({ name: d.group, value: d.revenue })) }],
            }} />
          </Card>
        )}
        {data.revenue_by_restaurant && (
          <Card title="Revenue by Restaurant">
            <EChart option={{
              tooltip: {},
              grid: { left: 120, right: 20, top: 10, bottom: 20 },
              xAxis: { type: 'value' },
              yAxis: { type: 'category', data: data.revenue_by_restaurant.slice(0, 10).map((d: any) => d.group).reverse() },
              series: [{ type: 'bar', data: data.revenue_by_restaurant.slice(0, 10).map((d: any) => d.revenue).reverse(), color: '#0ea5e9' }],
            }} />
          </Card>
        )}
        {data.revenue_by_city && (
          <Card title="Revenue by City">
            <EChart option={{
              tooltip: {},
              xAxis: { type: 'category', data: data.revenue_by_city.map((d: any) => d.group) },
              yAxis: { type: 'value' },
              grid: { left: 55, right: 20, top: 20, bottom: 50 },
              series: [{ type: 'bar', data: data.revenue_by_city.map((d: any) => d.revenue), color: '#6366f1' }],
            }} />
          </Card>
        )}
      </div>

      {products.length > 0 && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold">Top 10 Products</h3>
            <div className="flex gap-1 text-xs">
              {(['revenue', 'quantity', 'profit'] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setMetric(m)}
                  className={`px-3 py-1.5 rounded-lg capitalize ${metric === m ? 'bg-brand-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'}`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-200 dark:border-slate-800">
                <th className="py-2">Product</th>
                <th className="py-2 text-right">Revenue</th>
                <th className="py-2 text-right">Quantity</th>
                {products[0]?.profit !== undefined && <th className="py-2 text-right">Profit</th>}
              </tr>
            </thead>
            <tbody>
              {products.map((p: any) => (
                <tr key={p.group} className="border-b border-slate-100 dark:border-slate-800/60">
                  <td className="py-1.5 font-medium">{p.group}</td>
                  <td className="py-1.5 text-right">₹{p.revenue?.toLocaleString()}</td>
                  <td className="py-1.5 text-right">{p.quantity}</td>
                  {p.profit !== undefined && <td className="py-1.5 text-right">₹{p.profit?.toLocaleString()}</td>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card p-4">
      <h3 className="font-medium text-sm mb-2 text-slate-500">{title}</h3>
      {children}
    </div>
  )
}
