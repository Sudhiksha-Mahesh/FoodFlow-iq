import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Database, TrendingUp, Users, Store, Truck,
  LineChart, UserX, Sparkles, FolderCog, UtensilsCrossed,
} from 'lucide-react'

const items = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/data-preparation', label: 'Data Preparation', icon: Database },
  { to: '/sales', label: 'Sales Analytics', icon: TrendingUp },
  { to: '/customers', label: 'Customer Analytics', icon: Users },
  { to: '/restaurants', label: 'Restaurant Analytics', icon: Store },
  { to: '/delivery', label: 'Delivery Analytics', icon: Truck },
  { to: '/forecast', label: 'Demand Forecast', icon: LineChart },
  { to: '/churn', label: 'Churn Prediction', icon: UserX },
  { to: '/recommendations', label: 'Recommendations', icon: Sparkles },
  { to: '/datasets', label: 'Dataset Manager', icon: FolderCog },
]

export default function Sidebar() {
  return (
    <aside className="w-64 shrink-0 h-screen sticky top-0 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white">
          <UtensilsCrossed size={18} />
        </div>
        <div>
          <div className="font-bold leading-none">FoodFlow IQ</div>
          <div className="text-[10px] text-slate-400 leading-none mt-0.5">Delivery BI &amp; Analytics</div>
        </div>
      </div>
      <nav className="flex-1 overflow-y-auto px-2 py-2 space-y-0.5">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-4 py-3 text-[11px] text-slate-400 border-t border-slate-200 dark:border-slate-800">
        From Every Order to Smarter Delivery Decisions.
      </div>
    </aside>
  )
}
