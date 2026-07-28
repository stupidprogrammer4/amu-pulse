import { createApp } from 'vue'

import App from './App.vue'
import '@/assets/styles/main.css'
import { DIRECTION, LOCALE } from '@/core/config/locale'
import router from '@/core/router'
import { pinia } from '@/core/store'
import { setUnauthorizedHandler } from '@/infra/http'

// Keep the document in sync with the app's single locale, in case a host page
// or a stray script changed it after index.html was parsed.
document.documentElement.lang = LOCALE.split('-')[0]
document.documentElement.dir = DIRECTION

// A dropped session sends the user back to the dashboard rather than leaving
// them on a page that will only keep failing.
setUnauthorizedHandler(() => {
  void router.push({ name: 'dashboard' })
})

createApp(App).use(pinia).use(router).mount('#app')
