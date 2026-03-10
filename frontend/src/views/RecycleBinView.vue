<script setup>
import { onMounted, ref } from "vue";

import Button from "primevue/button";
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import InputNumber from "primevue/inputnumber";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import Tag from "primevue/tag";

import { fetchRecycleFileList, purgeRecycleFile, restoreRecycleFile } from "../api/files";
import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();

const loading = ref(false);
const error = ref("");
const successMessage = ref("");
const items = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(10);

const keyword = ref("");
const minSize = ref(null);
const maxSize = ref(null);
const restoringFileId = ref(null);
const purgingFileId = ref(null);

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(1)} GB`;
}

function formatTime(iso) {
  return new Date(iso).toLocaleString("zh-CN");
}

async function loadRecycleFiles() {
  if (!authStore.accessToken) return;

  loading.value = true;
  error.value = "";
  try {
    const payload = await fetchRecycleFileList({
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
    error.value = err instanceof Error ? err.message : "加载回收站失败";
  } finally {
    loading.value = false;
  }
}

async function search() {
  page.value = 1;
  await loadRecycleFiles();
}

async function resetFilters() {
  keyword.value = "";
  minSize.value = null;
  maxSize.value = null;
  page.value = 1;
  await loadRecycleFiles();
}

async function onPageChange(event) {
  page.value = event.page + 1;
  pageSize.value = event.rows;
  await loadRecycleFiles();
}

async function triggerRestore(fileItem) {
  if (!authStore.accessToken) return;

  restoringFileId.value = fileItem.id;
  error.value = "";
  successMessage.value = "";
  try {
    await restoreRecycleFile({
      accessToken: authStore.accessToken,
      fileId: fileItem.id
    });
    successMessage.value = `已恢复文件：${fileItem.file_name}`;
    await loadRecycleFiles();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "恢复失败";
  } finally {
    restoringFileId.value = null;
  }
}

async function triggerPurge(fileItem) {
  if (!authStore.accessToken) return;
  if (!window.confirm(`确认彻底删除“${fileItem.file_name}”？该操作不可恢复。`)) {
    return;
  }

  purgingFileId.value = fileItem.id;
  error.value = "";
  successMessage.value = "";
  try {
    await purgeRecycleFile({
      accessToken: authStore.accessToken,
      fileId: fileItem.id
    });
    successMessage.value = `已彻底删除文件：${fileItem.file_name}`;
    await loadRecycleFiles();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "彻底删除失败";
  } finally {
    purgingFileId.value = null;
  }
}

onMounted(() => {
  loadRecycleFiles();
});
</script>

<template>
  <Card>
    <template #title>回收站</template>
    <template #subtitle>已删除文件管理（恢复 / 彻底删除）</template>
    <template #content>
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

      <Message v-if="successMessage" severity="success" :closable="false">{{ successMessage }}</Message>
      <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

      <div class="health-row">
        <Tag severity="warn" value="已删除文件" />
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
              <Button
                label="恢复"
                size="small"
                icon="pi pi-replay"
                :loading="restoringFileId === data.id"
                @click="triggerRestore(data)"
              />
              <Button
                label="彻底删除"
                size="small"
                severity="danger"
                text
                icon="pi pi-times-circle"
                :loading="purgingFileId === data.id"
                @click="triggerPurge(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </template>
  </Card>
</template>
