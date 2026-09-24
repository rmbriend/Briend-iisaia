import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import { createMemoryHistory, createRouter } from 'vue-router'
import ResourceFormView from '@/views/ResourceFormView.vue'

// Exercise the actual resource form and native email/pattern constraints.
describe('resource email field', () => {
  it('allows an empty email and rejects addresses without a dotted domain', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: {} }] })
    const wrapper = mount(ResourceFormView, {
      global: { plugins: [router, [VueQueryPlugin, { queryClient: new QueryClient() }]] },
    })
    const input = wrapper.get('input[name="email"]')
    const element = input.element as HTMLInputElement
    expect(element.checkValidity()).toBe(true)
    for (const value of ['ana', 'ana@empresa', '@empresa.com', 'ana@@empresa.com']) {
      await input.setValue(value)
      expect(element.checkValidity(), value).toBe(false)
    }
    await input.setValue('ana@empresa.com')
    expect(element.checkValidity()).toBe(true)
    wrapper.unmount()
  })
})
