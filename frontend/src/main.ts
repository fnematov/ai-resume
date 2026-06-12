import { VueQueryPlugin } from "@tanstack/vue-query"
import { createPinia } from "pinia"
import { createApp } from "vue"

import App from "./App.vue"
import { i18n } from "./i18n"
import router from "./router"
import "./style.css"

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
