<script setup lang="ts">
defineProps<{ items: [string, string | number][] }>()
</script>

<template>
  <div class="stats">
    <div v-for="[label, value] in items" :key="label" class="stat">
      <span>{{ label }}</span><strong>{{ value }}</strong>
    </div>
  </div>
</template>
