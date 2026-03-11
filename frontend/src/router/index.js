import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

const LoginView = () => import("../views/LoginView.vue");
const RegisterView = () => import("../views/RegisterView.vue");
const FileCenterView = () => import("../views/FileCenterView.vue");
const RecycleBinView = () => import("../views/RecycleBinView.vue");
const AdminLogsView = () => import("../views/AdminLogsView.vue");
const AdminFilesView = () => import("../views/AdminFilesView.vue");
const UploadView = () => import("../views/UploadView.vue");
const PreviewView = () => import("../views/PreviewView.vue");

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/files"
    },
    {
      path: "/login",
      name: "login",
      component: LoginView,
      meta: {
        guestOnly: true,
        pageTitle: "登录页",
        pageSubtitle: "账号登录与注册入口",
        pageKpis: ["安全登录", "JWT 会话", "双角色"]
      }
    },
    {
      path: "/register",
      name: "register",
      component: RegisterView,
      meta: {
        guestOnly: true,
        pageTitle: "注册页",
        pageSubtitle: "创建账号并进入文件仓库",
        pageKpis: ["邮箱注册", "密码策略", "即刻可用"]
      }
    },
    {
      path: "/files",
      name: "files",
      component: FileCenterView,
      meta: {
        requiresAuth: true,
        pageTitle: "文件仓库首页 / 文件列表",
        pageSubtitle: "文件检索、筛选、批量操作",
        pageKpis: ["文件中心", "元数据检索", "在线操作"]
      }
    },
    {
      path: "/upload",
      name: "upload",
      component: UploadView,
      meta: {
        requiresAuth: true,
        pageTitle: "文件上传页",
        pageSubtitle: "分片上传、队列、断点续传",
        pageKpis: ["分片上传", "上传队列", "失败重试"]
      }
    },
    {
      path: "/preview/:fileId?",
      name: "preview",
      component: PreviewView,
      meta: {
        requiresAuth: true,
        pageTitle: "文件详情 / 预览页",
        pageSubtitle: "文件内容预览与元数据",
        pageKpis: ["图片/PDF/TXT", "权限校验", "下载入口"]
      }
    },
    {
      path: "/recycle",
      name: "recycle",
      component: RecycleBinView,
      meta: {
        requiresAuth: true,
        pageTitle: "回收站页",
        pageSubtitle: "恢复与彻底删除",
        pageKpis: ["软删除", "恢复", "彻底删除"]
      }
    },
    {
      path: "/admin/logs",
      name: "admin-logs",
      component: AdminLogsView,
      meta: {
        requiresAuth: true,
        requiresAdmin: true,
        pageTitle: "操作日志页",
        pageSubtitle: "审计筛选与行为追踪",
        pageKpis: ["审计查询", "行为追踪", "风险操作"]
      }
    },
    {
      path: "/admin/files",
      name: "admin-files",
      component: AdminFilesView,
      meta: {
        requiresAuth: true,
        requiresAdmin: true,
        pageTitle: "后台管理页",
        pageSubtitle: "容量、活跃与文件状态管理",
        pageKpis: ["全量文件", "状态管理", "管理动作"]
      }
    }
  ]
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();
  authStore.syncLocalTokens();

  if (authStore.accessToken && !authStore.user) {
    try {
      await authStore.loadProfile();
    } catch {
      authStore.logout();
    }
  }

  if (to.meta.requiresAuth && !authStore.accessToken) {
    return { name: "login", query: { redirect: to.fullPath } };
  }

  if (to.meta.requiresAdmin && authStore.user?.role !== "admin") {
    return { name: "files" };
  }

  if (to.meta.guestOnly && authStore.accessToken) {
    return { name: "files" };
  }

  return true;
});

export default router;
