<script setup>
import Card from "primevue/card";
import Button from "primevue/button";
</script>

<template>
  <Card>
    <template #title>文件仓库系统</template>
    <template #subtitle>前端最小可运行骨架</template>
    <template #content>
      <p class="intro-text">
        当前页面用于验证 Vue 3 + PrimeVue + Vue Router 基础链路已正常工作，下一步将接入后端健康检查与业务页面。
      </p>
      <Button label="骨架已就绪" icon="pi pi-check-circle" severity="contrast" disabled />
    </template>
  </Card>
</template>
