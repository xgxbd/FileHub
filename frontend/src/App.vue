<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";

import Button from "primevue/button";

import { useAuthStore } from "./stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const userLabel = computed(() => authStore.user?.username || "");

function logout() {
  authStore.logout();
  router.push("/login");
}
</script>

<template>
  <div class="layout-shell">
    <header class="layout-header">
      <div class="brand">
        <i class="pi pi-folder brand-icon" aria-hidden="true"></i>
        <span class="brand-title">FileHub</span>
      </div>
      <div class="header-actions">
        <template v-if="authStore.isAuthenticated">
          <span class="phase-tag">当前用户：{{ userLabel }}</span>
          <Button size="small" severity="secondary" text label="文件中心" @click="router.push('/files')" />
          <Button size="small" label="退出" icon="pi pi-sign-out" @click="logout" />
        </template>
        <template v-else>
          <Button size="small" severity="secondary" text label="登录" @click="router.push('/login')" />
          <Button size="small" label="注册" icon="pi pi-user-plus" @click="router.push('/register')" />
        </template>
      </div>
    </header>
    <main class="layout-main">
      <RouterView />
    </main>
  </div>
</template>
