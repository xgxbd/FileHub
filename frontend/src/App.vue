<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import Button from "primevue/button";
import Tag from "primevue/tag";

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
    { label: "后台", to: "/admin/files", requiresAuth: true, requiresAdmin: true, adminOnlyLabel: true },
    { label: "日志", to: "/admin/logs", requiresAuth: true, requiresAdmin: true, adminOnlyLabel: true }
  ];

  return baseItems.filter((item) => {
    if (item.guestOnly) return !authStore.isAuthenticated;
    return authStore.isAuthenticated;
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

function jumpTo(item) {
  if (item.requiresAdmin && authStore.user?.role !== "admin") {
    window.alert("该页面仅管理员可访问");
    return;
  }
  if (route.path !== item.to) {
    router.push(item.to);
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
      <div
        class="brand"
        @click="jumpTo({ to: authStore.isAuthenticated ? '/files' : '/login', requiresAdmin: false })"
      >
        FileHub
      </div>
      <div class="page-info">
        <h1>{{ pageTitle }}</h1>
        <p>{{ pageSubtitle }}</p>
      </div>
      <div class="top-actions">
        <template v-if="authStore.isAuthenticated">
          <span class="user-chip">{{ userLabel }}</span>
          <Tag value="全局搜索规划中" severity="secondary" />
          <Tag v-if="authStore.user?.role === 'admin'" value="管理员账号" severity="info" />
          <Button size="small" label="退出" icon="pi pi-sign-out" @click="logout" />
        </template>
        <template v-else>
          <Button
            size="small"
            severity="secondary"
            text
            label="登录"
            @click="jumpTo({ to: '/login', requiresAdmin: false })"
          />
          <Button size="small" label="注册" @click="jumpTo({ to: '/register', requiresAdmin: false })" />
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
          @click="jumpTo(item)"
        >
          {{ item.label }}
          <span v-if="item.adminOnlyLabel" class="nav-badge">管理员</span>
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
