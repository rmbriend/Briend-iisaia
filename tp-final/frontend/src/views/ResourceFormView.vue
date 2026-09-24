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
  queryKey: ['recurso', () => props.id],
  queryFn: () => api.resource(props.id!),
  enabled: () => !!props.id,
  refetchOnWindowFocus: false,
})
const form = reactive({ recurso_nombre: '', password: '', es_admin: false })
watch(
  () => existing.data.value,
  (r) => r && Object.assign(form, { recurso_nombre: r.recurso_nombre, es_admin: r.es_admin }),
  { immediate: true },
)

const { busy, submit } = useSubmit(async () => {
  await api.saveResource(form, props.id)
  return '/recursos'
})
</script>

<template>
  <LoadState :loading="!!id && existing.isPending.value" :error="existing.error.value" @retry="existing.refetch()">
    <FormShell :title="id ? 'Editar recurso' : 'Nuevo recurso'" back="/recursos" :busy="busy" @submit="submit">
      <TextField v-model="form.recurso_nombre" name="recurso_nombre" label="Nombre de usuario" required autocomplete="off" />
      <TextField
        v-model="form.password" name="password" type="password" minlength="8" autocomplete="new-password"
        :label="id ? 'Restablecer contraseña (opcional)' : 'Contraseña inicial'" :required="!id"
      />
      <p class="muted">Mínimo 8 caracteres. El usuario deberá cambiarla en su próximo acceso.</p>
      <label class="checkbox"><input v-model="form.es_admin" type="checkbox" name="es_admin" /> Acceso de administrador</label>
    </FormShell>
  </LoadState>
</template>
