export interface ColumnProfile {
  column: string
  type: string
  missing: number
  missing_pct: number
  unique: number
  outliers: number
  issues: string[]
}

export interface DatasetProfile {
  rows: number
  columns: number
  numeric_columns: number
  categorical_columns: number
  date_columns: number
  missing_values: number
  duplicate_rows: number
  data_quality_score: number
  column_profiles: ColumnProfile[]
}

export interface ModuleStatus {
  status: 'available' | 'partial' | 'unavailable'
  label: string
  note?: string | null
}

export interface DatasetSummary {
  dataset_id: string
  name: string
  rows: number
  columns: number
  status?: string
  uploaded_at?: string
  is_sample?: boolean
}

export interface UploadResponse extends DatasetSummary {
  profile: DatasetProfile
  compatibility: Record<string, { available: boolean }>
  module_availability: Record<string, ModuleStatus>
}

export interface FilterState {
  date_from?: string
  date_to?: string
  city?: string[]
  restaurant?: string[]
  cuisine?: string[]
  order_status?: string[]
  payment_method?: string[]
  customer_type?: string[]
  food_category?: string[]
}

export interface AvailableFilters {
  date_range?: [string, string]
  city?: string[]
  restaurant?: string[]
  cuisine?: string[]
  order_status?: string[]
  payment_method?: string[]
  customer_type?: string[]
  food_category?: string[]
}
