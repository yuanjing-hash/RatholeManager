// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import ServersView from '../views/ServersView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'servers',
      component: ServersView
    },
    // 我们先为规则页面占个位
    {
      path: '/rules',
      name: 'rules',
      // 懒加载组件
      component: () => import('../views/RulesView.vue')
    }
  ]
})

export default router