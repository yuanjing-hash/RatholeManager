<template>
  <el-form :model="formData" ref="formRef" label-position="top">
    <el-form-item label="Alias" prop="alias" required>
      <el-input v-model="formData.alias" placeholder="e.g., My Cloud Server" />
    </el-form-item>

    <el-form-item label="Hostname / IP Address" prop="hostname" required>
      <el-input v-model="formData.hostname" placeholder="e.g., 123.45.67.89" />
    </el-form-item>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="SSH User" prop="ssh_user" required>
          <el-input v-model="formData.ssh_user" />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="SSH Port" prop="ssh_port" required>
          <el-input-number v-model="formData.ssh_port" :min="1" :max="65535" controls-position="right" style="width: 100%;" />
        </el-form-item>
      </el-col>
    </el-row>

    <el-form-item label="SSH Password" prop="ssh_password">
      <el-input 
        v-model="formData.ssh_password" 
        type="password" 
        show-password 
        :placeholder="isEditMode ? 'Leave blank to keep unchanged' : ''"
        :required="!isEditMode"
      />
    </el-form-item>

    <el-form-item label="Role" prop="role" required>
      <el-select v-model="formData.role" placeholder="Select role" style="width: 100%;">
        <el-option label="Server" value="server" />
        <el-option label="Client" value="client" />
        <el-option label="Both" value="both" />
      </el-select>
    </el-form-item>

    <el-form-item>
      <el-button type="primary" @click="handleSubmit" :loading="serverStore.isLoading">
        {{ isEditMode ? 'Update Server' : 'Add Server' }}
      </el-button>
      <el-button v-if="isEditMode" @click="$emit('cancel')">Cancel</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { useServerStore } from '@/stores/servers';
import { ElMessage } from 'element-plus';

const props = defineProps({ initialData: { type: Object, default: null, }, });
const emit = defineEmits(['submit-success', 'cancel']);
const serverStore = useServerStore();
const formRef = ref(null);
const formData = ref({});
const isEditMode = computed(() => !!props.initialData);
const defaultFormData = { alias: '', hostname: '', ssh_user: 'root', ssh_port: 22, ssh_password: '', role: 'server', };
watch(() => props.initialData, (newData) => {
  if (newData) { formData.value = { ...newData, ssh_password: '' }; } 
  else { formData.value = { ...defaultFormData }; }
}, { immediate: true, deep: true });
const handleSubmit = async () => {
  let success = false;
  if (isEditMode.value) { success = await serverStore.updateServer(props.initialData.id, formData.value); } 
  else { success = await serverStore.addServer(formData.value); }
  if (success) { ElMessage({ type: 'success', message: `Server ${isEditMode.value ? 'updated' : 'added'}!` }); emit('submit-success'); } 
  else { ElMessage({ type: 'error', message: serverStore.error }); }
};
</script>