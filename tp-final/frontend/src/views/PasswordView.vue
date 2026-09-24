<script setup lang="ts">
import { reactive } from 'vue'
import PageHeading from '@/components/PageHeading.vue'
import TextField from '@/components/TextField.vue'
import { useSubmit } from '@/composables/submit'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
const form = reactive({ actual: '', password: '', confirmacion: '' })
const { busy, submit } = useSubmit(
  async () => {
    await session.changePassword(form)
    return { name: 'projects' }
  },
  { success: 'Contraseña actualizada.' },
)
</script>

<template>
  <PageHeading title="Cambiar contraseña" eyebrow="MI CUENTA" />
  <form class="panel editor" @submit.prevent="submit">
    <div v-if="session.user?.debe_cambiar_password" class="alert alert-info">
      Para continuar, reemplazá tu contraseña inicial por una propia.
    </div>
    <TextField v-model="form.actual" name="actual" label="Contraseña actual" type="password" required autocomplete="current-password" />
    <TextField v-model="form.password" name="password" label="Nueva contraseña" type="password" required minlength="8" autocomplete="new-password" />
    <TextField v-model="form.confirmacion" name="confirmacion" label="Confirmar nueva contraseña" type="password" required minlength="8" autocomplete="new-password" />
    <p class="muted">Usá al menos 8 caracteres.</p>
    <button class="btn btn-primary" :disabled="busy">Guardar contraseña</button>
  </form>
</template>
