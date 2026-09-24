<script setup lang="ts">
// Loading / error / content wrapper for a page's queries (the old "No se pudo cargar la página").
defineProps<{ loading: boolean; error: Error | null }>()
defineEmits<{ retry: [] }>()
</script>

<template>
  <p v-if="loading" role="status">Cargando…</p>
  <section v-else-if="error" class="panel empty">
    <h1>No se pudo cargar la página</h1>
    <p>{{ error.message }}</p>
    <div class="actions justify-content-center">
      <button class="btn btn-primary" @click="$emit('retry')">Reintentar</button>
      <RouterLink class="btn btn-outline-secondary" to="/proyectos">Volver al inicio</RouterLink>
    </div>
  </section>
  <slot v-else />
</template>
