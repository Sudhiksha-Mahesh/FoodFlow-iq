const BASE = '/api'

async function request(input: string, init?: RequestInit) {
  try {
    return await fetch(`${BASE}${input}`, init)
  } catch {
    throw new Error(
      'Cannot reach the FoodFlow IQ backend. Start it from the backend folder with: uvicorn app.main:app --reload --port 8000'
    )
  }
}

async function handle(res: Response) {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  return res.json()
}

export const api = {
  health: () => request('/health').then(handle),

  uploadDataset: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request('/datasets/upload', { method: 'POST', body: form }).then(handle)
  },
  loadSample: () => request('/datasets/load-sample', { method: 'POST' }).then(handle),
  listDatasets: () => request('/datasets').then(handle),
  getDataset: (id: string) => request(`/datasets/${id}`).then(handle),
  deleteDataset: (id: string) => request(`/datasets/${id}`, { method: 'DELETE' }).then(handle),
  getProfile: (id: string) => request(`/datasets/${id}/profile`).then(handle),
  cleanDataset: (id: string, options: any) =>
    request(`/datasets/${id}/clean`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options),
    }).then(handle),

  getFilters: (id: string) => request(`/datasets/${id}/filters`).then(handle),

  post: (path: string, body: any = {}) =>
    request(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(handle),

  dashboardOverview: (id: string, filters: any) => api.post(`/datasets/${id}/dashboard/overview`, filters),
  dashboardSales: (id: string, filters: any) => api.post(`/datasets/${id}/dashboard/sales`, filters),
  dashboardCustomers: (id: string, filters: any) => api.post(`/datasets/${id}/dashboard/customers`, filters),
  dashboardRestaurants: (id: string, filters: any) => api.post(`/datasets/${id}/dashboard/restaurants`, filters),
  dashboardDelivery: (id: string, filters: any) => api.post(`/datasets/${id}/dashboard/delivery`, filters),
  dashboardTime: (id: string, filters: any) => api.post(`/datasets/${id}/dashboard/time`, filters),
  dashboardLocations: (id: string, filters: any) => api.post(`/datasets/${id}/dashboard/locations`, filters),
  insights: (id: string, filters: any) => api.post(`/datasets/${id}/insights`, filters),

  rfm: (id: string, filters: any) => api.post(`/datasets/${id}/rfm`, filters),
  forecast: (id: string, body: any) => api.post(`/datasets/${id}/forecast`, body),
  churn: (id: string, body: any) => api.post(`/datasets/${id}/churn`, body),
  apriori: (id: string, body: any) => api.post(`/datasets/${id}/apriori`, body),
  recommendations: (id: string, filters: any) => api.post(`/datasets/${id}/recommendations`, filters),
}
