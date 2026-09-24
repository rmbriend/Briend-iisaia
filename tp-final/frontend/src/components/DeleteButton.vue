<script setup lang="ts">
import { useQueryClient } from '@tanstack/vue-query'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { handleError, showNotice } from '@/composables/notice'

const props = defineProps<{ remove: () => Promise<unknown>; returnTo: string }>()
const router = useRouter()
const queryClient = useQueryClient()
const busy = ref(false)

async function run() {
  if (!window.confirm('¿Eliminar este registro? Esta acción no se puede deshacer.')) return
  busy.value = true
  try {
    await props.remove()
    await router.push(props.returnTo) // leave first: the deleted record's page must not refetch
    await queryClient.invalidateQueries()
    showNotice('Registro eliminado.', 'success')
  } catch (error) {
    await handleError(error, router)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <button type="button" class="btn btn-sm btn-outline-danger" :disabled="busy" @click="run">Eliminar</button>
</template>
