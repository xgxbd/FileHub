import { createApp } from "vue";
import { createPinia } from "pinia";
import PrimeVue from "primevue/config";
import Aura from "@primeuix/themes/aura";

import App from "./App.vue";
import router from "./router";
import { useAuthStore } from "./stores/auth";
import "./styles/main.css";
import "primeicons/primeicons.css";

async function bootstrap() {
  const app = createApp(App);
  const pinia = createPinia();

  app.use(pinia);
  app.use(router);
  app.use(PrimeVue, {
    theme: {
      preset: Aura
    }
  });

  const authStore = useAuthStore(pinia);
  await authStore.initSession();

  app.mount("#app");
}

bootstrap();
