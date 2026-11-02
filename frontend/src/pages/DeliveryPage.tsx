import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { useApp } from '../hooks/AppContext'
import { useFilters } from '../hooks/FilterContext'
import { LoadingState, EmptyState, UnavailableState, SectionTitle, KpiCard } from '../components/Common'
import GlobalFilterBar from '../components/GlobalFilterBar'
import EChart from '../charts/EChart'
import LocationMap from '../components/LocationMap'
import { Clock, AlertOctagon, XCircle, Gauge, MapPin } from 'lucide-react'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export default function DeliveryPage() {
  const { currentDataset } = useApp()
  const { filters } = useFilters()
  const [data, setData] = useState<any>(null)
  const [timeData, setTimeData] = useState<any>(null)
  const [locationData, setLocationData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!currentDataset) return
    setLoading(true)
    Promise.all([
      api.dashboardDelivery(currentDataset.dataset_id, filters),
      api.dashboardTime(currentDataset.dataset_id, filters),
      api.dashboardLocations(currentDataset.dataset_id, filters),
    ]).then(([d, t, l]) => { setData(d); setTimeData(t); setLocationData(l) }).finally(() => setLoading(false))
  }, [currentDataset, filters])

  if (!currentDataset) return <EmptyState title="No dataset loaded" />
  if (loading) return <LoadingState label="Analysing delivery operations…" />
  if (!data) return <EmptyState title="No data available" />
  if (!data.available) return <UnavailableState reason={data.reason} />

  const heat = timeData?.heatmap_day_hour
  const heatData = heat ? heat.map((h: any) => [h.order_hour, DAYS.indexOf(h.day_of_week), h.orders]).filter((d: any) => d[1] >= 0) : []
  const maxOrders = heat ? Math.max(...heat.map((h: any) => h.orders), 1) : 1

  return (
    <div className="space-y-6">
      <SectionTitle>Delivery &amp; Operations Analytics</SectionTitle>
      <GlobalFilterBar datasetId={currentDataset.dataset_id} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Avg Delivery Time" value={`${data.avg_delivery_time} min`} icon={Clock} />
        {data.avg_delivery_delay !== undefined && <KpiCard label="Avg Delivery Delay" value={`${data.avg_delivery_delay} min`} icon={AlertOctagon} />}
        {data.late_delivery_pct !== undefined && <KpiCard label="Late Delivery %" value={`${data.late_delivery_pct}%`} icon={Gauge} />}
        {data.cancellation_rate !== undefined && <KpiCard label="Cancellation Rate" value={`${data.cancellation_rate}%`} icon={XCircle} />}
      </div>

      <div className="grid lg:grid-cols-2 gap-5">
        {data.delivery_time_by_hour && (
          <Card title="Delivery Time by Hour">
            <EChart option={{
              tooltip: {},
              xAxis: { type: 'category', data: data.delivery_time_by_hour.map((d: any) => `${d.order_hour}:00`) },
              yAxis: { type: 'value', name: 'min' },
              grid: { left: 45, right: 20, top: 20, bottom: 30 },
              series: [{ type: 'line', data: data.delivery_time_by_hour.map((d: any) => d.avg_delivery_time), smooth: true, color: '#f59e0b' }],
            }} />
          </Card>
        )}
        {data.delivery_time_by_city && (
          <Card title="Delivery Time by City">
            <EChart option={{
              tooltip: {},
              xAxis: { type: 'category', data: data.delivery_time_by_city.map((d: any) => d.city) },
              yAxis: { type: 'value', name: 'min' },
              grid: { left: 45, right: 20, top: 20, bottom: 50 },
              series: [{ type: 'bar', data: data.delivery_time_by_city.map((d: any) => d.avg_delivery_time), color: '#0ea5e9' }],
            }} />
          </Card>
        )}
        {data.distance_vs_time && (
          <Card title="Distance vs Delivery Time">
            <EChart option={{
              tooltip: {},
              xAxis: { type: 'value', name: 'Distance (km)' },
              yAxis: { type: 'value', name: 'Time (min)' },
              grid: { left: 55, right: 20, top: 20, bottom: 40 },
              series: [{ type: 'scatter', symbolSize: 5, data: data.distance_vs_time.map((d: any) => [d.distance, d.time]), color: '#6366f1' }],
            }} />
          </Card>
        )}
        {data.delivery_partner_ranking && (
          <Card title="Delivery Partner Ranking (by Orders)">
            <EChart option={{
              tooltip: {},
              grid: { left: 70, right: 20, top: 10, bottom: 20 },
              xAxis: { type: 'value' },
              yAxis: { type: 'category', data: data.delivery_partner_ranking.slice(0, 10).map((d: any) => d.partner_id).reverse() },
              series: [{ type: 'bar', data: data.delivery_partner_ranking.slice(0, 10).map((d: any) => d.orders).reverse(), color: '#16a34a' }],
            }} />
          </Card>
        )}
      </div>

      {heatData.length > 0 && (
        <div className="card p-4">
          <h3 className="font-medium text-sm mb-2 text-slate-500">Order Volume Heatmap — Day × Hour</h3>
          <EChart height={340} option={{
            tooltip: { position: 'top' },
            grid: { left: 80, right: 20, top: 20, bottom: 40 },
            xAxis: { type: 'category', data: Array.from({ length: 24 }, (_, i) => `${i}:00`), splitArea: { show: true } },
            yAxis: { type: 'category', data: DAYS, splitArea: { show: true } },
            visualMap: { min: 0, max: maxOrders, calculable: true, orient: 'horizontal', left: 'center', bottom: 0 },
            series: [{ type: 'heatmap', data: heatData, emphasis: { itemStyle: { shadowBlur: 10 } } }],
          }} />
        </div>
      )}

      {locationData?.available && (
        <div className="card p-4">
          <h3 className="font-medium text-sm mb-2 text-slate-500 flex items-center gap-2"><MapPin size={15} /> Order Density Map</h3>
          {locationData.has_coordinates ? (
            <LocationMap points={locationData.points} />
          ) : (
            <div className="text-xs text-slate-400 mb-2">
              No latitude/longitude columns detected — showing city-level order counts instead of a map.
              <div className="mt-2 flex flex-wrap gap-2">
                {locationData.city_breakdown?.slice(0, 10).map((c: any) => (
                  <span key={c[Object.keys(c)[0]]} className="badge bg-slate-100 dark:bg-slate-800">
                    {Object.values(c)[0] as string}: {c.orders}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {timeData?.available && (
        <div className="grid sm:grid-cols-2 gap-4 text-sm">
          {timeData.peak_hour !== null && timeData.peak_hour !== undefined && (
            <div className="card p-4">Peak ordering hour: <span className="font-semibold">{timeData.peak_hour}:00</span></div>
          )}
          {timeData.peak_day && (
            <div className="card p-4">Peak ordering day: <span className="font-semibold">{timeData.peak_day}</span></div>
          )}
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
