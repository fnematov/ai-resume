import { VueQueryPlugin } from "@tanstack/vue-query"
import { createPinia } from "pinia"
import { createApp } from "vue"

import App from "./App.vue"
import { useTheme } from "./composables/useTheme"
import { i18n } from "./i18n"
import router from "./router"
import "./style.css"

// Apply the saved/system theme before mount to avoid a flash of the wrong theme.
useTheme()

const app = createApp(App)
app.use(createPinia())
app.use(i18n)
app.use(router)
app.use(VueQueryPlugin, {
  queryClientConfig: {
    defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
  },
})
app.mount("#app")
