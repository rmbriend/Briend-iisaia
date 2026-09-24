import 'bootstrap/dist/css/bootstrap.min.css'
import './styles/main.css'
import { QueryCache, QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import { createPinia } from 'pinia'
import { createApp } from 'vue'
import { APIError } from './api/client'
import App from './App.vue'
import { handleError } from './composables/notice'
import { createAppRouter } from './router'

const app = createApp(App)
const router = createAppRouter()
const queryClient = new QueryClient({
  // A read that fails because the session expired (or a password change is pending) redirects;
  // other load errors are shown by the page's own error panel.
  queryCache: new QueryCache({
    onError(error) {
      if (error instanceof APIError && (error.status === 401 || error.code === 'password_change_required')) {
        void handleError(error, router)
      }
    },
  }),
  defaultOptions: { queries: { retry: false, refetchOnWindowFocus: true } },
})

app.use(createPinia()).use(router).use(VueQueryPlugin, { queryClient })
app.mount('#app')
