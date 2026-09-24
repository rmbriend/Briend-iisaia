<script setup lang="ts">
import { computed } from 'vue'
import { fmt } from '@/utils'

const props = defineProps<{ value: number }>()
const safe = computed(() => Math.max(0, Math.min(100, Number(props.value) || 0)))
</script>

<template>
  <div class="progress-label"><span>Avance real</span><strong>{{ fmt(safe) }} %</strong></div>
  <div class="progress" role="progressbar" aria-label="Avance real" :aria-valuenow="safe" aria-valuemin="0" aria-valuemax="100">
    <div class="progress-bar" :style="{ width: safe + '%' }"></div>
  </div>
</template>
