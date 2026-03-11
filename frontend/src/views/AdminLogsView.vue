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

import { fetchAdminLogs } from "../api/adminLogs";
import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();

const loading = ref(false);
const error = ref("");
const items = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(10);

const action = ref("");
const userId = ref(null);
const startAt = ref("");
const endAt = ref("");

function buildApiDateTime(localValue) {
  if (!localValue) return "";
  return new Date(localValue).toISOString();
}

function formatDetail(detailJson) {
  if (!detailJson) return "-";
  try {
    const payload = JSON.parse(detailJson);
    const summaryKeys = ["file_name", "range", "size_bytes", "path"];
    const summary = summaryKeys
      .filter((key) => payload[key] !== undefined && payload[key] !== null && payload[key] !== "")
      .map((key) => `${key}: ${payload[key]}`);
    if (summary.length > 0) {
      return summary.join(" | ");
    }
    return JSON.stringify(payload);
  } catch {
    return detailJson;
  }
}

function formatTime(iso) {
  return new Date(iso).toLocaleString("zh-CN");
}

async function loadLogs() {
  if (!authStore.accessToken) return;

  loading.value = true;
  error.value = "";
  try {
    const payload = await fetchAdminLogs({
      accessToken: authStore.accessToken,
      action: action.value.trim(),
      userId: userId.value,
      startAt: buildApiDateTime(startAt.value),
      endAt: buildApiDateTime(endAt.value),
      page: page.value,
      pageSize: pageSize.value
    });
    items.value = payload.items || [];
    total.value = payload.total || 0;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "加载操作日志失败";
  } finally {
    loading.value = false;
  }
}

async function search() {
  page.value = 1;
  await loadLogs();
}

async function resetFilters() {
  action.value = "";
  userId.value = null;
  startAt.value = "";
  endAt.value = "";
  page.value = 1;
  await loadLogs();
}

async function onPageChange(event) {
  page.value = event.page + 1;
  pageSize.value = event.rows;
  await loadLogs();
}

onMounted(() => {
  loadLogs();
});
</script>

<template>
  <Card>
    <template #title>操作日志</template>
    <template #subtitle>管理员审计视图（MVP）</template>
    <template #content>
      <div class="file-filter-row">
        <div class="file-filter-item">
          <label class="auth-label">操作类型</label>
          <InputText v-model="action" placeholder="例如：login、download" />
        </div>
        <div class="file-filter-item">
          <label class="auth-label">用户ID</label>
          <InputNumber v-model="userId" :useGrouping="false" />
        </div>
        <div class="file-filter-item">
          <label class="auth-label">开始时间</label>
          <input v-model="startAt" class="native-input" type="datetime-local" />
        </div>
      </div>

      <div class="file-filter-row">
        <div class="file-filter-item">
          <label class="auth-label">结束时间</label>
          <input v-model="endAt" class="native-input" type="datetime-local" />
        </div>
      </div>

      <div class="file-filter-actions">
        <Button label="查询" icon="pi pi-search" :loading="loading" @click="search" />
        <Button label="重置" severity="secondary" text @click="resetFilters" />
      </div>

      <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
      <div class="health-row">
        <Tag severity="info" value="管理员视图" />
        <Tag v-if="action" severity="secondary" :value="`动作：${action}`" />
        <span class="health-message">当前结果 {{ total }} 条日志</span>
      </div>

      <Message v-if="!loading && items.length === 0" severity="secondary" :closable="false">
        当前筛选条件下没有日志记录。
      </Message>

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
        <Column field="id" header="ID"></Column>
        <Column field="user_id" header="用户ID"></Column>
        <Column field="username_snapshot" header="用户名"></Column>
        <Column field="action" header="操作"></Column>
        <Column field="target_type" header="目标类型"></Column>
        <Column field="target_id" header="目标ID"></Column>
        <Column header="详情">
          <template #body="{ data }">
            <span class="log-detail-text">{{ formatDetail(data.detail_json) }}</span>
          </template>
        </Column>
        <Column header="时间">
          <template #body="{ data }">{{ formatTime(data.created_at) }}</template>
        </Column>
      </DataTable>
    </template>
  </Card>
</template>
