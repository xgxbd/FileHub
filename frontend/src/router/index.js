import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

import AdminLogsView from "../views/AdminLogsView.vue";
import AdminFilesView from "../views/AdminFilesView.vue";
import FileCenterView from "../views/FileCenterView.vue";
import LoginView from "../views/LoginView.vue";
import RecycleBinView from "../views/RecycleBinView.vue";
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
    },
    {
      path: "/recycle",
      name: "recycle",
      component: RecycleBinView,
      meta: { requiresAuth: true }
    },
    {
      path: "/admin/logs",
      name: "admin-logs",
      component: AdminLogsView,
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: "/admin/files",
      name: "admin-files",
      component: AdminFilesView,
      meta: { requiresAuth: true, requiresAdmin: true }
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

  if (to.meta.requiresAdmin && authStore.user?.role !== "admin") {
    return { name: "files" };
  }

  if (to.meta.guestOnly && authStore.accessToken) {
    return { name: "files" };
  }

  return true;
});

export default router;
