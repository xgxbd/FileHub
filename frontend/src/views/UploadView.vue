<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import Button from "primevue/button";
import Card from "primevue/card";
import Message from "primevue/message";
import ProgressBar from "primevue/progressbar";
import Tag from "primevue/tag";

import { completeUploadSession, createUploadSession, uploadChunk } from "../api/upload";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const selectedFiles = ref([]);
const uploadQueue = ref([]);
const uploadLoading = ref(false);
const uploadProgress = ref(0);
const uploadMessage = ref("");
const uploadError = ref("");
const targetFolder = ref("");
const fileInputRef = ref(null);
const currentUploadingName = ref("");
const cancelRequested = ref(false);
const activeAbortController = ref(null);

function normalizeFolder(raw) {
  const cleaned = String(raw || "")
    .replace(/\\/g, "/")
    .split("/")
    .map((part) => part.trim())
    .filter((part) => part && part !== "." && part !== "..")
    .join("/");
  return cleaned;
}

function mergedFileName(fileName) {
  const folder = normalizeFolder(targetFolder.value);
  return folder ? `${folder}/${fileName}` : fileName;
}

const targetFolderLabel = computed(() => {
  const folder = normalizeFolder(targetFolder.value);
  return folder ? `/${folder}/` : "/";
});

function resetUploadState() {
  uploadProgress.value = 0;
  uploadMessage.value = "";
  uploadError.value = "";
}

function isAbortError(err) {
  if (!err) return false;
  return err.name === "AbortError" || String(err.message || "").toLowerCase().includes("abort");
}

function recalculateUploadProgress() {
  const totalBytes = selectedFiles.value.reduce((sum, file) => sum + file.size, 0);
  if (totalBytes <= 0) {
    uploadProgress.value = 0;
    return;
  }

  const finishedBytes = uploadQueue.value.reduce((sum, item, index) => {
    const fileSize = selectedFiles.value[index]?.size || item.size || 0;
    const ratio = item.status === "success" ? 1 : Math.min(item.progress, 100) / 100;
    return sum + fileSize * ratio;
  }, 0);

  uploadProgress.value = Math.min(100, Math.floor((finishedBytes / totalBytes) * 100));
}

function syncSelectedFiles(files) {
  selectedFiles.value = files;
  uploadQueue.value = files.map((file, index) => ({
    id: `${Date.now()}-${index}-${file.name}`,
    name: file.name,
    path: mergedFileName(file.name),
    size: file.size,
    status: "pending",
    progress: 0,
    message: ""
  }));
  currentUploadingName.value = "";
  cancelRequested.value = false;
  resetUploadState();
  recalculateUploadProgress();
}

function onFileChange(event) {
  const files = Array.from(event.target.files || []);
  syncSelectedFiles(files);
  event.target.value = "";
}

function openFilePicker() {
  fileInputRef.value?.click();
}

function onDrop(event) {
  event.preventDefault();
  const files = Array.from(event.dataTransfer?.files || []);
  if (files.length > 0) {
    syncSelectedFiles(files);
  }
}

function onDragOver(event) {
  event.preventDefault();
}

function markRemainingQueueCanceled(startIndex) {
  for (let index = startIndex; index < uploadQueue.value.length; index += 1) {
    const queueItem = uploadQueue.value[index];
    if (!queueItem || queueItem.status === "success") {
      continue;
    }
    queueItem.status = "canceled";
    queueItem.progress = 0;
    queueItem.message = "已取消";
  }
}

