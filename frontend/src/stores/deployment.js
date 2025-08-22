// src/stores/deployment.js
import { defineStore } from 'pinia';
import apiClient from '@/api/apiClient';

export const useDeploymentStore = defineStore('deployment', {
  state: () => ({
    isDeploying: false,
    results: null, // 存放部署结果
    error: null,
  }),
  actions: {
    async triggerDeployment() {
      this.isDeploying = true;
      this.results = null; // 清空上次的结果
      this.error = null;
      try {
        const response = await apiClient.post('/deploy');
        this.results = response.data.results;
        return true;
      } catch (error) {
        this.error = 'Deployment failed with a network or server error.';
        console.error(error);
        return false;
      } finally {
        this.isDeploying = false;
      }
    },
    // 用于关闭结果面板
    clearResults() {
      this.results = null;
      this.error = null;
    }
  },
});