import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { useApp } from '../hooks/AppContext'
import { useFilters } from '../hooks/FilterContext'
import { LoadingState, EmptyState, UnavailableState, SectionTitle } from '../components/Common'
import { Lightbulb, ArrowRight, Settings2 } from 'lucide-react'

export default function RecommendationsPage() {
  const { currentDataset } = useApp()
  const { filters } = useFilters()
  const [recs, setRecs] = useState<any[] | null>(null)
  const [loadingRecs, setLoadingRecs] = useState(true)

  const [minSupport, setMinSupport] = useState(0.01)
  const [minConfidence, setMinConfidence] = useState(0.15)
  const [minLift, setMinLift] = useState(1.0)
  const [apriori, setApriori] = useState<any>(null)
  const [loadingApriori, setLoadingApriori] = useState(true)

  useEffect(() => {
    if (!currentDataset) return
    setLoadingRecs(true)
    api.recommendations(currentDataset.dataset_id, filters).then((r) => setRecs(r.recommendations)).finally(() => setLoadingRecs(false))
  }, [currentDataset, filters])

  useEffect(() => {
    if (!currentDataset) return
    setLoadingApriori(true)
    api.apriori(currentDataset.dataset_id, { min_support: minSupport, min_confidence: minConfidence, min_lift: minLift })
      .then(setApriori).finally(() => setLoadingApriori(false))
  }, [currentDataset, minSupport, minConfidence, minLift])

  if (!currentDataset) return <EmptyState title="No dataset loaded" />

  return (
    <div className="space-y-6">
      <SectionTitle>Business Recommendations</SectionTitle>

      {loadingRecs ? <LoadingState label="Generating data-driven recommendations…" /> : (
        <div className="space-y-3">
          {recs?.map((r, i) => (
            <div key={i} className="card p-4 flex items-start gap-3">
              <div className="w-9 h-9 rounded-lg bg-amber-50 dark:bg-amber-900/30 flex items-center justify-center text-amber-600 shrink-0">
                <Lightbulb size={18} />
              </div>
              <div>
                <div className="text-[11px] uppercase tracking-wide font-semibold text-brand-600 mb-0.5">
                  {r.type} · {r.category}
                </div>
                <div className="text-sm">{r.text}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      <SectionTitle
        action={
          <div className="flex items-center gap-2 text-xs">
            <Settings2 size={14} className="text-slate-400" />
            <label className="flex items-center gap-1">Support <input type="number" step="0.005" className="input w-20 py-1" value={minSupport} onChange={(e) => setMinSupport(Number(e.target.value))} /></label>
            <label className="flex items-center gap-1">Confidence <input type="number" step="0.05" className="input w-20 py-1" value={minConfidence} onChange={(e) => setMinConfidence(Number(e.target.value))} /></label>
            <label className="flex items-center gap-1">Lift <input type="number" step="0.1" className="input w-20 py-1" value={minLift} onChange={(e) => setMinLift(Number(e.target.value))} /></label>
          </div>
        }
      >
        Product Recommendations (Association Rules)
      </SectionTitle>

      {loadingApriori ? <LoadingState label="Mining basket associations…" /> : !apriori ? (
        <EmptyState title="No data" />
      ) : !apriori.available ? (
        <UnavailableState reason={apriori.reason} />
      ) : (
        <div className="card p-5">
          <p className="text-xs text-slate-400 mb-3">{apriori.orders_analyzed} multi-item orders analysed</p>
          <div className="grid md:grid-cols-2 gap-3">
            {apriori.rules.map((r: any, i: number) => (
              <div key={i} className="rounded-lg border border-slate-200 dark:border-slate-800 p-3 text-sm">
                <div className="flex items-center gap-2 flex-wrap">
                  {r.antecedents.map((a: string) => <span key={a} className="badge bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">{a}</span>)}
                  <ArrowRight size={14} className="text-slate-400" />
                  {r.consequents.map((c: string) => <span key={c} className="badge bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300">{c}</span>)}
                </div>
                <div className="text-xs text-slate-400 mt-2 flex gap-3">
                  <span>Support: {(r.support * 100).toFixed(1)}%</span>
                  <span>Confidence: {(r.confidence * 100).toFixed(1)}%</span>
                  <span>Lift: {r.lift.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
