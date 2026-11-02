import React, { createContext, useContext, useState } from 'react'
import type { FilterState } from '../types'

interface FilterContextValue {
  filters: FilterState
  setFilters: (f: FilterState) => void
  resetFilters: () => void
}

const FilterContext = createContext<FilterContextValue | null>(null)

export function FilterProvider({ children }: { children: React.ReactNode }) {
  const [filters, setFilters] = useState<FilterState>({})
  return (
    <FilterContext.Provider value={{ filters, setFilters, resetFilters: () => setFilters({}) }}>
      {children}
    </FilterContext.Provider>
  )
}

export function useFilters() {
  const ctx = useContext(FilterContext)
  if (!ctx) throw new Error('useFilters must be used within FilterProvider')
  return ctx
}
