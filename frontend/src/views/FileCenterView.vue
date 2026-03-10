<script setup>
import { onMounted, ref } from "vue";

import Button from "primevue/button";
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Dialog from "primevue/dialog";
import InputNumber from "primevue/inputnumber";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import ProgressBar from "primevue/progressbar";
import Tag from "primevue/tag";

import { downloadFile, fetchFileList, previewFile } from "../api/files";
import { completeUploadSession, createUploadSession, uploadChunk } from "../api/upload";
import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();

const loading = ref(false);
const error = ref("");
const items = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(10);

const keyword = ref("");
const minSize = ref(null);
const maxSize = ref(null);

const selectedFile = ref(null);
const uploadLoading = ref(false);
const uploadProgress = ref(0);
const uploadMessage = ref("");
const uploadError = ref("");
const downloadError = ref("");
const downloadingFileId = ref(null);
const previewVisible = ref(false);
const previewLoading = ref(false);
const previewError = ref("");
const previewType = ref("");
const previewText = ref("");
const previewUrl = ref("");
const previewName = ref("");

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(1)} GB`;
}

function formatTime(iso) {
  return new Date(iso).toLocaleString("zh-CN");
}

async function loadFiles() {
  if (!authStore.accessToken) return;

  loading.value = true;
  error.value = "";
  try {
    const payload = await fetchFileList({
      accessToken: authStore.accessToken,
      keyword: keyword.value.trim(),
      minSize: minSize.value,
      maxSize: maxSize.value,
      page: page.value,
      pageSize: pageSize.value
    });
    items.value = payload.items || [];
    total.value = payload.total || 0;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "加载文件列表失败";
  } finally {
    loading.value = false;
  }
}

async function search() {
  page.value = 1;
  await loadFiles();
}

async function resetFilters() {
  keyword.value = "";
  minSize.value = null;
  maxSize.value = null;
  page.value = 1;
  await loadFiles();
}

async function onPageChange(event) {
  page.value = event.page + 1;
  pageSize.value = event.rows;
  await loadFiles();
}

function onFileChange(event) {
  const file = event.target.files?.[0] || null;
  selectedFile.value = file;
  uploadProgress.value = 0;
  uploadMessage.value = "";
  uploadError.value = "";
}

async function startUpload() {
  if (!selectedFile.value) {
    uploadError.value = "请先选择文件";
    return;
  }
  if (!authStore.accessToken) {
    uploadError.value = "当前未登录";
    return;
  }

  uploadLoading.value = true;
  uploadError.value = "";
  uploadMessage.value = "";
  uploadProgress.value = 0;

  const chunkSize = 1024 * 1024;
  const totalChunks = Math.ceil(selectedFile.value.size / chunkSize);

  try {
    const session = await createUploadSession({
      accessToken: authStore.accessToken,
      payload: {
        file_name: selectedFile.value.name,
        total_size: selectedFile.value.size,
        chunk_size: chunkSize,
        total_chunks: totalChunks,
        mime_type: selectedFile.value.type || "application/octet-stream"
      }
    });

    for (let index = 0; index < totalChunks; index += 1) {
      const start = index * chunkSize;
      const end = Math.min(start + chunkSize, selectedFile.value.size);
      const blob = selectedFile.value.slice(start, end);

      await uploadChunk({
        accessToken: authStore.accessToken,
        uploadId: session.upload_id,
        chunkIndex: index,
        chunkBlob: blob
      });
      uploadProgress.value = Math.floor(((index + 1) / totalChunks) * 100);
    }

    await completeUploadSession({
      accessToken: authStore.accessToken,
      uploadId: session.upload_id
    });

    uploadMessage.value = "上传完成";
    await loadFiles();
  } catch (err) {
    uploadError.value = err instanceof Error ? err.message : "上传失败";
  } finally {
    uploadLoading.value = false;
  }
}

async function triggerDownload(fileItem) {
  if (!authStore.accessToken) return;

  downloadError.value = "";
  downloadingFileId.value = fileItem.id;
  try {
    const blob = await downloadFile({
      accessToken: authStore.accessToken,
      fileId: fileItem.id,
      rangeHeader: "bytes=0-"
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = fileItem.file_name;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  } catch (err) {
    downloadError.value = err instanceof Error ? err.message : "下载失败";
  } finally {
    downloadingFileId.value = null;
  }
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

async function triggerPreview(fileItem) {
  if (!authStore.accessToken) return;

  resetPreviewState();
  previewVisible.value = true;
  previewLoading.value = true;
  previewName.value = fileItem.file_name;

  try {
    const { blob, contentType } = await previewFile({
      accessToken: authStore.accessToken,
      fileId: fileItem.id
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

function closePreview() {
  previewVisible.value = false;
  resetPreviewState();
}

onMounted(() => {
  loadFiles();
});
</script>

<template>
  <Card>
    <template #title>文件仓库首页</template>
    <template #subtitle>文件列表与基础筛选（MVP）</template>
    <template #content>
      <p class="intro-text">当前用户：{{ authStore.user?.username || "未知用户" }}，可按文件名和大小进行筛选。</p>
      <div class="upload-panel">
        <div class="upload-actions">
          <input type="file" @change="onFileChange" />
          <Button label="开始上传" icon="pi pi-upload" :loading="uploadLoading" @click="startUpload" />
        </div>
        <div class="upload-status">
          <span v-if="selectedFile">已选择：{{ selectedFile.name }}</span>
          <span v-else>未选择文件</span>
        </div>
        <ProgressBar :value="uploadProgress"></ProgressBar>
        <Message v-if="uploadMessage" severity="success" :closable="false">{{ uploadMessage }}</Message>
        <Message v-if="uploadError" severity="error" :closable="false">{{ uploadError }}</Message>
        <Message v-if="downloadError" severity="error" :closable="false">{{ downloadError }}</Message>
      </div>
      <div class="file-filter-row">
        <div class="file-filter-item">
          <label class="auth-label">文件名关键字</label>
          <InputText v-model="keyword" placeholder="例如：report、photo" />
        </div>
        <div class="file-filter-item">
          <label class="auth-label">最小大小（字节）</label>
          <InputNumber v-model="minSize" :useGrouping="false" />
        </div>
        <div class="file-filter-item">
          <label class="auth-label">最大大小（字节）</label>
          <InputNumber v-model="maxSize" :useGrouping="false" />
        </div>
      </div>
      <div class="file-filter-actions">
        <Button label="查询" icon="pi pi-search" :loading="loading" @click="search" />
        <Button label="重置" severity="secondary" text @click="resetFilters" />
      </div>
      <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
      <div class="health-row">
        <Tag severity="success" value="已登录" />
        <span class="health-message">共 {{ total }} 个文件</span>
      </div>
      <DataTable
        :value="items"
        :loading="loading"
        paginator
        lazy
        :rows="pageSize"
        :first="(page - 1) * pageSize"
        :totalRecords="total"
        @page="onPageChange"
      >
        <Column field="file_name" header="文件名"></Column>
        <Column header="大小">
          <template #body="{ data }">{{ formatBytes(data.size_bytes) }}</template>
        </Column>
        <Column field="mime_type" header="类型"></Column>
        <Column field="status" header="状态"></Column>
        <Column header="创建时间">
          <template #body="{ data }">{{ formatTime(data.created_at) }}</template>
        </Column>
        <Column header="操作">
          <template #body="{ data }">
            <div class="file-row-actions">
              <Button label="预览" size="small" severity="secondary" text icon="pi pi-eye" @click="triggerPreview(data)" />
              <Button
                label="下载"
                size="small"
                icon="pi pi-download"
                :loading="downloadingFileId === data.id"
                @click="triggerDownload(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>

      <Dialog
        :visible="previewVisible"
        modal
        :header="`预览：${previewName}`"
        :style="{ width: '70vw' }"
        @update:visible="(val) => { if (!val) closePreview(); }"
      >
        <div class="preview-body">
          <Message v-if="previewError" severity="error" :closable="false">{{ previewError }}</Message>
          <ProgressBar v-if="previewLoading" mode="indeterminate" style="height: 6px" />
          <img v-if="!previewLoading && previewType === 'image'" :src="previewUrl" class="preview-image" alt="image-preview" />
          <iframe v-if="!previewLoading && previewType === 'pdf'" :src="previewUrl" class="preview-pdf"></iframe>
          <pre v-if="!previewLoading && previewType === 'text'" class="preview-text">{{ previewText }}</pre>
        </div>
      </Dialog>
    </template>
  </Card>
</template>
