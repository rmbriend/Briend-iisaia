import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import type { Consumption, User } from '@/api/client'
import ConsumptionTable from '@/components/ConsumptionTable.vue'

const hostile = '<img src=x onerror=alert(1)>"\''
const row = (recurso_id: number): Consumption => ({
  consumo_id: recurso_id, proyecto_id: 1, recurso_id, rol_id: 1, fecha_inicio: '2026-09-01',
  fecha_fin: '2026-09-02', horas_consumidas: 2.5, tarea: hostile, proyecto_nombre: hostile,
  recurso_nombre: hostile, rol_descripcion: 'Analista',
})
const user = (es_admin: boolean): User => ({ recurso_id: 2, recurso_nombre: 'ana', es_admin, debe_cambiar_password: false })

function render(currentUser: User) {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/:p(.*)*', component: {} }] })
  return mount(ConsumptionTable, {
    props: { rows: [row(2), row(3)], user: currentUser, showProject: true },
    global: { plugins: [router, [VueQueryPlugin, { queryClient: new QueryClient() }]] },
  })
}

describe('ConsumptionTable', () => {
  it('renders untrusted names and tasks as text, never as HTML', () => {
    const wrapper = render(user(false))
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.text()).toContain(hostile)
    expect(wrapper.html()).toContain('&lt;img')
  })

  it('offers edit/delete only on own rows for plain users, on every row for admins', () => {
    expect(render(user(false)).findAll('.btn-outline-danger')).toHaveLength(1)
    expect(render(user(false)).text()).toContain('Solo lectura')
    expect(render(user(true)).findAll('.btn-outline-danger')).toHaveLength(2)
  })

  it('formats hours with the Argentine locale', () => {
    expect(render(user(true)).text()).toContain('2,5')
  })
})
