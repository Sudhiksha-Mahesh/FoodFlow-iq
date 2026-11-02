import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

interface Point { lat: number; lon: number; orders: number; revenue?: number }

export default function LocationMap({ points }: { points: Point[] }) {
  if (!points.length) return null
  const center: [number, number] = [points[0].lat, points[0].lon]
  const maxOrders = Math.max(...points.map((p) => p.orders), 1)

  return (
    <div className="rounded-lg overflow-hidden" style={{ height: 360 }}>
      <MapContainer center={center} zoom={11} style={{ height: '100%', width: '100%' }} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {points.map((p, i) => (
          <CircleMarker
            key={i}
            center={[p.lat, p.lon]}
            radius={4 + (p.orders / maxOrders) * 16}
            pathOptions={{ color: '#2563eb', fillColor: '#3b82f6', fillOpacity: 0.5 }}
          >
            <Tooltip>
              {p.orders} orders{p.revenue !== undefined ? ` · ₹${p.revenue.toLocaleString()}` : ''}
            </Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  )
}
