<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { api } from '@/api/client'
import DeleteButton from '@/components/DeleteButton.vue'
import LoadState from '@/components/LoadState.vue'
import PageHeading from '@/components/PageHeading.vue'

const rows = useQuery({ queryKey: ['recursos'], queryFn: api.resources })
</script>

<template>
  <PageHeading title="Recursos" subtitle="Personas con acceso al sistema." eyebrow="EQUIPO">
    <RouterLink class="btn btn-primary" to="/recursos/nuevo">+ Nuevo recurso</RouterLink>
  </PageHeading>
  <LoadState :loading="rows.isPending.value" :error="rows.error.value" @retry="rows.refetch()">
    <section class="panel table-responsive">
      <table class="table">
        <thead><tr><th>Usuario</th><th>Acceso</th><th>Contraseña</th><th>Acciones</th></tr></thead>
        <tbody>
          <tr v-for="r in rows.data.value" :key="r.recurso_id">
            <td>{{ r.recurso_nombre }}</td>
            <td>{{ r.es_admin ? 'Administrador' : 'Usuario' }}</td>
            <td>{{ r.debe_cambiar_password ? 'Cambio pendiente' : 'Configurada' }}</td>
            <td>
              <div class="actions">
                <RouterLink class="btn btn-sm btn-outline-secondary" :to="`/recursos/${r.recurso_id}/editar`">Editar</RouterLink>
                <DeleteButton :remove="() => api.deleteResource(r.recurso_id)" return-to="/recursos" />
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </LoadState>
</template>
