<script setup lang="ts">
defineProps<{ title: string; back: string; disabled?: boolean; busy?: boolean }>()
defineEmits<{ submit: [] }>()
</script>

<template>
  <div class="form-heading">
    <RouterLink :to="back">← Volver</RouterLink>
    <h1>{{ title }}</h1>
  </div>
  <form class="panel editor" @submit.prevent="$emit('submit')">
    <slot />
    <div class="actions">
      <button class="btn btn-primary" :disabled="disabled || busy">Guardar</button>
      <RouterLink class="btn btn-outline-secondary" :to="back">Cancelar</RouterLink>
    </div>
  </form>
</template>
