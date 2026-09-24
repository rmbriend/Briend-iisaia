<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue'
import { notice } from '@/composables/notice'
</script>

<template>
  <AppHeader />
  <main class="container-fluid page">
    <div v-if="notice.text" :class="`alert alert-${notice.kind}`" role="alert" aria-live="polite">
      {{ notice.text }}
    </div>
    <RouterView />
  </main>
  <footer>Pulso · Seguimiento de proyectos y dedicación</footer>
</template>
