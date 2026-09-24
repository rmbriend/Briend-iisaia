import { describe, expect, it } from 'vitest'
import type { RouteLocationNormalized } from 'vue-router'
import type { User } from '@/api/client'
import { redirectFor } from '@/router'

const to = (name: string, admin = false) => ({ name, meta: { admin } }) as unknown as RouteLocationNormalized
const user = (overrides: Partial<User> = {}): User => ({
  recurso_id: 1, recurso_nombre: 'ana', es_admin: false, debe_cambiar_password: false, ...overrides,
})

describe('navigation rules', () => {
  it('sends anonymous visitors to login', () => {
    expect(redirectFor(null, to('projects'))).toBe('login')
    expect(redirectFor(null, to('login'))).toBeNull()
  })
  it('forces a pending password change before anything else', () => {
    expect(redirectFor(user({ debe_cambiar_password: true }), to('projects'))).toBe('password')
    expect(redirectFor(user({ debe_cambiar_password: true }), to('password'))).toBeNull()
  })
  it('keeps signed-in users away from login and plain users away from admin pages', () => {
    expect(redirectFor(user(), to('login'))).toBe('projects')
    expect(redirectFor(user(), to('resources', true))).toBe('projects')
    expect(redirectFor(user({ es_admin: true }), to('resources', true))).toBeNull()
  })
})
