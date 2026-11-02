import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { useApp } from '../hooks/AppContext'
import { useFilters } from '../hooks/FilterContext'
import { LoadingState, EmptyState, UnavailableState, SectionTitle } from '../components/Common'
import GlobalFilterBar from '../components/GlobalFilterBar'
import { Lightbulb } from 'lucide-react'

export default function RestaurantPage() {
  const { currentDataset } = useApp()
  const { filters } = useFilters()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!currentDataset) return
    setLoading(true)
    api.dashboardRestaurants(currentDataset.dataset_id, filters).then(setData).finally(() => setLoading(false))
  }, [currentDataset, filters])

  if (!currentDataset) return <EmptyState title="No dataset loaded" />
  if (loading) return <LoadingState label="Ranking restaurants…" />
  if (!data) return <EmptyState title="No data available" />
  if (!data.available) return <UnavailableState reason={data.reason} />

  return (
    <div className="space-y-6">
      <SectionTitle>Restaurant Analytics</SectionTitle>
      <GlobalFilterBar datasetId={currentDataset.dataset_id} />

      {data.insights?.length > 0 && (
        <div className="card p-4 border-brand-200 dark:border-brand-900 space-y-2">
          {data.insights.map((text: string, i: number) => (
            <div key={i} className="flex items-start gap-2 text-sm">
              <Lightbulb size={16} className="text-amber-500 mt-0.5 shrink-0" />
              <span>{text}</span>
            </div>
          ))}
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-5">
        {data.top_performing && (
          <RestaurantTable title="Top Performing Restaurants" rows={data.top_performing} />
        )}
        {data.underperforming && (
          <RestaurantTable title="Underperforming Restaurants" rows={data.underperforming} />
        )}
        {data.high_revenue_low_rating?.length > 0 && (
          <RestaurantTable title="High Revenue + Low Rating" rows={data.high_revenue_low_rating} />
        )}
        {data.high_rating_low_revenue?.length > 0 && (
          <RestaurantTable title="High Rating + Low Revenue" rows={data.high_rating_low_revenue} />
        )}
      </div>

      <div className="card p-5">
        <h3 className="font-semibold mb-3">All Restaurants</h3>
        <div className="max-h-[420px] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-white dark:bg-slate-900">
              <tr className="text-left text-slate-400 border-b border-slate-200 dark:border-slate-800">
                <th className="py-2">Restaurant</th><th className="py-2 text-right">Orders</th>
                <th className="py-2 text-right">Revenue</th><th className="py-2 text-right">AOV</th>
                <th className="py-2 text-right">Rating</th><th className="py-2 text-right">Delivery Time</th>
                <th className="py-2 text-right">Cancel %</th>
              </tr>
            </thead>
            <tbody>
              {data.restaurants.slice(0, 200).map((r: any) => (
                <tr key={r.restaurant} className="border-b border-slate-100 dark:border-slate-800/60">
                  <td className="py-1.5 font-medium">{r.restaurant}</td>
                  <td className="py-1.5 text-right">{r.orders}</td>
                  <td className="py-1.5 text-right">₹{r.revenue?.toLocaleString?.() ?? r.revenue}</td>
                  <td className="py-1.5 text-right">₹{Math.round(r.avg_order_value || 0)}</td>
                  <td className="py-1.5 text-right">{r.avg_rating}</td>
                  <td className="py-1.5 text-right">{r.avg_delivery_time} min</td>
                  <td className="py-1.5 text-right">{r.cancellation_rate}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function RestaurantTable({ title, rows }: { title: string; rows: any[] }) {
  return (
    <div className="card p-4">
      <h3 className="font-medium text-sm mb-2 text-slate-500">{title}</h3>
      <table className="w-full text-xs">
        <tbody>
          {rows.slice(0, 5).map((r) => (
            <tr key={r.restaurant} className="border-b border-slate-100 dark:border-slate-800/60">
              <td className="py-1.5 font-medium">{r.restaurant}</td>
              <td className="py-1.5 text-right">₹{r.revenue?.toLocaleString?.() ?? r.revenue}</td>
              <td className="py-1.5 text-right">{r.avg_rating ? `${r.avg_rating}★` : ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
