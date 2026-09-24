<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { reactive, watch } from 'vue'
import { api } from '@/api/client'
import FormShell from '@/components/FormShell.vue'
import LoadState from '@/components/LoadState.vue'
import TextField from '@/components/TextField.vue'
import { useSubmit } from '@/composables/submit'

const props = defineProps<{ id?: number }>()
const existing = useQuery({
  queryKey: ['rol', () => props.id],
  queryFn: () => api.role(props.id!),
  enabled: () => !!props.id,
  refetchOnWindowFocus: false,
})
const form = reactive({ rol_descripcion: '' })
watch(
  () => existing.data.value,
  (r) => r && Object.assign(form, { rol_descripcion: r.rol_descripcion }),
  { immediate: true },
)

const { busy, submit } = useSubmit(async () => {
  await api.saveRole(form, props.id)
  return '/roles'
})
</script>

<template>
  <LoadState :loading="!!id && existing.isPending.value" :error="existing.error.value" @retry="existing.refetch()">
    <FormShell :title="id ? 'Editar rol' : 'Nuevo rol'" back="/roles" :busy="busy" @submit="submit">
      <TextField v-model="form.rol_descripcion" name="rol_descripcion" label="Descripción del rol" required />
    </FormShell>
  </LoadState>
</template>
