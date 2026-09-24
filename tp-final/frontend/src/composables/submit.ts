import { useQueryClient } from '@tanstack/vue-query'
import { ref } from 'vue'
import { type RouteLocationRaw, useRouter } from 'vue-router'
import { handleError, notice, showNotice } from './notice'

/**
 * Form submission: runs `action`, refreshes cached reads, navigates to the returned route and
 * shows `success`. On error the form (and what the user typed) stays in place with the message.
 */
export function useSubmit(
  action: () => Promise<RouteLocationRaw | void>,
  { success = 'Cambios guardados.', login = false } = {},
) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const busy = ref(false)

  async function submit() {
    busy.value = true
    notice.text = ''
    try {
      const target = await action()
      await queryClient.invalidateQueries()
      if (target) await router.push(target)
      if (success) showNotice(success, 'success')
    } catch (error) {
      await handleError(error, router, { login })
    } finally {
      busy.value = false
    }
  }

  return { busy, submit }
}
