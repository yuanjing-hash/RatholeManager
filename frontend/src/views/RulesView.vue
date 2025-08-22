<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>Forwarding Rules Management</span>
          <el-button type="primary" @click="openAddDialog">
            <el-icon><Plus /></el-icon>
            <span style="margin-left: 5px;">Add Rule</span>
          </el-button>
        </div>
      </template>

      <el-table :data="ruleStore.rules" v-loading="ruleStore.isLoading" style="width: 100%">
        <template #empty>
          <el-empty description="No rules found. Click 'Add Rule' to create one." />
        </template>
        
        <el-table-column prop="name" label="Rule Name" min-width="150" />
        
        <el-table-column label="Client (Source)" min-width="180">
          <template #default="scope">
            <strong>{{ scope.row.client_alias }}</strong>
            <div class="hostname-text">({{ scope.row.client_hostname }})</div>
          </template>
        </el-table-column>
        
        <el-table-column label="Forwarding" min-width="180">
          <template #default="scope">
            <div class="forwarding-cell">
              <el-tag type="info">{{ scope.row.local_port }}</el-tag>
              <div class="forwarding-arrow">
                <el-icon><Right /></el-icon>
                <span class="rule-type-text">{{ scope.row.rule_type.toUpperCase() }}</span>
              </div>
              <el-tag type="success">{{ scope.row.remote_port }}</el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="Target Server (Destination)" min-width="180">
          <template #default="scope">
            <strong>{{ scope.row.server_alias }}</strong>
            <div class="hostname-text">({{ scope.row.server_hostname }})</div>
          </template>
        </el-table-column>
        
        <el-table-column label="Actions" width="180" fixed="right">
          <template #default="scope">
            <el-button type="primary" size="small" @click="openEditDialog(scope.row)">Edit</el-button>
            <el-button type="danger" size="small" @click="handleDelete(scope.row)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" :close-on-click-modal="false">
      <RuleForm 
        :initial-data="ruleToEdit"
        @submit-success="dialogVisible = false"
        @cancel="dialogVisible = false"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRuleStore } from '@/stores/rules';
import { useServerStore } from '@/stores/servers'; // Also import server store for prerequisites
import RuleForm from '@/components/RuleForm.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Right } from '@element-plus/icons-vue';

const ruleStore = useRuleStore();
const serverStore = useServerStore(); // Needed for the prerequisite check

const dialogVisible = ref(false);
const ruleToEdit = ref(null);
const dialogTitle = computed(() => (ruleToEdit.value ? `Edit Rule: ${ruleToEdit.value.name}` : 'Add New Rule'));

const openAddDialog = () => {
  ruleToEdit.value = null;
  dialogVisible.value = true;
};

const openEditDialog = (rule) => {
  ruleToEdit.value = { ...rule };
  dialogVisible.value = true;
};

const handleDelete = (rule) => {
  ElMessageBox.confirm(
    `This will permanently delete the rule "${rule.name}". Continue?`,
    'Warning',
    { confirmButtonText: 'OK', cancelButtonText: 'Cancel', type: 'warning' }
  ).then(async () => {
    const success = await ruleStore.deleteRule(rule.id);
    if (success) {
      ElMessage({ type: 'success', message: 'Delete completed' });
    } else {
      ElMessage({ type: 'error', message: ruleStore.error });
    }
  }).catch(() => {
    ElMessage({ type: 'info', message: 'Delete canceled' });
  });
};

// onMounted hook ensures that we fetch necessary server data before fetching rules
onMounted(async () => {
  // Ensure the server list is available for the form's dropdowns
  if (serverStore.servers.length === 0) {
      await serverStore.fetchServers();
  }
  await ruleStore.fetchRules();
});
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hostname-text {
  color: #909399;
  font-size: 12px;
}

.forwarding-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.forwarding-arrow {
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1;
}

.rule-type-text {
  font-size: 10px;
  color: #b1b3b8;
}
</style>