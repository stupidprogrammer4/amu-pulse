import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import './assets/styles/main.css'
import { router } from './core/router'

// The panel is English-only; pin the direction so nothing inherits an RTL page.
document.documentElement.lang = 'en'
document.documentElement.dir = 'ltr'

createApp(App).use(createPinia()).use(router).mount('#app')
