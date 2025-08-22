// src/stores/servers.js
import { defineStore } from 'pinia';
import apiClient from '@/api/apiClient';

export const useServerStore = defineStore('servers', {
  state: () => ({
    servers: [],
    isLoading: false,
    error: null,
  }),
  actions: {
    async fetchServers() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await apiClient.get('/servers');
        this.servers = response.data;
      } catch (error) {
        this.error = 'Failed to fetch servers.';
        console.error(error);
      } finally {
        this.isLoading = false;
      }
    },

    // --- 新增 action ---
    async addServer(serverData) {
      this.isLoading = true; // 可以共用一个加载状态
      this.error = null;
      try {
        // 向后端API发送POST请求
        await apiClient.post('/servers', serverData);

        // 添加成功后，调用 fetchServers 重新获取完整列表
        // 这是最可靠的方式，能确保前端数据和后端数据库完全同步
        await this.fetchServers();
        return true; // 返回 true 表示成功
      } catch (error) {
        this.error = 'Failed to add server.';
        if (error.response && error.response.data && error.response.data.detail) {
          // 显示后端返回的具体错误信息
          this.error = `Failed to add server: ${error.response.data.detail}`;
        }
        console.error(error);
        return false; // 返回 false 表示失败
      } finally {
        this.isLoading = false;
      }
    },

    // 删除 action
    async deleteServer(serverId) {
      // 注意：这里我们不设置全局isLoading，因为删除是单个条目的操作，
      // 整个列表变灰或显示加载中，用户体验不佳。
      this.error = null;
      try {
        await apiClient.delete(`/servers/${serverId}`);

        // 删除成功后，直接从前端的 state 数组中移除该项
        // 这种方式比重新 fetch 整个列表更快，用户体验更好
        this.servers = this.servers.filter(server => server.id !== serverId);

        return true;
      } catch (error) {
        this.error = 'Failed to delete server.';
        if (error.response && error.response.data && error.response.data.detail) {
          this.error = `Failed to delete server: ${error.response.data.detail}`;
        }
        console.error(error);
        return false;
      }
    },
    async updateServer(serverId, serverData) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await apiClient.put(`/servers/${serverId}`, serverData);
        // 更新成功后，在本地数组中找到并替换该项
        const index = this.servers.findIndex(s => s.id === serverId);
        if (index !== -1) {
          this.servers[index] = response.data;
        }
        return true;
      } catch (error) {
         this.error = 'Failed to update server.';
         if (error.response?.data?.detail) {
          this.error = `Failed to update server: ${error.response.data.detail}`;
        }
        return false;
      } finally {
        this.isLoading = false;
      }
    },

    async checkServerStatus(serverId) {
      const server = this.servers.find(s => s.id === serverId);
      if (!server) return;

      // 为单个服务器设置加载状态，避免全局加载
      server.isStatusLoading = true;
      try {
        const response = await apiClient.get(`/servers/${serverId}/status`);
        // 将返回的状态对象直接赋给服务器对象的一个新属性
        server.status = response.data;
      } catch (error) {
        console.error(`Failed to check status for server ${serverId}:`, error);
        server.status = { server_status: 'unknown', client_status: 'unknown' };
      } finally {
        server.isStatusLoading = false;
      }
    },

    async fetchServerLogs(serverId, serviceRole) {
      try {
        const response = await apiClient.get(`/servers/${serverId}/logs`, {
          params: { service_role: serviceRole }
        });
        return response.data.logs;
      } catch (error) {
        console.error(`Failed to fetch logs for server ${serverId}:`, error);
        return 'Error loading logs. See browser console for details.';
      }
    },

        async uninstallServer(serverId) {
      // 这是一个特殊操作，我们为它单独管理加载和错误状态
      const server = this.servers.find(s => s.id === serverId);
      if (!server) return { success: false, message: "Server not found." };
      
      server.isUninstalling = true; // 为单个服务器设置卸载状态
      this.error = null;
      try {
        const response = await apiClient.post(`/servers/${serverId}/uninstall`);
        // 卸载后，最好刷新一下状态，它应该会变为 inactive 或 unknown
        this.checkServerStatus(serverId);
        return { success: true, message: response.data.message };
      } catch (error) {
        const errorMessage = error.response?.data?.detail || 'Failed to uninstall services.';
        this.error = errorMessage;
        return { success: false, message: errorMessage };
      } finally {
        if(server) server.isUninstalling = false;
      }
    },


  },
});