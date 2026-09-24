import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api, type Schemas, type User } from '@/api/client'

export const useSessionStore = defineStore('session', () => {
  const user = ref<User | null>(null)

  async function refresh() {
    user.value = (await api.session()).user ?? null
    return user.value
  }
  async function login(body: Schemas['LoginIn']) {
    user.value = (await api.login(body)).user ?? null
  }
  async function logout() {
    user.value = (await api.logout()).user ?? null
  }
  async function changePassword(body: Schemas['PasswordIn']) {
    user.value = (await api.changePassword(body)).user ?? null
  }
  function forget() {
    user.value = null
  }

  return { user, refresh, login, logout, changePassword, forget }
})
