<template>
  <div class="common-layout">
    <el-container>
      <el-aside width="200px">
        <div class="logo">Rathole Manager</div>
        <el-menu
          :default-active="activeMenu"
          class="el-menu-vertical"
          router
        >
          <el-menu-item index="/">
            <el-icon><Service /></el-icon>
            <span>Servers</span>
          </el-menu-item>
          <el-menu-item index="/rules">
            <el-icon><Switch /></el-icon>
            <span>Rules</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <el-container>
        <el-header>
          <div class="header-title">
            Dashboard
          </div>
          <div class="actions">
            <el-button type="primary" @click="handleDeploy" :loading="deploymentStore.isDeploying" class="deploy-btn">
              <el-icon><Promotion /></el-icon>
              <span style="margin-left: 5px;">{{ deploymentStore.isDeploying ? 'Deploying...' : 'Deploy All Changes' }}</span>
            </el-button>
          </div>
        </el-header>
        
        <el-main>
          <RouterView />
        </el-main>
      </el-container>
    </el-container>

    <DeploymentResults />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { RouterView, useRoute } from 'vue-router';
import { useDeploymentStore } from './stores/deployment';
import DeploymentResults from './components/DeploymentResults.vue';
// 引入所有需要的图标
import { Service, Switch, Promotion } from '@element-plus/icons-vue';

const deploymentStore = useDeploymentStore();
const route = useRoute();

// 计算属性，让菜单高亮与当前路由同步
const activeMenu = computed(() => route.path);

const handleDeploy = () => {
  if (window.confirm("Are you sure you want to deploy all current configurations to all servers?")) {
    deploymentStore.triggerDeployment();
  }
};
</script>

<style>
/* 全局样式调整 */
html, body, #app, .common-layout, .el-container {
  height: 100%;
  margin: 0;
  padding: 0;
}

.el-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #ffffff;
  border-bottom: 1px solid #e4e7ed;
}

.el-aside {
  background-color: #ffffff;
  border-right: 1px solid #e4e7ed;
}

.el-aside .logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  font-weight: bold;
  font-size: 18px;
  background-color: #f8f9fa;
}

.el-menu-vertical {
  border-right: none;
}

.el-main {
  background-color: #f4f5f7;
}
</style>打