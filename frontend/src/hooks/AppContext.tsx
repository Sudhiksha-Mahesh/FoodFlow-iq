import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { DatasetSummary } from '../types'
import { api } from '../services/api'

interface Toast { id: number; message: string; type: 'success' | 'error' | 'info' }

interface AppContextValue {
  currentDataset: DatasetSummary | null
  setCurrentDataset: (d: DatasetSummary | null) => void
  datasets: DatasetSummary[]
  refreshDatasets: () => Promise<void>
  theme: 'light' | 'dark'
  toggleTheme: () => void
  toasts: Toast[]
  pushToast: (message: string, type?: Toast['type']) => void
}

const AppContext = createContext<AppContextValue | null>(null)

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [currentDataset, setCurrentDatasetState] = useState<DatasetSummary | null>(null)
  const [datasets, setDatasets] = useState<DatasetSummary[]>([])
  const [theme, setTheme] = useState<'light' | 'dark'>(
    (localStorage.getItem('ffiq-theme') as 'light' | 'dark') || 'light'
  )
  const [toasts, setToasts] = useState<Toast[]>([])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('ffiq-theme', theme)
  }, [theme])

  const refreshDatasets = useCallback(async () => {
    try {
      const list = await api.listDatasets()
      setDatasets(list)
    } catch {
      /* backend not reachable yet */
    }
  }, [])

  useEffect(() => {
    refreshDatasets()
  }, [refreshDatasets])

  const setCurrentDataset = (d: DatasetSummary | null) => {
    setCurrentDatasetState(d)
    if (d) localStorage.setItem('ffiq-dataset-id', d.dataset_id)
  }

  const pushToast = (message: string, type: Toast['type'] = 'info') => {
    const id = Date.now() + Math.random()
    setToasts((t) => [...t, { id, message, type }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000)
  }

  return (
    <AppContext.Provider
      value={{
        currentDataset,
        setCurrentDataset,
        datasets,
        refreshDatasets,
        theme,
        toggleTheme: () => setTheme((t) => (t === 'light' ? 'dark' : 'light')),
        toasts,
        pushToast,
      }}
    >
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within AppProvider')
  return ctx
}
