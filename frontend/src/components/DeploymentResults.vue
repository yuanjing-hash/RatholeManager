<template>
  <div v-if="deploymentStore.results || deploymentStore.error" class="results-overlay">
    <div class="results-panel">
      <h2>Deployment Results</h2>
      <button @click="deploymentStore.clearResults()" class="close-btn">×</button>

      <div v-if="deploymentStore.error" class="error-message">
        {{ deploymentStore.error }}
      </div>

      <ul v-if="deploymentStore.results" class="results-list">
        <li v-for="(result, index) in deploymentStore.results" :key="index">
          <span :class="['status', result.status === 'success' ? 'status-success' : 'status-failed']">
            {{ result.status.toUpperCase() }}
          </span>
          <span class="hostname">{{ result.hostname }}</span>
          <p v-if="result.status === 'failed'" class="error-detail">
            Error: {{ result.error }}
          </p>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { useDeploymentStore } from '@/stores/deployment';
const deploymentStore = useDeploymentStore();
</script>

<style scoped>
.results-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.results-panel {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  width: 80%;
  max-width: 600px;
  position: relative;
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}
.close-btn {
  position: absolute;
  top: 10px;
  right: 15px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
}
.results-list {
  list-style-type: none;
  padding: 0;
  margin-top: 20px;
  max-height: 400px;
  overflow-y: auto;
}
.results-list li {
  padding: 10px;
  border-bottom: 1px solid #eee;
}
.status {
  font-weight: bold;
  padding: 3px 8px;
  border-radius: 4px;
  color: white;
  margin-right: 10px;
}
.status-success { background-color: #28a745; }
.status-failed { background-color: #dc3545; }
.hostname { font-family: monospace; }
.error-detail {
  font-size: 0.9em;
  color: #721c24;
  background-color: #f8d7da;
  padding: 5px;
  border-radius: 4px;
  margin-top: 5px;
  white-space: pre-wrap;
}
.error-message {
  color: #721c24;
  background-color: #f8d7da;
  padding: 10px;
  border-radius: 4px;
}
</style>