import { expect, test, vi, beforeEach } from 'vitest'
import { api, fetchFromAPI } from '@/lib/api'

// Mock global fetch
global.fetch = vi.fn()

beforeEach(() => {
  vi.resetAllMocks()
})

test('fetchFromAPI makes correct call', async () => {
  const mockResponse = { data: 'test' };
  (global.fetch as any).mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(mockResponse),
  })

  const result = await fetchFromAPI('/test')
  
  expect(fetch).toHaveBeenCalledWith(
    expect.stringContaining('/api/test'),
    expect.objectContaining({
      headers: { 'Content-Type': 'application/json' }
    })
  )
  expect(result).toEqual(mockResponse)
})

test('api.getRepos calls correct endpoint', async () => {
  (global.fetch as any).mockResolvedValue({
    ok: true,
    json: () => Promise.resolve([]),
  })

  await api.getRepos()
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/repos'), expect.anything())
})

test('handles non-json response', async () => {
  (global.fetch as any).mockResolvedValue({
    ok: true,
    json: () => Promise.reject(new Error('Invalid JSON')),
  })

  const result = await fetchFromAPI('/test')
  expect(result).toBeNull()
})

test('throws error on non-ok response', async () => {
  (global.fetch as any).mockResolvedValue({
    ok: false,
    statusText: 'Not Found',
  })

  await expect(fetchFromAPI('/test')).rejects.toThrow('API call failed: Not Found')
})
