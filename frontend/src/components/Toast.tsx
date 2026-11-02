import { useApp } from '../hooks/AppContext'
import { CheckCircle2, XCircle, Info } from 'lucide-react'

export default function ToastContainer() {
  const { toasts } = useApp()
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`card px-4 py-3 flex items-center gap-2 shadow-lg min-w-[240px] animate-in fade-in slide-in-from-bottom-2 ${
            t.type === 'error' ? 'border-rose-300' : t.type === 'success' ? 'border-emerald-300' : ''
          }`}
        >
          {t.type === 'success' && <CheckCircle2 size={18} className="text-emerald-600" />}
          {t.type === 'error' && <XCircle size={18} className="text-rose-600" />}
          {t.type === 'info' && <Info size={18} className="text-brand-600" />}
          <span className="text-sm">{t.message}</span>
        </div>
      ))}
    </div>
  )
}
