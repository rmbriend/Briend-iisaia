<script setup lang="ts">
defineOptions({ inheritAttrs: false })
defineProps<{ name: string; label: string; type?: string }>()
const model = defineModel<string | number | null>()
</script>

<template>
  <div class="field">
    <label :for="name">{{ label }}</label>
    <input :id="name" v-model="model" class="form-control" :name="name" :type="type ?? 'text'" v-bind="$attrs" />
  </div>
</template>
