// src/stores/rules.js
import { defineStore } from 'pinia';
import apiClient from '@/api/apiClient';
import { useServerStore } from './servers'; // 导入 server store

export const useRuleStore = defineStore('rules', {
  state: () => ({
    rules: [],
    isLoading: false,
    error: null,
  }),
  actions: {
    // action 1: 获取规则列表
    async fetchRules() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await apiClient.get('/rules');
        this.rules = response.data;
      } catch (error) {
        this.error = 'Failed to fetch rules.';
        console.error(error);
      } finally {
        this.isLoading = false;
      }
    },

    // action 2: 添加新规则
    async addRule(ruleData) {
      this.isLoading = true;
      this.error = null;
      try {
        await apiClient.post('/rules', ruleData);
        await this.fetchRules(); // 成功后刷新列表
        return true;
      } catch (error) {
        this.error = 'Failed to add rule.';
         if (error.response && error.response.data && error.response.data.detail) {
          this.error = `Failed to add rule: ${error.response.data.detail}`;
        }
        console.error(error);
        return false;
      } finally {
        this.isLoading = false;
      }
    },

    // action 3: 删除规则
    async deleteRule(ruleId) {
      this.error = null;
      try {
        await apiClient.delete(`/rules/${ruleId}`);
        this.rules = this.rules.filter(rule => rule.id !== ruleId);
        return true;
      } catch (error) {
        this.error = 'Failed to delete rule.';
        console.error(error);
        return false;
      }
    },

    // 一个辅助 action，确保创建规则前，我们有可用的服务器列表
    async fetchPrerequisites() {
      const serverStore = useServerStore();
      if (serverStore.servers.length === 0) {
        await serverStore.fetchServers();
      }
    },
    
    async updateRule(ruleId, ruleData) {
      this.isLoading = true;
      this.error = null;
      try {
        // 注意：我们尚未创建后端 PUT /api/rules/{id} 接口，但先把前端逻辑写好
        const response = await apiClient.put(`/rules/${ruleId}`, ruleData);
        const index = this.rules.findIndex(r => r.id === ruleId);
        if (index !== -1) {
          // 后端应返回更新后的完整数据，包含别名等
          this.rules[index] = response.data;
        }
        return true;
      } catch (error) {
        this.error = 'Failed to update rule.';
        if (error.response?.data?.detail) {
          this.error = `Failed to update rule: ${error.response.data.detail}`;
        }
        return false;
      } finally {
        this.isLoading = false;
      }
    },
  },
});