import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, APIError } from '@/api/client'

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

function mockFetch(...responses: (Response | Error)[]) {
  const fetch = vi.fn(async (_request: Request) => {
    const next = responses.shift()
    if (!next || next instanceof Error) throw next ?? new Error('sin respuesta')
    return next
  })
  vi.stubGlobal('fetch', fetch)
  return fetch
}

afterEach(() => vi.unstubAllGlobals())

describe('API client', () => {
  it('sends JSON with cookies and the latest rotated CSRF token on mutations only', async () => {
    const fetch = mockFetch(
      json({ user: null, csrf_token: 'first' }),
      json({ user: { recurso_id: 1 }, csrf_token: 'second' }),
      json([]),
      new Response(null, { status: 204 }),
    )
    await api.session()
    await api.login({ recurso_nombre: 'admin', password: 'x' })
    await api.roles()
    expect(await api.deleteRole(3)).toBeUndefined()

    const [session, login, roles, remove] = fetch.mock.calls.map(([request]) => request)
    expect(session!.headers.get('X-CSRF-Token')).toBeNull()
    expect(login!.headers.get('X-CSRF-Token')).toBe('first')
    expect(login!.headers.get('Content-Type')).toContain('application/json')
    expect(login!.credentials).toBe('same-origin')
    expect(roles!.headers.get('X-CSRF-Token')).toBeNull()
    expect(remove!.method).toBe('DELETE')
    expect(remove!.headers.get('X-CSRF-Token')).toBe('second')
    expect(await remove!.text()).toBe('{}')
  })

  it('maps the error contract to APIError without retrying', async () => {
    const fetch = mockFetch(json({ error: { code: 'csrf_invalid', message: 'La sesión venció.' } }, 400))
    const error = await api.saveRole({ rol_descripcion: 'X' }).catch((e) => e)
    expect(error).toBeInstanceOf(APIError)
    expect([error.status, error.code, error.message]).toEqual([400, 'csrf_invalid', 'La sesión venció.'])
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('reports network failures and invalid responses in Spanish', async () => {
    mockFetch(new TypeError('Failed to fetch'))
    await expect(api.roles()).rejects.toMatchObject({ code: 'network_error', status: 0 })
    mockFetch(new Response('<html>', { status: 200, headers: { 'Content-Type': 'application/json' } }))
    await expect(api.roles()).rejects.toMatchObject({ code: 'invalid_response' })
  })
})
