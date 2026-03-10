<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

import Button from "primevue/button";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import Password from "primevue/password";

import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const email = ref("");
const username = ref("");
const password = ref("");
const error = ref("");

async function submit() {
  error.value = "";
  if (!email.value.includes("@")) {
    error.value = "请输入有效邮箱";
    return;
  }

  if (password.value.length < 8) {
    error.value = "密码长度至少 8 位";
    return;
  }

  try {
    await authStore.register({
      email: email.value,
      username: username.value,
      password: password.value
    });
    router.push("/files");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "注册失败";
  }
}
</script>

<template>
  <Card class="auth-card">
    <template #title>注册 FileHub 账号</template>
    <template #subtitle>创建后可直接进入文件中心</template>
    <template #content>
      <div class="auth-form">
        <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
        <label class="auth-label">邮箱</label>
        <InputText v-model="email" placeholder="请输入邮箱" />
        <label class="auth-label">用户名</label>
        <InputText v-model="username" placeholder="请输入用户名" />
        <label class="auth-label">密码</label>
        <Password v-model="password" :feedback="false" toggleMask placeholder="请输入密码（至少8位）" />
        <Button label="注册并登录" icon="pi pi-user-plus" :loading="authStore.loading" @click="submit" />
        <Button label="已有账号？去登录" severity="secondary" text @click="router.push('/login')" />
      </div>
    </template>
  </Card>
</template>
