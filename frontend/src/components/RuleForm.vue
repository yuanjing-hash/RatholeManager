<template>
    <el-form :model="formData" ref="formRef" label-position="top">
        <el-form-item label="Rule Name" prop="name" required>
            <el-input v-model="formData.name" placeholder="e.g., My Web Service" />
        </el-form-item>

        <el-form-item label="Client Server (Source)" prop="client_id" required>
            <el-select v-model.number="formData.client_id" filterable style="width: 100%;">
                <el-option v-for="client in clientServers" :key="client.id" :value="client.id"
                    :label="`${client.alias} (${client.hostname})`" />
            </el-select>
        </el-form-item>

        <el-form-item label="Protocol" prop="rule_type" required>
            <el-radio-group v-model="formData.rule_type">
                <el-radio-button label="tcp" />
                <el-radio-button label="udp" />
            </el-radio-group>
        </el-form-item>

        <el-form-item label="Local Port (on Client)" prop="local_port" required>
            <el-input-number v-model.number="formData.local_port" :min="1" :max="65535" controls-position="right"
                style="width: 100%;" />
        </el-form-item>

        <el-form-item label="Target Server (Destination)" prop="server_id" required>
            <el-select v-model.number="formData.server_id" filterable style="width: 100%;">
                <el-option v-for="server in targetServers" :key="server.id" :value="server.id"
                    :label="`${server.alias} (${server.hostname})`" />
            </el-select>
        </el-form-item>

        <el-form-item label="Remote Port (on Target)" prop="remote_port" required>
            <el-input-number v-model.number="formData.remote_port" :min="1" :max="65535" controls-position="right"
                style="width: 100%;" />
        </el-form-item>

        <el-form-item>
            <el-button type="primary" @click="handleSubmit" :loading="ruleStore.isLoading">
                {{ isEditMode ? 'Update Rule' : 'Add Rule' }}
            </el-button>
            <el-button v-if="isEditMode" @click="$emit('cancel')">Cancel</el-button>
        </el-form-item>
    </el-form>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRuleStore } from '@/stores/rules';
import { useServerStore } from '@/stores/servers';
import { ElMessage } from 'element-plus';

const props = defineProps({ initialData: { type: Object, default: null } });
const emit = defineEmits(['submit-success', 'cancel']);

const ruleStore = useRuleStore();
const serverStore = useServerStore();

const formData = ref({});
const isEditMode = computed(() => !!props.initialData);

const defaultFormData = { name: '', client_id: '', local_port: 8080, server_id: '', remote_port: 80 };

watch(() => props.initialData, (newData) => {
    if (newData) { formData.value = { ...newData }; }
    else { formData.value = { ...defaultFormData }; }
}, { immediate: true, deep: true });

const clientServers = computed(() => serverStore.servers.filter(s => ['client', 'both'].includes(s.role)));
const targetServers = computed(() => serverStore.servers.filter(s => ['server', 'both'].includes(s.role)));

const handleSubmit = async () => {
    let success = false;
    if (isEditMode.value) { success = await ruleStore.updateRule(props.initialData.id, formData.value); }
    else { success = await ruleStore.addRule(formData.value); }

    if (success) { ElMessage({ type: 'success', message: `Rule ${isEditMode.value ? 'updated' : 'added'}!` }); emit('submit-success'); }
    else { ElMessage({ type: 'error', message: ruleStore.error }); }
};
</script>