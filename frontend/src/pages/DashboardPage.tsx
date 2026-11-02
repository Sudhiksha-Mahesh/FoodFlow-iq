import { useEffect, useState } from 'react'
import { IndianRupee, ShoppingBag, Users, Percent, TrendingUp, Clock, XCircle, Star } from 'lucide-react'
import { api } from '../services/api'
import { useApp } from '../hooks/AppContext'
import { useFilters } from '../hooks/FilterContext'
import { LoadingState, EmptyState, KpiCard, SectionTitle } from '../components/Common'
import GlobalFilterBar from '../components/GlobalFilterBar'
import EChart from '../charts/EChart'

export default function DashboardPage() {
  const { currentDataset } = useApp()
  const { filters } = useFilters()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!currentDataset) return
    setLoading(true)
    api.dashboardOverview(currentDataset.dataset_id, filters).then(setData).finally(() => setLoading(false))
  }, [currentDataset, filters])

  if (!currentDataset) return <EmptyState title="No dataset loaded" description="Upload a dataset to see the executive dashboard." />
  if (loading) return <LoadingState label="Building your executive dashboard…" />
  if (!data) return <EmptyState title="No data available" />

  const k = data.kpis || {}

  return (
    <div className="space-y-6">
      <SectionTitle>Executive Dashboard</SectionTitle>
      <GlobalFilterBar datasetId={currentDataset.dataset_id} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {k.total_revenue !== undefined && <KpiCard label="Total Revenue" value={`₹${k.total_revenue.toLocaleString()}`} icon={IndianRupee} />}
        <KpiCard label="Total Orders" value={k.total_orders?.toLocaleString()} icon={ShoppingBag} />
        {k.total_customers !== undefined && <KpiCard label="Total Customers" value={k.total_customers.toLocaleString()} icon={Users} />}
        {k.avg_order_value !== undefined && <KpiCard label="Avg Order Value" value={`₹${k.avg_order_value}`} icon={TrendingUp} />}
        {k.total_profit !== undefined && <KpiCard label="Total Profit" value={`₹${k.total_profit.toLocaleString()}`} icon={IndianRupee} />}
        {k.avg_delivery_time !== undefined && <KpiCard label="Avg Delivery Time" value={`${k.avg_delivery_time} min`} icon={Clock} />}
        {k.cancellation_rate !== undefined && <KpiCard label="Cancellation Rate" value={`${k.cancellation_rate}%`} icon={XCircle} />}
        {k.avg_rating !== undefined && <KpiCard label="Avg Rating" value={`${k.avg_rating} / 5`} icon={Star} />}
      </div>

      <div className="grid lg:grid-cols-2 gap-5">
        {data.revenue_by_month && (
          <ChartCard title="Revenue Trend by Month">
            <EChart option={{
              tooltip: { trigger: 'axis' },
              xAxis: { type: 'category', data: data.revenue_by_month.labels },
              yAxis: { type: 'value' },
              grid: { left: 50, right: 20, top: 20, bottom: 30 },
              series: [{ type: 'line', data: data.revenue_by_month.revenue, smooth: true, areaStyle: {}, color: '#2563eb' }],
            }} />
          </ChartCard>
        )}
        {data.revenue_by_city && (
          <ChartCard title="Orders by City">
            <EChart option={{
              tooltip: {},
              xAxis: { type: 'category', data: data.revenue_by_city.map((d: any) => d.group) },
              yAxis: { type: 'value' },
              grid: { left: 50, right: 20, top: 20, bottom: 60 },
              series: [{ type: 'bar', data: data.revenue_by_city.map((d: any) => d.orders), color: '#0ea5e9' }],
            }} />
          </ChartCard>
        )}
        {data.revenue_by_cuisine && (
          <ChartCard title="Revenue by Cuisine">
            <EChart option={{
              tooltip: { trigger: 'item' },
              series: [{
                type: 'pie', radius: ['40%', '70%'],
                data: data.revenue_by_cuisine.map((d: any) => ({ name: d.group, value: d.revenue })),
              }],
            }} />
          </ChartCard>
        )}
        {data.revenue_by_restaurant && (
          <ChartCard title="Revenue by Restaurant (Top 15)">
            <EChart option={{
              tooltip: {},
              grid: { left: 120, right: 20, top: 10, bottom: 20 },
              xAxis: { type: 'value' },
              yAxis: { type: 'category', data: data.revenue_by_restaurant.slice(0, 15).map((d: any) => d.group).reverse() },
              series: [{ type: 'bar', data: data.revenue_by_restaurant.slice(0, 15).map((d: any) => d.revenue).reverse(), color: '#6366f1' }],
            }} />
          </ChartCard>
        )}
        {data.orders_by_status && (
          <ChartCard title="Orders by Status">
            <EChart option={{
              tooltip: { trigger: 'item' },
              series: [{ type: 'pie', radius: '65%', data: data.orders_by_status.map((d: any) => ({ name: d.group, value: d.orders })) }],
            }} />
          </ChartCard>
        )}
        {data.orders_by_payment_method && (
          <ChartCard title="Payment Method Distribution">
            <EChart option={{
              tooltip: { trigger: 'item' },
              series: [{ type: 'pie', radius: ['40%', '70%'], data: data.orders_by_payment_method.map((d: any) => ({ name: d.group, value: d.orders })) }],
            }} />
          </ChartCard>
        )}
      </div>
    </div>
  )
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card p-4">
      <h3 className="font-medium text-sm mb-2 text-slate-500">{title}</h3>
      {children}
    </div>
  )
}
