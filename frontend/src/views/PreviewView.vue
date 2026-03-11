<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import Button from "primevue/button";
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Message from "primevue/message";
import ProgressBar from "primevue/progressbar";

import { downloadFile, fetchFileList, previewFile } from "../api/files";
import { useAuthStore } from "../stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const previewLoading = ref(false);
const previewError = ref("");
const previewType = ref("");
const previewText = ref("");
const previewUrl = ref("");

const fileCandidates = ref([]);
const fileCandidatesLoading = ref(false);
const fileCandidatesError = ref("");

const currentFileId = computed(() => {
  const id = route.params.fileId;
  return typeof id === "string" && id ? id : "";
});

const currentFileName = computed(() => {
  const name = route.query.name;
  return typeof name === "string" && name ? name : "";
});

const selectedLabel = computed(() => {
  if (currentFileName.value) return currentFileName.value;
  if (currentFileId.value) return `文件 #${currentFileId.value}`;
  return "未选择文件";
});

function normalizeFilePath(raw) {
  return String(raw || "")
    .replace(/\\/g, "/")
    .split("/")
    .map((part) => part.trim())
    .filter((part) => part && part !== "." && part !== "..")
    .join("/");
}

function fileBaseName(fileName) {
  const normalized = normalizeFilePath(fileName);
  const parts = normalized.split("/");
  return parts[parts.length - 1] || normalized;
}

function fileDirectoryLabel(fileName) {
  const normalized = normalizeFilePath(fileName);
  const parts = normalized.split("/");
  if (parts.length <= 1) return "/";
  return `/${parts.slice(0, -1).join("/")}/`;
}

function formatTime(iso) {
  return new Date(iso).toLocaleString("zh-CN");
}

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
    previewError.value = "请先从下方文件列表选择要预览的文件";
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

async function loadCandidates() {
  if (!authStore.accessToken) return;

  fileCandidatesLoading.value = true;
  fileCandidatesError.value = "";
  try {
    const payload = await fetchFileList({
      accessToken: authStore.accessToken,
      page: 1,
      pageSize: 20
    });
    fileCandidates.value = payload.items || [];
  } catch (err) {
    fileCandidatesError.value = err instanceof Error ? err.message : "加载文件列表失败";
  } finally {
    fileCandidatesLoading.value = false;
  }
}

function pickFile(fileItem) {
  router.push({
    path: `/preview/${fileItem.id}`,
    query: { name: fileBaseName(fileItem.file_name) }
  });
}

async function triggerDownload() {
  if (!currentFileId.value || !authStore.accessToken) {
    previewError.value = "请先选择文件";
    return;
  }

  try {
    const blob = await downloadFile({
      accessToken: authStore.accessToken,
      fileId: currentFileId.value,
      rangeHeader: "bytes=0-"
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = currentFileName.value || `file-${currentFileId.value}`;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  } catch (err) {
    previewError.value = err instanceof Error ? err.message : "下载失败";
  }
}

watch(
  () => currentFileId.value,
  async (id) => {
    if (id) {
      await loadPreviewById(id);
      return;
    }
    resetPreviewState();
  },
  { immediate: true }
);

onMounted(async () => {
  await loadCandidates();
});

onBeforeUnmount(() => {
  resetPreviewState();
});
</script>

<template>
  <Card>
    <template #title>文件详情 / 预览页</template>
    <template #subtitle>按文件路径选择并预览图片、PDF、文本</template>
    <template #content>
      <div class="preview-layout">
        <section class="panel">
          <div class="file-filter-actions">
            <Button label="返回文件列表" severity="secondary" text @click="router.push('/files')" />
            <Button label="下载当前文件" icon="pi pi-download" @click="triggerDownload" :disabled="!currentFileId" />
          </div>

          <Message v-if="previewError" severity="error" :closable="false">{{ previewError }}</Message>
          <ProgressBar v-if="previewLoading" mode="indeterminate" style="height: 6px" />

          <div class="preview-box" v-if="!previewLoading && !previewType && !previewError">请先从下方文件列表选择文件</div>
          <img v-if="!previewLoading && previewType === 'image'" :src="previewUrl" class="preview-image" alt="image-preview" />
          <iframe v-if="!previewLoading && previewType === 'pdf'" :src="previewUrl" class="preview-pdf"></iframe>
          <pre v-if="!previewLoading && previewType === 'text'" class="preview-text">{{ previewText }}</pre>
        </section>

        <section class="panel meta">
          <div class="row"><span>已选文件</span><b>{{ selectedLabel }}</b></div>
          <div class="row"><span>预览类型</span><b>{{ previewType || "未知" }}</b></div>
          <div class="row"><span>上传用户</span><b>{{ authStore.user?.username || "未知" }}</b></div>
        </section>
      </div>

      <section class="panel" style="margin-top: 12px">
        <div class="file-filter-actions" style="justify-content: space-between">
          <strong>最近文件</strong>
          <Button size="small" text severity="secondary" label="刷新列表" icon="pi pi-refresh" @click="loadCandidates" />
        </div>
        <Message v-if="fileCandidatesError" severity="error" :closable="false">{{ fileCandidatesError }}</Message>
        <DataTable :value="fileCandidates" :loading="fileCandidatesLoading">
          <Column header="文件名">
            <template #body="{ data }">{{ fileBaseName(data.file_name) }}</template>
          </Column>
          <Column header="所在目录">
            <template #body="{ data }">{{ fileDirectoryLabel(data.file_name) }}</template>
          </Column>
          <Column field="mime_type" header="类型"></Column>
          <Column header="创建时间">
            <template #body="{ data }">{{ formatTime(data.created_at) }}</template>
          </Column>
          <Column header="操作">
            <template #body="{ data }">
              <Button size="small" label="预览" icon="pi pi-eye" @click="pickFile(data)" />
            </template>
          </Column>
        </DataTable>
      </section>
    </template>
  </Card>
</template>
