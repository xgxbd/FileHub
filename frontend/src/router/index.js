import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

import FileCenterView from "../views/FileCenterView.vue";
import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/files"
    },
    {
      path: "/login",
      name: "login",
      component: LoginView,
      meta: { guestOnly: true }
    },
    {
      path: "/register",
      name: "register",
      component: RegisterView,
      meta: { guestOnly: true }
    },
    {
      path: "/files",
      name: "files",
      component: FileCenterView,
      meta: { requiresAuth: true }
    }
  ]
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();
  authStore.syncLocalTokens();

  if (authStore.accessToken && !authStore.user) {
    try {
      await authStore.loadProfile();
    } catch {
      authStore.logout();
    }
  }

  if (to.meta.requiresAuth && !authStore.accessToken) {
    return { name: "login", query: { redirect: to.fullPath } };
  }

  if (to.meta.guestOnly && authStore.accessToken) {
    return { name: "files" };
  }

  return true;
});

export default router;
