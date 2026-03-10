<script setup>
import { onMounted, ref } from "vue";

import Card from "primevue/card";
import Button from "primevue/button";
import Tag from "primevue/tag";

import { fetchHealth } from "../api/health";

const loading = ref(false);
const checkTime = ref("");
const health = ref({
  status: "unknown",
  message: "尚未执行健康检查"
});

async function loadHealth() {
  loading.value = true;
  try {
    const payload = await fetchHealth();
    health.value = {
      status: payload.status || "ok",
      message: `后端在线，版本 ${payload.version || "unknown"}`
    };
    checkTime.value = new Date().toLocaleString("zh-CN");
  } catch (error) {
    health.value = {
      status: "down",
      message: error instanceof Error ? error.message : "后端健康检查失败"
    };
    checkTime.value = new Date().toLocaleString("zh-CN");
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadHealth();
});
</script>

<template>
  <Card>
    <template #title>文件仓库系统</template>
    <template #subtitle>前端最小可运行骨架</template>
    <template #content>
      <p class="intro-text">
        当前页面用于验证 Vue 3 + PrimeVue + Vue Router 基础链路，并展示后端健康检查联通状态。
      </p>
      <div class="health-row">
        <Tag
          :severity="health.status === 'ok' ? 'success' : health.status === 'down' ? 'danger' : 'contrast'"
          :value="health.status === 'ok' ? '后端在线' : health.status === 'down' ? '后端不可用' : '未检查'"
        />
        <span class="health-message">{{ health.message }}</span>
      </div>
      <p class="check-time" v-if="checkTime">最近检查时间：{{ checkTime }}</p>
      <Button
        :label="loading ? '检查中...' : '重新检查后端健康状态'"
        icon="pi pi-refresh"
        severity="contrast"
        :loading="loading"
        @click="loadHealth"
      />
    </template>
  </Card>
</template>
