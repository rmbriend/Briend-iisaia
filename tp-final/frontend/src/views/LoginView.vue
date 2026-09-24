<script setup lang="ts">
import { reactive } from 'vue'
import TextField from '@/components/TextField.vue'
import { useSubmit } from '@/composables/submit'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
const form = reactive({ recurso_nombre: '', password: '' })
const { busy, submit } = useSubmit(
  async () => {
    await session.login(form)
    return { name: 'projects' }
  },
  { success: '', login: true },
)
</script>

<template>
  <section class="login-layout">
    <div class="login-copy">
      <p class="eyebrow">CADA HORA CUENTA</p>
      <h1>Una mirada clara<br />a tus proyectos.</h1>
      <p class="lead">Registrá la dedicación de tu equipo y seguí el avance del trabajo en un mismo lugar.</p>
      <div class="login-art">
        <div><span>PLANIFICAR</span><b>01</b></div>
        <div><span>REGISTRAR</span><b>02</b></div>
        <div><span>AVANZAR</span><b>03</b></div>
      </div>
    </div>
    <div class="panel login-panel">
      <p class="eyebrow">BIENVENIDO A PULSO</p>
      <h2>Iniciar sesión</h2>
      <p class="muted">Ingresá con tu usuario registrado.</p>
      <form @submit.prevent="submit">
        <TextField v-model="form.recurso_nombre" name="recurso_nombre" label="Usuario" required autocomplete="username" />
        <TextField v-model="form.password" name="password" label="Contraseña" type="password" required autocomplete="current-password" />
        <button class="btn btn-primary w-100" :disabled="busy">Ingresar</button>
      </form>
    </div>
  </section>
</template>
