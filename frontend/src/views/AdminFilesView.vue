<script setup>
import { onMounted, ref } from "vue";

import Button from "primevue/button";
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import InputNumber from "primevue/inputnumber";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import SelectButton from "primevue/selectbutton";
import Tag from "primevue/tag";

import { fetchAdminFiles } from "../api/adminFiles";
import { purgeRecycleFile, restoreRecycleFile, softDeleteFile } from "../api/files";
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
const ownerId = ref(null);
const statusFilter = ref("active");

const operatingFileId = ref(null);

const statusOptions = [
  { label: "有效文件", value: "active" },
  { label: "已删除文件", value: "deleted" },
  { label: "全部", value: "all" }
];

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(1)} GB`;
}

function formatTime(iso) {
  return new Date(iso).toLocaleString("zh-CN");
}

async function loadAdminFiles() {
  if (!authStore.accessToken) return;

  loading.value = true;
  error.value = "";
  try {
    const payload = await fetchAdminFiles({
      accessToken: authStore.accessToken,
      keyword: keyword.value.trim(),
      ownerId: ownerId.value,
      status: statusFilter.value,
      page: page.value,
      pageSize: pageSize.value
    });
    items.value = payload.items || [];
    total.value = payload.total || 0;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "加载管理员文件列表失败";
  } finally {
    loading.value = false;
  }
}

async function search() {
  page.value = 1;
  await loadAdminFiles();
}

async function resetFilters() {
  keyword.value = "";
  ownerId.value = null;
  statusFilter.value = "active";
  page.value = 1;
  await loadAdminFiles();
}

async function onPageChange(event) {
  page.value = event.page + 1;
  pageSize.value = event.rows;
  await loadAdminFiles();
}

async function triggerDelete(fileItem) {
  if (!authStore.accessToken) return;
  if (!window.confirm(`确认将“${fileItem.file_name}”移入回收站吗？`)) {
    return;
  }
  operatingFileId.value = fileItem.id;
  error.value = "";
  successMessage.value = "";
  try {
    await softDeleteFile({
      accessToken: authStore.accessToken,
      fileId: fileItem.id
    });
    successMessage.value = `已删除：${fileItem.file_name}`;
    await loadAdminFiles();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "删除失败";
  } finally {
    operatingFileId.value = null;
  }
}

async function triggerRestore(fileItem) {
  if (!authStore.accessToken) return;
  operatingFileId.value = fileItem.id;
  error.value = "";
  successMessage.value = "";
  try {
    await restoreRecycleFile({
      accessToken: authStore.accessToken,
      fileId: fileItem.id
    });
    successMessage.value = `已恢复：${fileItem.file_name}`;
    await loadAdminFiles();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "恢复失败";
  } finally {
    operatingFileId.value = null;
  }
}

async function triggerPurge(fileItem) {
  if (!authStore.accessToken) return;
  if (!window.confirm(`确认彻底删除“${fileItem.file_name}”？该操作不可恢复。`)) {
    return;
  }
  operatingFileId.value = fileItem.id;
  error.value = "";
  successMessage.value = "";
  try {
    await purgeRecycleFile({
      accessToken: authStore.accessToken,
      fileId: fileItem.id
    });
    successMessage.value = `已彻底删除：${fileItem.file_name}`;
    await loadAdminFiles();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "彻底删除失败";
  } finally {
    operatingFileId.value = null;
  }
}

onMounted(() => {
  loadAdminFiles();
});
</script>

<template>
  <Card>
    <template #title>管理端文件管理</template>
    <template #subtitle>管理员全量文件视图（MVP）</template>
    <template #content>
      <div class="file-filter-row">
        <div class="file-filter-item">
          <label class="auth-label">文件关键字</label>
          <InputText v-model="keyword" placeholder="例如：report、photo" />
        </div>
        <div class="file-filter-item">
          <label class="auth-label">Owner ID</label>
          <InputNumber v-model="ownerId" :useGrouping="false" />
        </div>
        <div class="file-filter-item">
          <label class="auth-label">状态</label>
          <SelectButton v-model="statusFilter" :options="statusOptions" optionLabel="label" optionValue="value" />
        </div>
      </div>

      <div class="file-filter-actions">
        <Button label="查询" icon="pi pi-search" :loading="loading" @click="search" />
        <Button label="重置" severity="secondary" text @click="resetFilters" />
      </div>

      <Message v-if="successMessage" severity="success" :closable="false">{{ successMessage }}</Message>
      <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

      <div class="health-row">
        <Tag severity="info" value="管理员文件管理" />
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
        <Column field="id" header="文件ID"></Column>
        <Column field="owner_id" header="Owner ID"></Column>
        <Column field="file_name" header="文件名"></Column>
        <Column header="大小">
          <template #body="{ data }">{{ formatBytes(data.size_bytes) }}</template>
        </Column>
        <Column field="status" header="状态"></Column>
        <Column header="创建时间">
          <template #body="{ data }">{{ formatTime(data.created_at) }}</template>
        </Column>
        <Column header="操作">
          <template #body="{ data }">
            <div class="file-row-actions">
              <Button
                v-if="data.status === 'active'"
                label="删除"
                size="small"
                severity="danger"
                text
                icon="pi pi-trash"
                :loading="operatingFileId === data.id"
                @click="triggerDelete(data)"
              />
              <Button
                v-if="data.status === 'deleted'"
                label="恢复"
                size="small"
                icon="pi pi-replay"
                :loading="operatingFileId === data.id"
                @click="triggerRestore(data)"
              />
              <Button
                v-if="data.status === 'deleted'"
                label="彻底删除"
                size="small"
                severity="danger"
                text
                icon="pi pi-times-circle"
                :loading="operatingFileId === data.id"
                @click="triggerPurge(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </template>
  </Card>
</template>
