import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
// 導入 toast
import Toast, { type PluginOptions } from 'vue-toastification'
import 'vue-toastification/dist/index.css'

import App from './App.vue'
import router from './router'
import './axios'

const app = createApp(App)

app.use(createPinia())
app.use(router)

const options: PluginOptions = {
  timeout: 2000,
}
app.use(Toast, options)
app.mount('#app')
