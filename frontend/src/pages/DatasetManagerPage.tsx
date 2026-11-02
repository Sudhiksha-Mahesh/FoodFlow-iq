import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../hooks/AppContext'
import { api } from '../services/api'
import { SectionTitle, EmptyState } from '../components/Common'
import { Trash2, CheckCircle2, UploadCloud } from 'lucide-react'

export default function DatasetManagerPage() {
  const { datasets, currentDataset, setCurrentDataset, refreshDatasets, pushToast } = useApp()
  const navigate = useNavigate()
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleDelete = async (id: string) => {
    setDeletingId(id)
    try {
      await api.deleteDataset(id)
      if (currentDataset?.dataset_id === id) setCurrentDataset(null)
      await refreshDatasets()
      pushToast('Dataset deleted', 'success')
    } catch (e: any) {
      pushToast(e.message || 'Delete failed', 'error')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <SectionTitle
        action={<button className="btn-primary flex items-center gap-2" onClick={() => navigate('/upload')}><UploadCloud size={16} /> Upload Dataset</button>}
      >
        Dataset Manager
      </SectionTitle>

      {datasets.length === 0 ? (
        <EmptyState title="No datasets yet" description="Upload a CSV or load the sample dataset to get started." />
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40">
                <th className="py-3 px-4">Dataset Name</th>
                <th className="py-3 px-4">Uploaded</th>
                <th className="py-3 px-4 text-right">Rows</th>
                <th className="py-3 px-4 text-right">Columns</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4"></th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((d) => (
                <tr key={d.dataset_id} className="border-b border-slate-100 dark:border-slate-800/60">
                  <td className="py-3 px-4 font-medium flex items-center gap-2">
                    {d.name} {d.is_sample && <span className="badge bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">Sample</span>}
                  </td>
                  <td className="py-3 px-4 text-slate-400">{d.uploaded_at ? new Date(d.uploaded_at).toLocaleString() : '—'}</td>
                  <td className="py-3 px-4 text-right">{d.rows.toLocaleString()}</td>
                  <td className="py-3 px-4 text-right">{d.columns}</td>
                  <td className="py-3 px-4 capitalize">{d.status}</td>
                  <td className="py-3 px-4 flex items-center gap-2 justify-end">
                    {currentDataset?.dataset_id === d.dataset_id ? (
                      <span className="flex items-center gap-1 text-emerald-600 text-xs"><CheckCircle2 size={14} /> Active</span>
                    ) : (
                      <button className="btn-secondary text-xs" onClick={() => setCurrentDataset(d)}>Open Dashboard</button>
                    )}
                    <button
                      className="p-2 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/30 text-rose-500 disabled:opacity-40"
                      disabled={deletingId === d.dataset_id}
                      onClick={() => handleDelete(d.dataset_id)}
                    >
                      <Trash2 size={15} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
