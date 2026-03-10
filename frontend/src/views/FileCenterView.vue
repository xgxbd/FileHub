<script setup>
import Card from "primevue/card";
import Tag from "primevue/tag";

import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();
</script>

<template>
  <Card>
    <template #title>文件仓库首页</template>
    <template #subtitle>认证接入阶段占位页面</template>
    <template #content>
      <p class="intro-text">当前已完成前端认证闭环，下一步将接入文件列表、上传和预览模块。</p>
      <div class="health-row">
        <Tag severity="success" value="已登录" />
        <span class="health-message">当前用户：{{ authStore.user?.username || "未知用户" }}</span>
      </div>
    </template>
  </Card>
</template>
