<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { api } from '@/api/client'
import DeleteButton from '@/components/DeleteButton.vue'
import LoadState from '@/components/LoadState.vue'
import PageHeading from '@/components/PageHeading.vue'

const rows = useQuery({ queryKey: ['roles'], queryFn: api.roles })
</script>

<template>
  <PageHeading title="Roles" subtitle="Funciones desempeñadas al registrar horas." eyebrow="ORGANIZACIÓN">
    <RouterLink class="btn btn-primary" to="/roles/nuevo">+ Nuevo rol</RouterLink>
  </PageHeading>
  <LoadState :loading="rows.isPending.value" :error="rows.error.value" @retry="rows.refetch()">
    <section class="panel table-responsive">
      <table class="table">
        <thead><tr><th>Descripción</th><th>Acciones</th></tr></thead>
        <tbody>
          <tr v-for="r in rows.data.value" :key="r.rol_id">
            <td>{{ r.rol_descripcion }}</td>
            <td>
              <div class="actions">
                <RouterLink class="btn btn-sm btn-outline-secondary" :to="`/roles/${r.rol_id}/editar`">Editar</RouterLink>
                <DeleteButton :remove="() => api.deleteRole(r.rol_id)" return-to="/roles" />
              </div>
            </td>
          </tr>
          <tr v-if="!rows.data.value?.length">
            <td colspan="2" class="empty">Agregá un rol para comenzar a registrar consumos.</td>
          </tr>
        </tbody>
      </table>
    </section>
  </LoadState>
</template>
