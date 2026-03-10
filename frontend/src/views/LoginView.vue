<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import Button from "primevue/button";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import Password from "primevue/password";

import { useAuthStore } from "../stores/auth";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const account = ref("");
const password = ref("");
const error = ref("");

async function submit() {
  error.value = "";
  try {
    await authStore.login({
      account: account.value,
      password: password.value
    });
    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/files";
    router.push(redirect);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "登录失败";
  }
}
</script>

<template>
  <Card class="auth-card">
    <template #title>登录 FileHub</template>
    <template #subtitle>使用已注册账号进入文件仓库</template>
    <template #content>
      <div class="auth-form">
        <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
        <label class="auth-label">账号（邮箱或用户名）</label>
        <InputText v-model="account" placeholder="请输入邮箱或用户名" />
        <label class="auth-label">密码</label>
        <Password v-model="password" :feedback="false" toggleMask placeholder="请输入密码" />
        <Button label="登录" icon="pi pi-sign-in" :loading="authStore.loading" @click="submit" />
        <Button
          label="没有账号？去注册"
          severity="secondary"
          text
          @click="router.push('/register')"
        />
      </div>
    </template>
  </Card>
</template>
