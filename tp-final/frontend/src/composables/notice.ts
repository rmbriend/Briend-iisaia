import { reactive } from 'vue'
import type { Router } from 'vue-router'
import { APIError } from '@/api/client'
import { useSessionStore } from '@/stores/session'

export const notice = reactive({ text: '', kind: 'danger' as 'danger' | 'success' })

export function showNotice(text: string, kind: 'danger' | 'success' = 'danger') {
  notice.text = text
  notice.kind = kind
}

/**
 * Shared reaction to API errors (same rules as the previous frontend): an expired session goes
 * to login, a pending password change goes to its form, an invalid CSRF token is refreshed —
 * a mutation is never retried automatically — and the message is always shown.
 */
export async function handleError(error: unknown, router: Router, { login = false } = {}) {
  const session = useSessionStore()
  if (error instanceof APIError) {
    if (error.status === 401 && !login) {
      session.forget()
      await router.replace({ name: 'login' })
    } else if (error.code === 'password_change_required') {
      await router.replace({ name: 'password' })
    } else if (error.code === 'csrf_invalid') {
      await session.refresh().catch(() => {})
    }
    showNotice(error.message)
  } else {
    showNotice('Ocurrió un error inesperado.')
    console.error(error)
  }
}
