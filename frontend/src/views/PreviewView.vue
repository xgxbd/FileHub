<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import Button from "primevue/button";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import ProgressBar from "primevue/progressbar";

import { downloadFile, previewFile } from "../api/files";
import { useAuthStore } from "../stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const previewLoading = ref(false);
const previewError = ref("");
const previewType = ref("");
const previewText = ref("");
const previewUrl = ref("");
const previewInputId = ref("");

const currentFileId = computed(() => {
  const id = route.params.fileId;
  return typeof id === "string" ? id : "";
});

const currentFileName = computed(() => {
  const name = route.query.name;
  return typeof name === "string" && name ? name : `文件 #${currentFileId.value || "未指定"}`;
});

function resetPreviewState() {
  previewLoading.value = false;
  previewError.value = "";
  previewType.value = "";
  previewText.value = "";
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
  }
  previewUrl.value = "";
}

async function loadPreviewById(fileId) {
  if (!fileId) {
    previewError.value = "请先输入文件 ID";
    return;
  }
  if (!authStore.accessToken) {
    previewError.value = "当前未登录";
    return;
  }

  resetPreviewState();
  previewLoading.value = true;

  try {
    const { blob, contentType } = await previewFile({
      accessToken: authStore.accessToken,
      fileId
    });

    if (contentType.startsWith("text/")) {
      previewType.value = "text";
      previewText.value = await blob.text();
    } else if (contentType.startsWith("image/")) {
      previewType.value = "image";
      previewUrl.value = URL.createObjectURL(blob);
    } else if (contentType.includes("pdf")) {
      previewType.value = "pdf";
      previewUrl.value = URL.createObjectURL(blob);
    } else {
      previewError.value = "当前类型不支持预览";
    }
  } catch (err) {
    previewError.value = err instanceof Error ? err.message : "预览失败";
  } finally {
    previewLoading.value = false;
  }
}

async function triggerDownload() {
  if (!currentFileId.value || !authStore.accessToken) return;

  try {
    const blob = await downloadFile({
      accessToken: authStore.accessToken,
      fileId: currentFileId.value,
      rangeHeader: "bytes=0-"
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = currentFileName.value;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  } catch (err) {
    previewError.value = err instanceof Error ? err.message : "下载失败";
  }
}

function jumpWithInputId() {
  const id = previewInputId.value.trim();
  if (!id) {
    previewError.value = "请先输入文件 ID";
    return;
  }
  router.push({ path: `/preview/${id}` });
}

watch(
  () => currentFileId.value,
  (id) => {
    previewInputId.value = id;
    if (id) {
      loadPreviewById(id);
    } else {
      resetPreviewState();
    }
  },
  { immediate: true }
);

onMounted(() => {
  previewInputId.value = currentFileId.value;
});

onBeforeUnmount(() => {
  resetPreviewState();
});
</script>

<template>
  <Card>
    <template #title>文件详情 / 预览页</template>
    <template #subtitle>图片、PDF、文本在线预览</template>
    <template #content>
      <div class="preview-layout">
        <section class="panel">
          <div class="file-filter-actions">
            <InputText v-model="previewInputId" placeholder="输入文件ID，例如 1" />
            <Button label="加载预览" icon="pi pi-eye" :loading="previewLoading" @click="jumpWithInputId" />
            <Button label="返回文件列表" severity="secondary" text @click="router.push('/files')" />
          </div>

          <Message v-if="previewError" severity="error" :closable="false">{{ previewError }}</Message>
          <ProgressBar v-if="previewLoading" mode="indeterminate" style="height: 6px" />

          <div class="preview-box" v-if="!previewLoading && !previewType && !previewError">请先选择文件后进行预览</div>
          <img v-if="!previewLoading && previewType === 'image'" :src="previewUrl" class="preview-image" alt="image-preview" />
          <iframe v-if="!previewLoading && previewType === 'pdf'" :src="previewUrl" class="preview-pdf"></iframe>
          <pre v-if="!previewLoading && previewType === 'text'" class="preview-text">{{ previewText }}</pre>
        </section>

        <section class="panel meta">
          <div class="row"><span>文件ID</span><b>{{ currentFileId || "未指定" }}</b></div>
          <div class="row"><span>文件名</span><b>{{ currentFileName }}</b></div>
          <div class="row"><span>预览类型</span><b>{{ previewType || "未知" }}</b></div>
          <div class="row"><span>上传用户</span><b>{{ authStore.user?.username || "未知" }}</b></div>
          <div class="actions" style="margin-top: 10px">
            <Button label="下载" icon="pi pi-download" @click="triggerDownload" :disabled="!currentFileId" />
          </div>
        </section>
      </div>
    </template>
  </Card>
</template>
