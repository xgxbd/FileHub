<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import Button from "primevue/button";
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import InputNumber from "primevue/inputnumber";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import Tag from "primevue/tag";

import { downloadFile, fetchFileList, softDeleteFile } from "../api/files";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
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

const downloadError = ref("");
const deleteError = ref("");
const downloadingFileId = ref(null);
const deletingFileId = ref(null);

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

async function triggerSoftDelete(fileItem) {
  if (!authStore.accessToken) return;
  if (!window.confirm(`确认将文件“${fileItem.file_name}”移入回收站吗？`)) {
    return;
  }

  deleteError.value = "";
  deletingFileId.value = fileItem.id;
  try {
    await softDeleteFile({
      accessToken: authStore.accessToken,
      fileId: fileItem.id
    });
    await loadFiles();
  } catch (err) {
    deleteError.value = err instanceof Error ? err.message : "删除失败";
  } finally {
    deletingFileId.value = null;
  }
}

function triggerPreview(fileItem) {
  router.push({ path: `/preview/${fileItem.id}`, query: { name: fileItem.file_name } });
}

onMounted(() => {
  loadFiles();
});
</script>

<template>
  <Card>
    <template #title>文件仓库首页</template>
    <template #subtitle>文件检索、筛选与操作</template>
    <template #content>
      <p class="intro-text">当前用户：{{ authStore.user?.username || "未知用户" }}，可按文件名和大小进行筛选。</p>

      <div class="file-filter-actions">
        <Button label="前往上传页" icon="pi pi-upload" @click="router.push('/upload')" />
        <Button label="回收站" severity="secondary" text @click="router.push('/recycle')" />
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
      <Message v-if="downloadError" severity="error" :closable="false">{{ downloadError }}</Message>
      <Message v-if="deleteError" severity="error" :closable="false">{{ deleteError }}</Message>

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
              <Button
                label="删除"
                size="small"
                severity="danger"
                text
                icon="pi pi-trash"
                :loading="deletingFileId === data.id"
                @click="triggerSoftDelete(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </template>
  </Card>
</template>
