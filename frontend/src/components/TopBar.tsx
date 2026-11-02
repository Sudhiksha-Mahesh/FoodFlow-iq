import { useNavigate } from 'react-router-dom'
import { Sun, Moon, ChevronDown, Database } from 'lucide-react'
import { useState } from 'react'
import { useApp } from '../hooks/AppContext'

export default function TopBar() {
  const { currentDataset, datasets, setCurrentDataset, theme, toggleTheme } = useApp()
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  return (
    <header className="h-16 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur sticky top-0 z-40 flex items-center justify-between px-6">
      <div className="relative">
        <button
          onClick={() => setOpen((o) => !o)}
          className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          <Database size={15} className="text-slate-400" />
          <span className="text-slate-400">Current Dataset:</span>
          <span className="font-medium">{currentDataset ? currentDataset.name : 'No dataset loaded'}</span>
          {datasets.length > 1 && <ChevronDown size={14} />}
        </button>
        {open && datasets.length > 0 && (
          <div className="absolute mt-1 left-0 card p-1 w-72 z-50">
            {datasets.map((d) => (
              <button
                key={d.dataset_id}
                onClick={() => {
                  setCurrentDataset(d)
                  setOpen(false)
                }}
                className="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-slate-100 dark:hover:bg-slate-800 flex flex-col"
              >
                <span className="font-medium">{d.name}</span>
                <span className="text-xs text-slate-400">{d.rows} rows · {d.columns} cols</span>
              </button>
            ))}
            <button
              onClick={() => { setOpen(false); navigate('/upload') }}
              className="w-full text-left px-3 py-2 rounded-lg text-sm text-brand-600 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              + Upload new dataset
            </button>
          </div>
        )}
      </div>

      <button
        onClick={toggleTheme}
        className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
        title="Toggle dark mode"
      >
        {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
      </button>
    </header>
  )
}
