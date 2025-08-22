<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>Server Management</span>
          <el-button type="primary" @click="openAddDialog">
             <el-icon><Plus /></el-icon>
             <span style="margin-left: 5px;">Add Server</span>
          </el-button>
        </div>
      </template>

      <el-table :data="serverStore.servers" v-loading="serverStore.isLoading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="Alias (Hostname)" min-width="180">
          <template #default="scope">
            <strong>{{ scope.row.alias }}</strong>
            <div class="hostname-text">({{ scope.row.hostname }})</div>
          </template>
        </el-table-column>
        <el-table-column prop="ssh_user" label="User" width="120" />
        <el-table-column prop="ssh_port" label="SSH Port" width="100" />
        <el-table-column prop="role" label="Role" width="100">
          <template #default="scope">
            <el-tag :type="getRoleTagType(scope.row.role)">{{ scope.row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Status" width="140">
           <template #default="scope">
            <div v-if="scope.row.isStatusLoading">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span style="font-size: 12px; color: #909399; margin-left: 4px;">checking...</span>
            </div>
            <div v-else-if="scope.row.status" class="status-tags">
              <el-tag v-if="scope.row.status.server_status" :type="getStatusTagType(scope.row.status.server_status)" size="small">
                Server: {{ scope.row.status.server_status }}
              </el-tag>
              <el-tag v-if="scope.row.status.client_status" :type="getStatusTagType(scope.row.status.client_status)" size="small">
                Client: {{ scope.row.status.client_status }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="Actions" width="280">
          <template #default="scope">
            <el-tooltip content="Refresh Status" placement="top">
              <el-button
                circle
                :icon="Refresh"
                size="small"
                @click="serverStore.checkServerStatus(scope.row.id)"
                :loading="scope.row.isStatusLoading"
              />
            </el-tooltip>

            <el-dropdown trigger="click" style="margin-left: 10px;">
              <el-button size="small">
                Logs<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-if="['server', 'both'].includes(scope.row.role)" @click="viewLogs(scope.row, 'server')">Server Logs</el-dropdown-item>
                  <el-dropdown-item v-if="['client', 'both'].includes(scope.row.role)" @click="viewLogs(scope.row, 'client')">Client Logs</el-dropdown-item>
                  <el-dropdown-item v-if="scope.row.role === 'server'" disabled>No client logs</el-dropdown-item>
                  <el-dropdown-item v-if="scope.row.role === 'client'" disabled>No server logs</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            
            <el-button style="margin-left: 10px;" type="primary" size="small" @click="openEditDialog(scope.row)">Edit</el-button>

            <el-button 
              type="warning" 
              size="small" 
              @click="handleUninstall(scope.row)"
              :loading="scope.row.isUninstalling"
            >
              Uninstall
            </el-button>
            
            <el-tooltip
              :content="isDeletable(scope.row) ? 'Delete from list' : 'Please uninstall the service first'"
              placement="top"
            >
              <el-button
                type="danger"
                size="small"
                @click="handleDelete(scope.row)"
                :disabled="!isDeletable(scope.row)"
              >
                Delete
              </el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" :close-on-click-modal="false">
      <ServerForm :initial-data="serverToEdit" @submit-success="dialogVisible = false" @cancel="dialogVisible = false" />
    </el-dialog>
    <el-dialog v-model="logDialog.visible" :title="logDialog.title" width="70%" top="5vh">
      <el-scrollbar height="70vh">
        <pre class="log-content">{{ logDialog.content }}</pre>
      </el-scrollbar>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useServerStore } from '@/stores/servers';
import ServerForm from '@/components/ServerForm.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Refresh, Loading, ArrowDown } from '@element-plus/icons-vue';

const serverStore = useServerStore();
const dialogVisible = ref(false);
const serverToEdit = ref(null);
const dialogTitle = computed(() => (serverToEdit.value ? `Edit Server: ${serverToEdit.value.alias}` : 'Add New Server'));

const logDialog = ref({
  visible: false,
  title: '',
  content: 'Loading logs...',
});

const openAddDialog = () => {
  serverToEdit.value = null;
  dialogVisible.value = true;
};
const openEditDialog = (server) => {
  serverToEdit.value = { ...server };
  dialogVisible.value = true;
};

// --- 新增：判断服务器是否可删除的辅助函数 ---
const isDeletable = (server) => {
  // 如果状态还未检查，不允许删除
  if (!server.status) return false;
  // 如果 server 或 client 任意一个服务是 active 状态，不允许删除
  if (server.status.server_status === 'active' || server.status.client_status === 'active') {
    return false;
  }
  // 其他情况（inactive, failed, unknown）都允许删除
  return true;
};

const handleUninstall = (server) => {
  ElMessageBox.confirm(
    `This will connect to "${server.alias}" and attempt to STOP and REMOVE all rathole services and configuration files. This action cannot be undone.`,
    'Confirm Uninstall',
    { confirmButtonText: 'Proceed', cancelButtonText: 'Cancel', type: 'warning' }
  ).then(async () => {
    const result = await serverStore.uninstallServer(server.id);
    if (result.success) ElMessage({ type: 'success', message: result.message });
    else ElMessage({ type: 'error', message: result.message });
  }).catch(() => { ElMessage({ type: 'info', message: 'Uninstall canceled' }); });
};

const handleDelete = (server) => {
  ElMessageBox.confirm(
    `This will permanently delete "${server.alias}" from the management list. This server's service appears to be inactive. Continue?`,
    'Confirm Deletion',
    { confirmButtonText: 'OK', cancelButtonText: 'Cancel', type: 'warning' }
  ).then(async () => {
    const success = await serverStore.deleteServer(server.id);
    if (success) ElMessage({ type: 'success', message: 'Delete completed' });
    else ElMessage({ type: 'error', message: serverStore.error });
  }).catch(() => { ElMessage({ type: 'info', message: 'Delete canceled' }); });
};

const viewLogs = async (server, serviceRole) => {
  logDialog.value.visible = true;
  logDialog.value.title = `Logs for ${server.alias} (${serviceRole})`;
  logDialog.value.content = 'Loading logs...';
  const logs = await serverStore.fetchServerLogs(server.id, serviceRole);
  logDialog.value.content = logs;
};

const getRoleTagType = (role) => {
  if (role === 'server') return 'success';
  if (role === 'client') return 'warning';
  return 'info';
};
const getStatusTagType = (status) => {
  if (status === 'active') return 'success';
  if (status === 'failed' || status === 'inactive') return 'danger';
  return 'info';
};

onMounted(async () => {
  await serverStore.fetchServers();
  serverStore.servers.forEach(server => {
    serverStore.checkServerStatus(server.id);
  });
});
</script>

<style scoped>
/* ... (所有样式保持不变) ... */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.status-tags .el-tag {
  display: block;
  width: fit-content;
}
.status-tags .el-tag + .el-tag {
  margin-top: 4px;
}
.el-table .el-button + .el-button,
.el-table .el-dropdown + .el-button,
.el-table .el-tooltip + .el-button {
  margin-left: 8px;
}
.log-content {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Courier New', Courier, monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>