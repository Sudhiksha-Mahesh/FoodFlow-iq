import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { useApp } from '../hooks/AppContext'
import { LoadingState, EmptyState, SectionTitle } from '../components/Common'
import type { DatasetProfile } from '../types'
import { PlayCircle } from 'lucide-react'

export default function DataPreparationPage() {
  const { currentDataset, pushToast } = useApp()
  const [profile, setProfile] = useState<DatasetProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [missingStrategy, setMissingStrategy] = useState('auto')
  const [removeDuplicates, setRemoveDuplicates] = useState(true)
  const [handleInvalid, setHandleInvalid] = useState(true)
  const [cleanResult, setCleanResult] = useState<any>(null)
  const [cleaning, setCleaning] = useState(false)

  useEffect(() => {
    if (!currentDataset) return
    setLoading(true)
    api.getProfile(currentDataset.dataset_id).then(setProfile).finally(() => setLoading(false))
  }, [currentDataset])

  if (!currentDataset) return <EmptyState title="No dataset loaded" description="Upload a dataset first." />
  if (loading) return <LoadingState label="Profiling dataset…" />
  if (!profile) return <EmptyState title="Could not load dataset profile" />

  const runClean = async () => {
    setCleaning(true)
    try {
      const res = await api.cleanDataset(currentDataset.dataset_id, {
        missing_strategy: missingStrategy,
        remove_duplicates: removeDuplicates,
        handle_invalid_numeric: handleInvalid,
      })
      setCleanResult(res)
      pushToast('ETL cleaning complete — derived fields generated', 'success')
    } catch (e: any) {
      pushToast(e.message || 'Cleaning failed', 'error')
    } finally {
      setCleaning(false)
    }
  }

  return (
    <div className="space-y-6">
      <SectionTitle>Data Preparation</SectionTitle>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <MiniStat label="Rows" value={profile.rows.toLocaleString()} />
        <MiniStat label="Columns" value={profile.columns} />
        <MiniStat label="Numerical" value={profile.numeric_columns} />
        <MiniStat label="Categorical" value={profile.categorical_columns} />
        <MiniStat label="Date" value={profile.date_columns} />
      </div>

      <div className="card p-5">
        <h3 className="font-semibold mb-3">Data Quality</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-200 dark:border-slate-800">
                <th className="py-2 pr-4">Column</th>
                <th className="py-2 pr-4">Type</th>
                <th className="py-2 pr-4 text-right">Missing</th>
                <th className="py-2 pr-4 text-right">Unique</th>
                <th className="py-2 pr-4 text-right">Outliers</th>
                <th className="py-2 pr-4">Issues</th>
              </tr>
            </thead>
            <tbody>
              {profile.column_profiles.map((c) => (
                <tr key={c.column} className="border-b border-slate-100 dark:border-slate-800/60">
                  <td className="py-1.5 pr-4 font-medium">{c.column}</td>
                  <td className="py-1.5 pr-4 text-slate-400">{c.type}</td>
                  <td className="py-1.5 pr-4 text-right">{c.missing}</td>
                  <td className="py-1.5 pr-4 text-right">{c.unique}</td>
                  <td className="py-1.5 pr-4 text-right">{c.outliers}</td>
                  <td className="py-1.5 pr-4">
                    {c.issues[0] === 'None' ? (
                      <span className="text-emerald-500 text-xs">None</span>
                    ) : (
                      c.issues.map((i) => (
                        <span key={i} className="badge bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300 mr-1">{i}</span>
                      ))
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card p-5">
        <h3 className="font-semibold mb-4">Cleaning Strategies</h3>
        <div className="grid sm:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Missing values</label>
            <select className="input w-full" value={missingStrategy} onChange={(e) => setMissingStrategy(e.target.value)}>
              <option value="auto">Auto Handle</option>
              <option value="fill_mean">Fill with Mean</option>
              <option value="fill_median">Fill with Median</option>
              <option value="fill_mode">Fill with Mode</option>
              <option value="drop_rows">Drop Rows</option>
              <option value="leave">Leave As-Is</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Duplicates</label>
            <select className="input w-full" value={removeDuplicates ? '1' : '0'} onChange={(e) => setRemoveDuplicates(e.target.value === '1')}>
              <option value="1">Remove duplicates</option>
              <option value="0">Keep duplicates</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Invalid numeric values</label>
            <select className="input w-full" value={handleInvalid ? '1' : '0'} onChange={(e) => setHandleInvalid(e.target.value === '1')}>
              <option value="1">Detect &amp; Handle</option>
              <option value="0">Leave As-Is</option>
            </select>
          </div>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={runClean} disabled={cleaning}>
          <PlayCircle size={16} /> {cleaning ? 'Running ETL…' : 'Run Cleaning & Generate Derived Fields'}
        </button>

        {cleanResult && (
          <div className="mt-5 grid sm:grid-cols-2 gap-4">
            <div className="rounded-lg border border-slate-200 dark:border-slate-800 p-4">
              <div className="text-xs font-medium text-slate-400 mb-2">BEFORE</div>
              <Row label="Rows" value={cleanResult.before.rows} />
              <Row label="Missing values" value={cleanResult.before.missing} />
              <Row label="Duplicate rows" value={cleanResult.before.duplicates} />
            </div>
            <div className="rounded-lg border border-emerald-200 dark:border-emerald-900 p-4">
              <div className="text-xs font-medium text-emerald-600 mb-2">AFTER</div>
              <Row label="Rows" value={cleanResult.after.rows} />
              <Row label="Missing values" value={cleanResult.after.missing} />
              <Row label="Duplicate rows" value={cleanResult.after.duplicates} />
            </div>
            <div className="sm:col-span-2 text-sm text-slate-500">
              <span className="font-medium">Derived fields generated:</span> {cleanResult.derived_columns.join(', ') || 'none'}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function MiniStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card p-4 text-center">
      <div className="text-xl font-bold">{value}</div>
      <div className="text-xs text-slate-400">{label}</div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between text-sm py-0.5">
      <span className="text-slate-500">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  )
}