async function startUpload({ retryUnfinished = false } = {}) {
  if (selectedFiles.value.length === 0) {
    uploadError.value = "请先选择至少一个文件";
    return;
  }
  if (!authStore.accessToken) {
    uploadError.value = "当前未登录";
    return;
  }
  if (uploadLoading.value) {
    return;
  }

  const candidateIndexes = uploadQueue.value
    .map((item, index) => ({ item, index }))
    .filter(({ item }) => {
      if (retryUnfinished) {
        return item.status !== "success";
      }
      return true;
    })
    .map(({ index }) => index);

  if (candidateIndexes.length === 0) {
    uploadError.value = "没有可上传的文件";
    return;
  }

  if (retryUnfinished) {
    candidateIndexes.forEach((index) => {
      uploadQueue.value[index].status = "pending";
      uploadQueue.value[index].progress = 0;
      uploadQueue.value[index].message = "";
    });
  }

  uploadLoading.value = true;
  cancelRequested.value = false;
  resetUploadState();
  const chunkSize = 1024 * 1024;
  let successCount = 0;
  let failedCount = 0;
  let canceledCount = 0;

  try {
    for (const fileIndex of candidateIndexes) {
      if (cancelRequested.value) {
        markRemainingQueueCanceled(fileIndex);
        break;
      }

      const file = selectedFiles.value[fileIndex];
      const totalChunks = Math.ceil(file.size / chunkSize);
      const queueItem = uploadQueue.value[fileIndex];
      queueItem.status = "uploading";
      queueItem.message = "上传中";
      queueItem.progress = 0;
      currentUploadingName.value = queueItem.path;
      activeAbortController.value = new AbortController();

      try {
        const session = await createUploadSession({
          accessToken: authStore.accessToken,
          payload: {
            file_name: mergedFileName(file.name),
            total_size: file.size,
            chunk_size: chunkSize,
            total_chunks: totalChunks,
            mime_type: file.type || "application/octet-stream"
          },
          signal: activeAbortController.value.signal
        });

        for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex += 1) {
          if (cancelRequested.value) {
            throw new DOMException("upload aborted", "AbortError");
          }
          const start = chunkIndex * chunkSize;
          const end = Math.min(start + chunkSize, file.size);
          const blob = file.slice(start, end);

          await uploadChunk({
            accessToken: authStore.accessToken,
            uploadId: session.upload_id,
            chunkIndex,
            chunkBlob: blob,
            signal: activeAbortController.value.signal
          });

          queueItem.progress = Math.min(95, Math.floor(((chunkIndex + 1) / totalChunks) * 95));
          recalculateUploadProgress();
        }

        await completeUploadSession({
          accessToken: authStore.accessToken,
          uploadId: session.upload_id,
          signal: activeAbortController.value.signal
        });

        successCount += 1;
        queueItem.status = "success";
        queueItem.progress = 100;
        queueItem.message = "上传完成";
        recalculateUploadProgress();
      } catch (err) {
        if (cancelRequested.value || isAbortError(err)) {
          canceledCount += 1;
          queueItem.status = "canceled";
          queueItem.message = "已取消";
        } else {
          failedCount += 1;
          queueItem.status = "error";
          queueItem.message = err instanceof Error ? err.message : "上传失败";
        }
        recalculateUploadProgress();
      } finally {
        activeAbortController.value = null;
      }
    }

    currentUploadingName.value = "";
    if (cancelRequested.value || canceledCount > 0) {
      markRemainingQueueCanceled(0);
      const totalCanceled = uploadQueue.value.filter((item) => item.status === "canceled").length;
      uploadMessage.value = `已停止剩余上传任务，已取消 ${totalCanceled} 个文件`;
    } else if (failedCount > 0) {
      uploadError.value = `${failedCount} 个文件上传失败，请查看队列结果`;
    }
    if (successCount === 1 && failedCount === 0 && canceledCount === 0 && candidateIndexes.length === 1) {
      uploadMessage.value = `上传完成：${uploadQueue.value[candidateIndexes[0]].path}`;
    } else if (successCount > 0 && failedCount === 0 && canceledCount === 0) {
      uploadMessage.value = `已完成 ${successCount} 个文件上传`;
    }
  } catch (err) {
    uploadError.value = err instanceof Error ? err.message : "上传失败";
  } finally {
    currentUploadingName.value = "";
    uploadLoading.value = false;
    activeAbortController.value = null;
    recalculateUploadProgress();
  }
}

function stopUploadQueue() {
  if (!uploadLoading.value) {
    return;
  }
  cancelRequested.value = true;
  activeAbortController.value?.abort();
}

async function retryUnfinishedUploads() {
  await startUpload({ retryUnfinished: true });
}

onMounted(() => {
  const folder = typeof route.query.folder === "string" ? route.query.folder : "";
  targetFolder.value = normalizeFolder(folder);
});
</script>

<template>
  <Card>
    <template #title>文件上传页</template>
    <template #subtitle>分片上传、队列、断点续传</template>
    <template #content>
      <div class="upload-layout">
        <section class="panel">
          <div class="file-filter-actions">
            <Tag severity="info" :value="`目标目录：${targetFolderLabel}`" />
          </div>
          <div class="dropzone" @click="openFilePicker" @drop="onDrop" @dragover="onDragOver">
            拖拽多个文件到此处或点击选择文件
          </div>
          <div class="upload-actions" style="margin-top: 10px">
            <input ref="fileInputRef" type="file" multiple style="display: none" @change="onFileChange" />
            <Button label="选择文件" severity="secondary" text icon="pi pi-folder-open" @click="openFilePicker" />
            <Button label="开始上传" icon="pi pi-upload" :loading="uploadLoading" @click="startUpload" />
            <Button
              label="停止队列"
              severity="danger"
              text
              icon="pi pi-stop"
              :disabled="!uploadLoading"
              @click="stopUploadQueue"
            />
            <Button
              label="重试未完成"
              severity="secondary"
              text
              icon="pi pi-refresh"
              :disabled="uploadLoading || !uploadQueue.some((item) => ['error', 'canceled'].includes(item.status))"
              @click="retryUnfinishedUploads"
            />
            <Button label="返回文件列表" severity="secondary" text @click="router.push('/files')" />
          </div>
          <div class="upload-status">
            <span v-if="selectedFiles.length > 0">已选择 {{ selectedFiles.length }} 个文件</span>
            <span v-else>未选择文件</span>
          </div>
          <div class="upload-status" v-if="currentUploadingName">当前上传：{{ currentUploadingName }}</div>
          <ProgressBar :value="uploadProgress"></ProgressBar>
          <Message v-if="uploadMessage" severity="success" :closable="false">{{ uploadMessage }}</Message>
          <Message v-if="uploadError" severity="error" :closable="false">{{ uploadError }}</Message>
        </section>

        <section class="panel queue">
          <h3>上传队列</h3>
          <div v-if="uploadQueue.length === 0" class="upload-status">尚未选择文件</div>
          <div v-for="item in uploadQueue" :key="item.id" class="item">
            <div class="queue-item-header">
              <strong>{{ item.name }}</strong>
              <span>{{
                item.status === "pending"
                  ? "待上传"
                  : item.status === "uploading"
                    ? "上传中"
                    : item.status === "success"
                      ? "已完成"
                      : item.status === "canceled"
                        ? "已取消"
                        : "失败"
              }}</span>
            </div>
            <div class="upload-status">{{ item.path }}</div>
            <div class="bar"><span :style="{ width: `${item.progress}%` }"></span></div>
            <div class="upload-status" v-if="item.message">{{ item.message }}</div>
          </div>
        </section>
      </div>
    </template>
  </Card>
</template>
