import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { UploadCloud, FileCheck2, FileWarning, Sparkles } from 'lucide-react'
import { api } from '../services/api'
import { useApp } from '../hooks/AppContext'
import type { UploadResponse } from '../types'
import { StatusBadge } from '../components/Common'

export default function UploadPage() {
  const [dragOver, setDragOver] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<UploadResponse | null>(null)
  const { setCurrentDataset, refreshDatasets, pushToast } = useApp()
  const navigate = useNavigate()

  const handleFile = useCallback(async (file: File) => {
    setError(null)
    setLoading(true)
    setResult(null)
    try {
      const res: UploadResponse = await api.uploadDataset(file)
      setResult(res)
      setCurrentDataset(res)
      await refreshDatasets()
      pushToast(`${file.name} uploaded and profiled successfully`, 'success')
    } catch (e: any) {
      setError(e.message || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }, [setCurrentDataset, refreshDatasets, pushToast])

  const handleSample = async () => {
    setError(null)
    setLoading(true)
    setResult(null)
    try {
      const res: UploadResponse = await api.loadSample()
      setResult(res)
      setCurrentDataset(res)
      await refreshDatasets()
      pushToast('Sample dataset loaded', 'success')
    } catch (e: any) {
      setError(e.message || 'Failed to load sample dataset')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-10 px-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-1">FoodFlow IQ</h1>
        <p className="text-slate-500">From Every Order to Smarter Delivery Decisions.</p>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          const file = e.dataTransfer.files?.[0]
          if (file) handleFile(file)
        }}
        className={`card border-2 border-dashed p-12 flex flex-col items-center justify-center text-center transition-colors ${
          dragOver ? 'border-brand-500 bg-brand-50 dark:bg-brand-950/20' : 'border-slate-300 dark:border-slate-700'
        }`}
      >
        <UploadCloud size={40} className="text-brand-500 mb-3" />
        <h3 className="font-semibold text-lg mb-1">Upload your food-delivery dataset</h3>
        <p className="text-sm text-slate-400 mb-4">Drag &amp; drop a .csv file here, or browse to select one</p>
        <label className="btn-primary cursor-pointer">
          Browse Files
          <input
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
        </label>
        <button onClick={handleSample} className="mt-4 text-sm text-brand-600 hover:underline flex items-center gap-1">
          <Sparkles size={14} /> Or try it instantly with the sample dataset
        </button>
      </div>

      {loading && (
        <div className="text-center mt-6 text-slate-400 text-sm">Validating, profiling and analysing your dataset…</div>
      )}

      {error && (
        <div className="card mt-6 p-4 border-rose-300 bg-rose-50 dark:bg-rose-950/20 text-rose-700 dark:text-rose-300 text-sm whitespace-pre-line">
          <div className="flex items-center gap-2 font-medium mb-1"><FileWarning size={16} /> Dataset cannot be analysed</div>
          {error}
        </div>
      )}

      {result && (
        <div className="mt-8 space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <Stat label="Records" value={result.rows.toLocaleString()} />
            <Stat label="Columns" value={result.columns} />
            <Stat label="Data Quality Score" value={`${result.profile.data_quality_score}%`} />
            <Stat label="Missing Values" value={result.profile.missing_values.toLocaleString()} />
            <Stat label="Duplicate Rows" value={result.profile.duplicate_rows.toLocaleString()} />
          </div>

          <div className="card p-5">
            <h3 className="font-semibold mb-3 flex items-center gap-2"><FileCheck2 size={16} /> Dataset Compatibility</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
              {Object.entries(result.compatibility).map(([label, v]) => (
                <div key={label} className="flex items-center gap-2">
                  <span className={v.available ? 'text-emerald-500' : 'text-amber-500'}>{v.available ? '✓' : '⚠'}</span>
                  <span className={v.available ? '' : 'text-slate-400'}>{label} {v.available ? 'detected' : 'unavailable'}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card p-5">
            <h3 className="font-semibold mb-3">Available Analytics Modules</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
              {Object.entries(result.module_availability).map(([mod, v]) => (
                <div key={mod} className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 py-1.5">
                  <span>{mod}</span>
                  <div className="flex items-center gap-2">
                    {v.note && <span className="text-xs text-slate-400">{v.note}</span>}
                    <StatusBadge status={v.status} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end">
            <button className="btn-primary" onClick={() => navigate('/data-preparation')}>
              Continue to Data Preparation →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card p-4 text-center">
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs text-slate-400 mt-1">{label}</div>
    </div>
  )
}
