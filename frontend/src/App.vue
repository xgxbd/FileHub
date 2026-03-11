<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import Button from "primevue/button";

import { useAuthStore } from "./stores/auth";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const userLabel = computed(() => authStore.user?.username || "游客");

const navItems = computed(() => {
  const baseItems = [
    { label: "登录", to: "/login", guestOnly: true },
    { label: "注册", to: "/register", guestOnly: true },
    { label: "文件列表", to: "/files", requiresAuth: true },
    { label: "上传", to: "/upload", requiresAuth: true },
    { label: "预览", to: "/preview", requiresAuth: true },
    { label: "回收站", to: "/recycle", requiresAuth: true },
    { label: "后台", to: "/admin/files", requiresAuth: true, requiresAdmin: true },
    { label: "日志", to: "/admin/logs", requiresAuth: true, requiresAdmin: true }
  ];

  return baseItems.filter((item) => {
    if (item.guestOnly) {
      return !authStore.isAuthenticated;
    }
    if (item.requiresAuth && !authStore.isAuthenticated) {
      return false;
    }
    if (item.requiresAdmin && authStore.user?.role !== "admin") {
      return false;
    }
    return true;
  });
});

const pageTitle = computed(() => route.meta.pageTitle || "文件仓库");
const pageSubtitle = computed(() => route.meta.pageSubtitle || "上传、管理、预览、回收与审计");
const pageKpis = computed(() => route.meta.pageKpis || []);

const activeNavPath = computed(() => {
  if (route.path.startsWith("/preview")) {
    return "/preview";
  }
  return route.path;
});

function jumpTo(to) {
  if (route.path !== to) {
    router.push(to);
  }
}

function logout() {
  authStore.logout();
  router.push("/login");
}
</script>

<template>
  <div class="scheme-root">
    <header class="topbar">
      <div class="brand" @click="jumpTo(authStore.isAuthenticated ? '/files' : '/login')">FileHub</div>
      <div class="page-info">
        <h1>{{ pageTitle }}</h1>
        <p>{{ pageSubtitle }}</p>
      </div>
      <div class="top-actions">
        <template v-if="authStore.isAuthenticated">
          <span class="user-chip">{{ userLabel }}</span>
          <Button size="small" severity="secondary" label="全局搜索" text />
          <Button v-if="authStore.user?.role === 'admin'" size="small" severity="secondary" text label="管理员" />
          <Button size="small" label="退出" icon="pi pi-sign-out" @click="logout" />
        </template>
        <template v-else>
          <Button size="small" severity="secondary" text label="登录" @click="jumpTo('/login')" />
          <Button size="small" label="注册" @click="jumpTo('/register')" />
        </template>
      </div>
    </header>

    <div class="shell">
      <aside class="sidebar">
        <button
          v-for="item in navItems"
          :key="item.to"
          class="nav-item"
          :class="{ active: activeNavPath === item.to }"
          @click="jumpTo(item.to)"
        >
          {{ item.label }}
        </button>
      </aside>

      <main class="main">
        <section v-if="pageKpis.length" class="kpi-row">
          <div v-for="kpi in pageKpis" :key="kpi" class="kpi">{{ kpi }}</div>
        </section>

        <section class="content-layout">
          <div class="primary">
            <RouterView />
          </div>
        </section>
      </main>
    </div>
  </div>
</template>
