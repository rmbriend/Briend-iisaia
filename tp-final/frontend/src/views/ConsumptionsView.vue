<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { api } from '@/api/client'
import ConsumptionTable from '@/components/ConsumptionTable.vue'
import LoadState from '@/components/LoadState.vue'
import PageHeading from '@/components/PageHeading.vue'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
const rows = useQuery({ queryKey: ['consumos'], queryFn: api.consumptions })
</script>

<template>
  <PageHeading title="Consumos" subtitle="El registro de horas de todos los proyectos." eyebrow="DEDICACIÓN">
    <RouterLink class="btn btn-primary" to="/consumos/nuevo">+ Registrar consumo</RouterLink>
  </PageHeading>
  <LoadState :loading="rows.isPending.value" :error="rows.error.value" @retry="rows.refetch()">
    <section v-if="session.user" class="panel">
      <ConsumptionTable :rows="rows.data.value ?? []" :user="session.user" show-project />
    </section>
  </LoadState>
</template>
