import { defineStore } from "pinia";

import { fetchCurrentUser, login as loginApi, refresh as refreshApi, register as registerApi } from "../api/auth";
import { clearTokens, readTokens, saveTokens } from "../utils/token";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    accessToken: "",
    refreshToken: "",
    user: null,
    loading: false
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken && state.user)
  },
  actions: {
    syncLocalTokens() {
      const { accessToken, refreshToken } = readTokens();
      this.accessToken = accessToken;
      this.refreshToken = refreshToken;
    },
    async register(payload) {
      this.loading = true;
      try {
        await registerApi(payload);
        return await this.login({
          account: payload.username,
          password: payload.password
        });
      } finally {
        this.loading = false;
      }
    },
    async login(payload) {
      this.loading = true;
      try {
        const tokens = await loginApi(payload);
        this.accessToken = tokens.access_token;
        this.refreshToken = tokens.refresh_token;
        saveTokens({ accessToken: this.accessToken, refreshToken: this.refreshToken });
        await this.loadProfile();
      } finally {
        this.loading = false;
      }
    },
    async loadProfile() {
      if (!this.accessToken) {
        this.user = null;
        return;
      }
      this.user = await fetchCurrentUser(this.accessToken);
    },
    async refreshSession() {
      if (!this.refreshToken) return false;
      try {
        const tokens = await refreshApi({ refresh_token: this.refreshToken });
        this.accessToken = tokens.access_token;
        this.refreshToken = tokens.refresh_token;
        saveTokens({ accessToken: this.accessToken, refreshToken: this.refreshToken });
        await this.loadProfile();
        return true;
      } catch {
        this.logout();
        return false;
      }
    },
    logout() {
      this.accessToken = "";
      this.refreshToken = "";
      this.user = null;
      clearTokens();
    },
    async initSession() {
      this.syncLocalTokens();
      if (!this.accessToken) return;
      try {
        await this.loadProfile();
      } catch {
        await this.refreshSession();
      }
    }
  }
});
