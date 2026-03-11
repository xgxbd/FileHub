<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

import Button from "primevue/button";
import Card from "primevue/card";
import Message from "primevue/message";
import ProgressBar from "primevue/progressbar";

import { completeUploadSession, createUploadSession, uploadChunk } from "../api/upload";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const selectedFile = ref(null);
const uploadLoading = ref(false);
const uploadProgress = ref(0);
const uploadMessage = ref("");
const uploadError = ref("");

function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null;
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
  } catch (err) {
    uploadError.value = err instanceof Error ? err.message : "上传失败";
  } finally {
    uploadLoading.value = false;
  }
}
</script>

<template>
  <Card>
    <template #title>文件上传页</template>
    <template #subtitle>分片上传、队列、断点续传</template>
    <template #content>
      <div class="upload-layout">
        <section class="panel">
          <div class="dropzone">拖拽文件到此处或点击上传</div>
          <div class="upload-actions" style="margin-top: 10px">
            <input type="file" @change="onFileChange" />
            <Button label="开始上传" icon="pi pi-upload" :loading="uploadLoading" @click="startUpload" />
            <Button label="返回文件列表" severity="secondary" text @click="router.push('/files')" />
          </div>
          <div class="upload-status">
            <span v-if="selectedFile">已选择：{{ selectedFile.name }}</span>
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
