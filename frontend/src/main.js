// src/main.js

import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

// --- 新增 Element Plus 的引入 ---
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css' // 引入样式文件

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus) // <-- 在这里应用 Element Plus

app.mount('#app')