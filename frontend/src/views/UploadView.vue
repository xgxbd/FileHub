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

const selectedFile = ref(null);
const uploadLoading = ref(false);
const uploadProgress = ref(0);
const uploadMessage = ref("");
const uploadError = ref("");
const targetFolder = ref("");
const fileInputRef = ref(null);

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

function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null;
  uploadProgress.value = 0;
  uploadMessage.value = "";
  uploadError.value = "";
}

function pickFile(file) {
  selectedFile.value = file || null;
  uploadProgress.value = 0;
  uploadMessage.value = "";
  uploadError.value = "";
}

function openFilePicker() {
  fileInputRef.value?.click();
}

function onDrop(event) {
  event.preventDefault();
  const file = event.dataTransfer?.files?.[0] || null;
  if (file) {
    pickFile(file);
  }
}

function onDragOver(event) {
  event.preventDefault();
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
        file_name: mergedFileName(selectedFile.value.name),
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
      uploadProgress.value = Math.min(95, Math.floor(((index + 1) / totalChunks) * 95));
    }

    await completeUploadSession({
      accessToken: authStore.accessToken,
      uploadId: session.upload_id
    });

    uploadProgress.value = 100;
    uploadMessage.value = `上传完成：${mergedFileName(selectedFile.value.name)}`;
  } catch (err) {
    uploadError.value = err instanceof Error ? err.message : "上传失败";
  } finally {
    uploadLoading.value = false;
  }
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
            拖拽文件到此处或点击选择文件
          </div>
          <div class="upload-actions" style="margin-top: 10px">
            <input ref="fileInputRef" type="file" style="display: none" @change="onFileChange" />
            <Button label="选择文件" severity="secondary" text icon="pi pi-folder-open" @click="openFilePicker" />
            <Button label="开始上传" icon="pi pi-upload" :loading="uploadLoading" @click="startUpload" />
            <Button label="返回文件列表" severity="secondary" text @click="router.push('/files')" />
          </div>
          <div class="upload-status">
            <span v-if="selectedFile">已选择：{{ mergedFileName(selectedFile.name) }}</span>
            <span v-else>未选择文件</span>
          </div>
          <ProgressBar :value="uploadProgress"></ProgressBar>
          <Message v-if="uploadMessage" severity="success" :closable="false">{{ uploadMessage }}</Message>
          <Message v-if="uploadError" severity="error" :closable="false">{{ uploadError }}</Message>
        </section>

        <section class="panel queue">
          <h3>上传策略</h3>
          <div class="item">分片大小：1 MB<div class="bar"><span style="width: 100%"></span></div></div>
          <div class="item">并发策略：串行（MVP）<div class="bar"><span style="width: 45%"></span></div></div>
          <div class="item">失败重试：手动重试<div class="bar"><span style="width: 70%"></span></div></div>
        </section>
      </div>
    </template>
  </Card>
</template>
