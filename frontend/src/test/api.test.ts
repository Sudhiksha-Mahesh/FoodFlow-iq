import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api } from '../services/api'

describe('api service', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('parses a successful JSON response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'ok' }),
    }) as any

    const result = await api.health()
    expect(result).toEqual({ status: 'ok' })
    expect(fetch).toHaveBeenCalledWith('/api/health')
  })

  it('surfaces the backend "detail" message on error responses', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      statusText: 'Bad Request',
      json: async () => ({ detail: 'No date column and no numeric revenue/amount column were detected.' }),
    }) as any

    await expect(api.getDataset('ds_123')).rejects.toThrow(
      'No date column and no numeric revenue/amount column were detected.'
    )
  })

  it('sends filter bodies as JSON on dashboard endpoints', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ kpis: {} }) }) as any
    await api.dashboardSales('ds_1', { city: ['Chennai'] })
    const [url, options] = (fetch as any).mock.calls[0]
    expect(url).toBe('/api/datasets/ds_1/dashboard/sales')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ city: ['Chennai'] })
  })
})
