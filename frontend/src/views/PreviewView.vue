<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import Button from "primevue/button";
import Card from "primevue/card";
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

const totalFileCount = computed(() => fileCandidates.value.length);

const selectedDirectoryLabel = computed(() => {
  if (!currentFileName.value) return "/";
  return fileDirectoryLabel(currentFileName.value);
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

function mapPreviewError(err) {
  const status = Number(err?.status || 0);
  const detail = String(err?.message || "");

  if (status === 400) {
    return detail || "当前类型不支持在线预览";
  }
  if (status === 403) {
    return "你无权预览该文件";
  }
  if (status === 404 && detail.includes("文件内容不存在")) {
    return "文件元数据存在，但文件内容不存在，请重新上传";
  }
  if (status === 404) {
    return detail || "文件不存在";
  }
  return detail || "预览失败";
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
    previewError.value = mapPreviewError(err);
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
      pageSize: 100
    });
    fileCandidates.value = payload.items || [];
    if (!currentFileId.value && fileCandidates.value.length > 0) {
      pickFile(fileCandidates.value[0]);
    }
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

        <section class="preview-side">
          <section class="panel meta meta-compact">
            <div class="meta-stat">
              <span class="meta-stat-label">文件数</span>
              <strong class="meta-stat-value">{{ totalFileCount }}</strong>
            </div>
            <div class="meta-divider"></div>
            <div class="row"><span>文件名</span><b>{{ selectedLabel }}</b></div>
            <div class="row"><span>所在目录</span><b>{{ selectedDirectoryLabel }}</b></div>
            <div class="row"><span>预览类型</span><b>{{ previewType || "未知" }}</b></div>
          </section>

          <section class="panel preview-candidates-panel">
            <div class="file-filter-actions" style="justify-content: space-between">
              <strong>最近文件</strong>
              <Button size="small" text severity="secondary" label="刷新列表" icon="pi pi-refresh" @click="loadCandidates" />
            </div>
            <Message v-if="fileCandidatesError" severity="error" :closable="false">{{ fileCandidatesError }}</Message>

            <div class="preview-candidate-list" v-if="!fileCandidatesLoading">
              <button
                v-for="item in fileCandidates"
                :key="item.id"
                type="button"
                class="preview-candidate-item"
                :class="{ active: String(item.id) === currentFileId }"
                @click="pickFile(item)"
              >
                <span class="preview-candidate-name">{{ fileBaseName(item.file_name) }}</span>
                <span class="preview-candidate-meta">{{ fileDirectoryLabel(item.file_name) }}</span>
              </button>
            </div>
            <ProgressBar v-else mode="indeterminate" style="height: 6px" />
          </section>
        </section>
      </div>
    </template>
  </Card>
</template>
